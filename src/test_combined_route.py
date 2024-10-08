import openrouteservice

from openrouteservice import convert

import json

from .models import DailyRoute, Position

import folium


def main():
    # partial_route_test()
    # normal_route()
    sub_routes()


def partial_route_test():
    ors_client = openrouteservice.Client(base_url="http://localhost:8080/ors")
    home_location_coords = [8.031346, 52.280421]
    workplace_coords = [8.051503, 52.272901]
    coords = [home_location_coords, workplace_coords]
    print(coords)

    calculated_route_info = ors_client.directions(
        coords, profile="driving-car", preference="fastest", units="m"
    )
    with open("openrouteservice_example_route_partial.json", "w") as f:
        json.dump(calculated_route_info, f)


def normal_route():
    ors_client = openrouteservice.Client(base_url="http://localhost:8080/ors")
    route_info = None
    with open("openrouteservice_example_route_partial.json", "r") as route_file:
        route_info = json.load(route_file)

    route = route_info["routes"][0]
    decoded_geometry_waypoints = convert.decode_polyline(route["geometry"])["coordinates"]

    home_location_coords = [8.031346, 52.280421]

    daily_route = DailyRoute()
    daily_route.add_waypoint(Position(home_location_coords[0], home_location_coords[1]))

    # num_routes = 3
    num_routes = 1
    for route_index in range(num_routes):
        route_steps = route["segments"][route_index][
            "steps"
        ]  # e.g. all steps from home -> workplace
        print(f"Segment {route_index}:")
        for step_i, step in enumerate(route_steps):
            print(f"Step {step_i}:")
            # e.g. waypoints from index 0 to 14 in the full LineString
            step_waypoints_from_idx = step["way_points"][0]
            step_waypoints_to_idx = step["way_points"][1]

            # If both indexes are the same, we are at a destination and the distance is obviously 0. We can skip this one
            if step_waypoints_from_idx == step_waypoints_to_idx:
                continue

            step_waypoint_to = decoded_geometry_waypoints[step_waypoints_to_idx]

            waypoint_pos = Position(
                step_waypoint_to[0],
                step_waypoint_to[1],
            )
            daily_route.add_waypoint(waypoint_pos)

    my_map = folium.Map(location=[home_location_coords[1], home_location_coords[0]], zoom_start=14)

    counter = 1
    for waypoint_position in daily_route.get_waypoints():
        folium.Marker(waypoint_position.to_lon_lat(), tooltip=str(counter)).add_to(my_map)
        counter += 1

    folium.PolyLine(
        daily_route.get_waypoints_as_lon_lat(), color="red", weight=2.5, opacity=1
    ).add_to(my_map)

    my_map.save("folium_map.html")


def sub_routes():
    ors_client = openrouteservice.Client(base_url="http://localhost:8080/ors")
    route_info = None
    with open("openrouteservice_example_route_partial.json", "r") as route_file:
        route_info = json.load(route_file)

    route = route_info["routes"][0]
    decoded_geometry_waypoints = convert.decode_polyline(route["geometry"])["coordinates"]

    home_location_coords = [8.031346, 52.280421]

    previous_waypoint_index = -1

    daily_route = DailyRoute()
    daily_route.add_waypoint(Position(home_location_coords[0], home_location_coords[1]))

    num_routes = 1
    # num_routes = 3
    for route_index in range(num_routes):
        route_steps = route["segments"][route_index][
            "steps"
        ]  # e.g. all steps from home -> workplace
        print(f"Segment {route_index}:")
        for step_i, step in enumerate(route_steps):
            print(f"Step {step_i}:")
            # e.g. waypoints from index 0 to 14 in the full LineString
            step_waypoints_from_idx = step["way_points"][0]
            step_waypoints_to_idx = step["way_points"][1]

            # If both indexes are the same, we are at a destination and the distance is obviously 0. We can skip this one
            if step_waypoints_from_idx == step_waypoints_to_idx:
                continue
            # The last waypoint index counts as well. Slice would otherwise not be inclusive
            for current_waypoint_index in range(step_waypoints_from_idx, step_waypoints_to_idx + 1):
                if current_waypoint_index == previous_waypoint_index:
                    continue

                print(f"From index {previous_waypoint_index} to {current_waypoint_index}...")

                current_waypoint = decoded_geometry_waypoints[current_waypoint_index]

                if previous_waypoint_index == -1:
                    previous_waypoint = home_location_coords
                else:
                    previous_waypoint = decoded_geometry_waypoints[previous_waypoint_index]

                # Calculate the distance between each waypoint
                coords = [
                    (previous_waypoint[0], previous_waypoint[1]),
                    (current_waypoint[0], current_waypoint[1]),
                ]

                calculated_route_info = ors_client.directions(
                    coords,
                    profile="driving-car",
                    preference="recommended",
                    units="m",
                )

                sub_route = calculated_route_info["routes"][0]
                sub_decoded_geometry_waypoints = convert.decode_polyline(sub_route["geometry"])[
                    "coordinates"
                ]
                steps = sub_route["segments"][0]["steps"]
                # prev_waypoint_idx_to_use = -1
                for step_info in steps:
                    waypoint_idx_to_use = step_info["way_points"][1]
                    waypoint_pos = Position(
                        sub_decoded_geometry_waypoints[waypoint_idx_to_use][0],
                        sub_decoded_geometry_waypoints[waypoint_idx_to_use][1],
                    )
                    if not daily_route.is_roughly_equal_to_last_waypoint(waypoint_pos):
                        # print(
                        #    f"Waypoints:\n{waypoint_pos} and {daily_route.get_last_waypoint()}. Equal? -> {waypoint_pos == daily_route.get_last_waypoint()}"
                        # )
                        print(f"Waypoint index {waypoint_idx_to_use}: {waypoint_pos}")
                        daily_route.add_waypoint(waypoint_pos)
                    else:
                        print(
                            f"Waypoint index {waypoint_idx_to_use}: {waypoint_pos} - Already got that one!"
                        )
                    # prev_waypoint_idx_to_use = waypoint_idx_to_use

                # Preparation for the next iteration
                previous_waypoint_index = current_waypoint_index

    my_map = folium.Map(location=[home_location_coords[1], home_location_coords[0]], zoom_start=14)

    counter = 1
    for waypoint_position in daily_route.get_waypoints():
        print(waypoint_position)
        folium.Marker(waypoint_position.to_lon_lat(), tooltip=str(counter)).add_to(my_map)
        counter += 1

    folium.PolyLine(
        daily_route.get_waypoints_as_lon_lat(), color="red", weight=2.5, opacity=1
    ).add_to(my_map)

    my_map.save("folium_detailed_map.html")
    # print(daily_route.to_linestring())
