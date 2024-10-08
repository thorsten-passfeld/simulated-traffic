import random
import openrouteservice

from tqdm import tqdm
from datetime import datetime, timedelta
from multiprocessing import Process, Queue, Pipe

from ..models import Person, Position, DailyRoute
from ..lib.random_time import get_random_time_in_timeframe


def calculate_directions(
    ors_client: openrouteservice.Client, coords, use_cycling_profile=True
) -> dict:
    if use_cycling_profile:
        profile_to_use = "cycling-regular"
    else:
        profile_to_use = "driving-car"

    return ors_client.directions(
        coords,
        profile=profile_to_use,
        preference="fastest",
        units="m",
    )


def generate_daily_routes_sequentially(
    start_date: datetime.date,
    num_days_to_simulate: int,
    generated_people: list,
    ors_client: openrouteservice.Client,
):
    for person in tqdm(generated_people):
        current_date = start_date
        for day in range(num_days_to_simulate):
            daily_route_for_person = generate_daily_route_for_person(
                person, current_date, ors_client
            )
            person.add_route(daily_route_for_person)
            # print("Daily route for person:")
            # print(daily_route_for_person)
            current_date += timedelta(days=1)


def generate_daily_route_for_person(
    person: Person, current_date, ors_client: openrouteservice.Client
) -> DailyRoute:
    # print(f"Generating traffic data for '{current_date}'...")
    daily_route_for_person = DailyRoute()

    # Handle weekdays and weekends differently to make it more realistic
    is_weekend = current_date.weekday() >= 5

    # Calculate a route from their home to their workplace, then to a route to a random free time place and back home
    # This is done in one step and the data is then separated for the sake of this simulation
    home_location = person.home_location
    workplace = person.workplace
    random_free_time_place = random.choice(person.favorite_free_time_places)

    stay_duration_free_time_hours = (
        random_free_time_place.typical_stay_duration_hours + random.uniform(0.0, 1.0)
    )

    if is_weekend:
        # TODO: Multiple free time activities?
        coords = [
            (home_location.lon, home_location.lat),
            (random_free_time_place.longitude, random_free_time_place.latitude),
            (home_location.lon, home_location.lat),
        ]
        stay_durations = [stay_duration_free_time_hours]

        # Randomly choose a time to start their day on the weekend
        start_of_day_time = get_random_time_in_timeframe(8, 18)
    else:
        coords = [
            (home_location.lon, home_location.lat),
            (workplace.longitude, workplace.latitude),
            (random_free_time_place.longitude, random_free_time_place.latitude),
            (home_location.lon, home_location.lat),
        ]
        # Let the stay durations vary a bit from day to day
        stay_duration_work_hours = 8.0 + random.uniform(-1.0, 1.0)

        # NOTE: The index of a stay duration has to match the index of that location inside "coords"
        # starting with index 1 until the second last index -> So index 0 -> e.g. the workplace (on a weekday)
        # But obviously the first and last location are excluded - e.g. the day is over anyways at the last location
        stay_durations = [stay_duration_work_hours, stay_duration_free_time_hours]

        # A small time delta to the start of day time to mimic slight variations in a set schedule
        # Randomly choose a time to start their day based on their workplace
        start_of_day_time = get_random_time_in_timeframe(
            workplace.start_time_from, workplace.start_time_to
        )

    current_time_for_person = datetime.strptime(
        f"{current_date} {start_of_day_time}", r"%Y-%m-%d %H:%M"
    )

    # The home location is the first waypoint
    current_position = Position(home_location.lat, home_location.lon, current_time_for_person)
    daily_route_for_person.add_waypoint(current_position)

    calculated_route_info = calculate_directions(ors_client, coords, use_cycling_profile=False)
    route = calculated_route_info["routes"][0]
    decoded_geometry_waypoints = openrouteservice.convert.decode_polyline(route["geometry"])[
        "coordinates"
    ]

    previous_waypoint_index = 0

    num_routes = len(coords) - 1
    for route_index in range(num_routes):
        route_steps = route["segments"][route_index][
            "steps"
        ]  # e.g. all steps from home -> workplace
        # print(f"Segment {route_index}:")
        for step_i, step in enumerate(route_steps):
            # print(f"Step {step_i}:")
            # e.g. waypoints from index 0 to 14 in the full LineString
            step_waypoints_from_idx = step["way_points"][0]
            step_waypoints_to_idx = step["way_points"][1]

            # If both indexes are the same, we are at a destination and the distance is obviously 0. We can skip this one
            if step_waypoints_from_idx == step_waypoints_to_idx:
                continue

            # The last waypoint index counts as well. The slice has to be inclusive
            for current_waypoint_index in range(step_waypoints_from_idx, step_waypoints_to_idx + 1):
                if current_waypoint_index == previous_waypoint_index:
                    continue

                # print(
                #    f"From index {previous_waypoint_index} to {current_waypoint_index}..."
                # )

                current_waypoint = decoded_geometry_waypoints[current_waypoint_index]
                previous_waypoint = decoded_geometry_waypoints[previous_waypoint_index]

                # Calculate the distance between each waypoint
                coords = [
                    (previous_waypoint[0], previous_waypoint[1]),
                    (current_waypoint[0], current_waypoint[1]),
                ]

                calculated_sub_route_info = calculate_directions(
                    ors_client, coords, use_cycling_profile=False
                )

                sub_route = calculated_sub_route_info["routes"][0]
                sub_decoded_geometry_waypoints = openrouteservice.convert.decode_polyline(
                    sub_route["geometry"]
                )["coordinates"]
                sub_route_steps = sub_route["segments"][0]["steps"]

                sub_route_summary = sub_route.get("summary")
                # e.g. Two neighboring waypoint indexes point to the exact same coordinates -> Route with no distance
                if not sub_route_summary:
                    # with open("troubleshooting_sub_route.json", "w") as f:
                    #    json.dump(calculated_sub_route_info, f)
                    # with open("troubleshooting_route.json", "w") as f:
                    #    json.dump(calculated_route_info, f)
                    # with open("troubleshooting_route_waypoints.json", "w") as f:
                    #    json.dump(decoded_geometry_waypoints, f)
                    # print(f"From: {step_waypoints_from_idx}")
                    # print(f"To: {step_waypoints_to_idx}")
                    # print(f"Current: {current_waypoint_index}")
                    # print(f"Previous: {previous_waypoint_index}")
                    # print("Saved logs and skipped this one.")
                    # Skip this pair and keep the previous waypoint index as the last "valid" one before the duplicates began
                    continue

                sub_route_total_duration_seconds = sub_route_summary["duration"]

                for sub_route_step_info in sub_route_steps:
                    waypoint_idx_to_use = sub_route_step_info["way_points"][1]
                    waypoint_pos = Position(
                        sub_decoded_geometry_waypoints[waypoint_idx_to_use][1],
                        sub_decoded_geometry_waypoints[waypoint_idx_to_use][0],
                    )
                    if not daily_route_for_person.is_roughly_equal_to_last_waypoint(waypoint_pos):
                        # print(f"Waypoint index {waypoint_idx_to_use}: {waypoint_pos}")

                        # NOTE: This is the passed time since the last time step
                        sub_route_step_duration_seconds = sub_route_step_info["duration"]
                        current_time_for_person += timedelta(
                            seconds=sub_route_step_duration_seconds
                        )
                        waypoint_pos.timestamp = current_time_for_person.timestamp()
                        # print(
                        #    f"Sub route step duration: {sub_route_step_duration_seconds} seconds"
                        # )

                        daily_route_for_person.add_waypoint(waypoint_pos)
                # Preparation for the next iteration
                previous_waypoint_index = current_waypoint_index
        # NOTE: The last route back home needs no stay duration - It's the end of the day
        if route_index < num_routes - 1:
            current_time_for_person += timedelta(hours=stay_durations[route_index])
    return daily_route_for_person


def generate_all_daily_routes_for_person_parallel(
    pid: int,
    start_date: datetime.date,
    num_days_to_simulate: int,
    ors_client: openrouteservice.Client,
    job_queue: Queue,
    connection_send,
):
    generated_subset_of_people = list()
    while True:
        person = job_queue.get()
        if not person:
            # Signal the other processes to exit
            job_queue.put(None)
            break
        # print(f"Process {pid}: Got a new person from the job queue")
        current_date = start_date
        for _ in range(num_days_to_simulate):
            # print(
            #    f"Process {pid}: Generating a daily route for the person - Current date: {current_date}"
            # )
            daily_route_for_person = generate_daily_route_for_person(
                person, current_date, ors_client
            )
            # print(f"Process {pid}: Generated daily route for the person -> {person}")
            person.add_route(daily_route_for_person)

            current_date += timedelta(days=1)

        generated_subset_of_people.append(person)

    # After this worker process got a signal to exit, it will hand off the data
    for person in generated_subset_of_people:
        connection_send.send(person)
    # All done!
    connection_send.send(None)


def generate_daily_routes_parallel(
    start_date: datetime.date,
    num_days_to_simulate: int,
    generated_people_without_daily_routes: list,
    ors_client: openrouteservice.Client,
):
    # TODO: Determine appropriately
    num_processes = 8
    # Leave some headroom for when workers are faster than the main process (scheduling order)
    job_queue = Queue(maxsize=int(1.5 * num_processes))

    # Processes are used to get around the GIL limitation that applies to threads in Python
    worker_processes = list()
    receiving_pipe_connections = list()
    for pid in range(num_processes):
        connection_recv, connection_send = Pipe()
        receiving_pipe_connections.append(connection_recv)
        process = Process(
            target=generate_all_daily_routes_for_person_parallel,
            args=(
                pid,
                start_date,
                num_days_to_simulate,
                ors_client,
                job_queue,
                connection_send,
            ),
        )
        worker_processes.append(process)
        process.start()

    for person in tqdm(generated_people_without_daily_routes):
        job_queue.put(person)

    # Signal the end, let it cascade
    job_queue.put(None)

    generated_people = list()
    for i, (process, connection_recv) in enumerate(
        zip(worker_processes, receiving_pipe_connections)
    ):
        # print(f"Getting results from process {i}...")
        # Extract and merge all generated data about peoples' daily routes into one list
        while True:
            generated_person = connection_recv.recv()
            if not generated_person:
                # print(f"Process {i} is all done sending its data!")
                break
            generated_people.append(generated_person)
        # print(f"Joining process {i}...")
        process.join()

    print(f"Successfully generated daily routes for all people.")
    return generated_people
