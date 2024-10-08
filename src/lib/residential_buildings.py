import json

import overpass

from pathlib import Path

from ..models import Position


def get_all_residential_buildings(
    central_location_latitude: float, central_location_longitude: float, overpass_api: overpass.API
) -> list:
    radius = 5000  # TODO: Set depending on square size

    Path("cache/").mkdir(exist_ok=True)

    cached_buildings_info = dict()
    with open("cache/overpass_cache.json", "r") as cache_file:
        cached_buildings_info = json.load(cache_file)

    query = f'way(around:{radius},{central_location_latitude},{central_location_longitude})["building"="residential"];(._;<;);'

    # Check if there already is an entry in the cache
    if not query in cached_buildings_info:
        result = overpass_api.Get(query, responseformat="geojson", verbosity="geom")
        # Cache residential info returned from the API
        buildings = list()
        for building_info in result["features"]:
            building_longitude = building_info["geometry"]["coordinates"][0][0]
            building_latitude = building_info["geometry"]["coordinates"][0][1]
            buildings.append([building_latitude, building_longitude])

        cached_buildings_info[query] = buildings
        print(buildings)

        with open("cache/overpass_cache.json", "w") as cache_file:
            json.dump(cached_buildings_info, cache_file)
    else:
        # print("Already in cache!")
        pass

    building_positions = list()
    for building in cached_buildings_info[query]:
        building_positions.append(Position(building[0], building[1]))

    return building_positions
