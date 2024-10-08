#!/usr/bin/env python

import json
import random
import overpass
import openrouteservice

from tqdm import tqdm
from datetime import date, timedelta, datetime
from geojson import Point
from defaultlist import defaultlist
from requests.exceptions import ConnectionError

from .models import Person, Position, DailyRoute
from .lib.points_of_interest import get_all_pois, parse_pois
from .lib.residential_buildings import get_all_residential_buildings
from .lib.places import get_all_places
from .lib.generating_routes import (
    generate_daily_routes_sequentially,
    generate_daily_routes_parallel,
)

# Route from A to B:
# http://localhost:8080/ors/v2/directions/driving-car?start=8.676581,49.418204&end=8.692803,49.409465

# Points of Interest in radius around a point
# http://localhost:5000/pois

# Query for finding the center of e.g. a city
# https://nominatim.openstreetmap.org/search?q=Osnabrueck (Url encode! / Use the requests module)
# curl -A 'Custom Curl' 'https://nominatim.openstreetmap.org/search?q=Osnabrueck&format=json'

SQUARE_LENGTH_km = 0.4

NUM_DAYS_TO_SIMULATE = 2

PEOPLE_PER_RESIDENTIAL_BUILDING = 1
NUM_FREE_TIME_PLACES_PER_PERSON = 2


def main():
    ors_client = openrouteservice.Client(base_url="http://localhost:8080/ors")
    overpass_api = overpass.API()

    # Use the city's geo location and a fixed size square (or something else) to get all points of interest
    # NOTE: Maximum size: 5km^2
    central_location_latitude = 52.2719595
    central_location_longitude = 8.047635
    central_location_point = Point((central_location_longitude, central_location_latitude))

    # e.g. 2023-03-29
    start_date = date.today()

    # Create a list with all workplaces and one with all free time places in the surrounding area
    # Combine it with information and parameters we set up in a file to specify e.g. the max. number of workers
    places_info = get_all_places("data/places_info.json")
    location_poi_info = get_all_pois(central_location_point, places_info, SQUARE_LENGTH_km)
    workplaces, free_time_places = parse_pois(location_poi_info, places_info)

    location_residential_buildings = get_all_residential_buildings(
        central_location_latitude, central_location_longitude, overpass_api
    )

    # Use the place objects to generate people
    generated_people = generate_people(location_residential_buildings, workplaces, free_time_places)

    # Use the generated people to come up with their daily routes for the given time span of X days

    # Generate routes for all days for each person
    # generate_daily_routes_sequentially(
    #    start_date, NUM_DAYS_TO_SIMULATE, generated_people, ors_client
    # )
    generated_people = generate_daily_routes_parallel(
        start_date, NUM_DAYS_TO_SIMULATE, generated_people, ors_client
    )

    # Iterate over generated people, which store a list of their daily routes
    output_dataset = dict()
    output_dataset["people"] = list()
    # Note: A defaultlist helps make the code much cleaner by allowing to iterate over people
    # and inserting all of their daily routes for every day in that iteration instead of iterating over days
    output_dataset["daily_routes"] = defaultlist(list)
    for person in generated_people:
        person_info = dict()
        person_info["id"] = person.id
        person_info["home_location"] = [person.home_location.lat, person.home_location.lon]
        person_info["workplace"] = [person.workplace.latitude, person.workplace.longitude]
        person_info["free_time_places"] = [
            [place.latitude, place.longitude] for place in person.favorite_free_time_places
        ]
        output_dataset["people"].append(person_info)

        all_daily_routes_for_person = person.get_all_routes_as_dicts()
        for day_index, daily_route_info in enumerate(all_daily_routes_for_person):
            output_dataset["daily_routes"][day_index].append(daily_route_info)

    # Save the end result for later use to visualize everything
    with open("output/generated_routes.json", "w") as out_file:
        json.dump(output_dataset, out_file)
    print("Saved all generated routes.")


def generate_people(
    location_residential_buildings: list, workplaces: list, free_time_places: list
) -> list:
    generated_people = list()
    person_id = 0
    random.shuffle(location_residential_buildings)
    # Assign everyone one of the residential buildings, up to the maximum of 8 people per building
    for home_location in tqdm(location_residential_buildings):
        if person_id == 10:
            break
        for i in range(PEOPLE_PER_RESIDENTIAL_BUILDING):
            # Randomly shuffle all workplaces and free time places so that there's no correlation between homes and workplaces and such
            random.shuffle(workplaces)
            random.shuffle(free_time_places)
            # Choose one of the workplaces
            chosen_workplace = None
            for workplace in workplaces:
                if workplace.current_people < workplace.max_workers:
                    # This workplace still has capacity
                    chosen_workplace = workplace
                    workplace.current_people += 1
                    break
            if not chosen_workplace:
                # print("All workplaces were full! Choosing a random 'full' workplace anyways...")
                # chosen_workplace = workplaces[0]
                print("All workplaces are full. No need to generate more people!")
                return generated_people

            # Now choose one of the free time places that is not this workplace
            chosen_free_time_places = list()
            for free_time_place in free_time_places:
                if not free_time_place == chosen_workplace:
                    if len(chosen_free_time_places) < NUM_FREE_TIME_PLACES_PER_PERSON:
                        chosen_free_time_places.append(free_time_place)
                    else:
                        break

            # The person can be created now
            person = Person(
                person_id,
                home_location,
                chosen_workplace,
                chosen_free_time_places,
            )
            generated_people.append(person)
            person_id += 1
    return generated_people


if __name__ == "__main__":
    main()
