import requests
import json
import math

from geojson import Point
from turfpy.measurement import destination

from ..models import Workplace, FreeTimePlace

LOCAL_API_SERVER = "http://localhost:5000/pois"


def get_all_pois(central_location_point: Point, places_info: dict, square_length_km: float) -> dict:
    distance_km = square_length_km * math.sqrt(2)  # length * sqrt(2)
    bearing_top_right = 45
    bearing_bottom_left = -135
    # For the full polygon, we need the other two corners as well
    bearing_top_left = 135
    bearing_bottom_right = -45
    options = {"units": "km"}
    dest_top_right = destination(central_location_point, distance_km, bearing_top_right, options)
    dest_bottom_left = destination(
        central_location_point, distance_km, bearing_bottom_left, options
    )

    dest_top_left = destination(central_location_point, distance_km, bearing_top_left, options)
    dest_bottom_right = destination(
        central_location_point, distance_km, bearing_bottom_right, options
    )

    # Collect all information for the places we're interested in
    category_group_ids_of_interest = [
        int(category_id)
        for category_id, place_info in places_info.items()
        if place_info["IsGroupID"]
    ]
    category_ids_of_interest = [
        int(category_id)
        for category_id, place_info in places_info.items()
        if not place_info["IsGroupID"]
    ]

    # buffer_meters = 2000
    buffer_meters = 0
    poi_req_info_json = {
        "request": "pois",
        "geometry": {
            "geojson": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            dest_bottom_left["geometry"]["coordinates"][0],
                            dest_bottom_left["geometry"]["coordinates"][1],
                        ],
                        [
                            dest_bottom_right["geometry"]["coordinates"][0],
                            dest_bottom_right["geometry"]["coordinates"][1],
                        ],
                        [
                            dest_top_right["geometry"]["coordinates"][0],
                            dest_top_right["geometry"]["coordinates"][1],
                        ],
                        [
                            dest_top_left["geometry"]["coordinates"][0],
                            dest_top_left["geometry"]["coordinates"][1],
                        ],
                        [
                            dest_bottom_left["geometry"]["coordinates"][0],
                            dest_bottom_left["geometry"]["coordinates"][1],
                        ],
                    ]
                ],
            },
            "buffer": buffer_meters,
        },
        "filters": {
            "category_group_ids": category_group_ids_of_interest,
            "category_ids": category_ids_of_interest,
        },
    }
    print(poi_req_info_json)

    r = requests.post(LOCAL_API_SERVER, json=poi_req_info_json)

    return r.json()


def parse_pois(poi_info: dict, places_info: dict) -> (list, list):
    known_group_category_ids = list()
    for category_id, place_info in places_info.items():
        if place_info["IsGroupID"]:
            known_group_category_ids.append(category_id)
    known_group_category_ids = sorted(known_group_category_ids)

    workplaces = list()
    free_time_places = list()

    for poi in poi_info["features"]:
        category_id = list(poi["properties"]["category_ids"].keys())[0]
        category_name = poi["properties"]["category_ids"][category_id]["category_name"]
        osm_tags = poi["properties"].get("osm_tags")
        if not osm_tags or "name" not in osm_tags:
            name = ""
        else:
            name = osm_tags["name"]
        latitude = poi["geometry"]["coordinates"][1]
        longitude = poi["geometry"]["coordinates"][0]

        # Associate information about this category with this point of interest by the ID
        related_place_info = places_info.get(category_id)
        if not related_place_info:
            # Look in the nearest group category
            best_id_match = -1
            for group_category_id in known_group_category_ids:
                if int(category_id) > int(group_category_id):
                    best_id_match = group_category_id
            related_place_info = places_info[best_id_match]

        work_info = related_place_info["WorkInfo"]
        free_time_activity_info = related_place_info["FreeTimeActivityInfo"]

        if work_info:
            workplace = Workplace(
                int(category_id),
                category_name,
                name,
                latitude,
                longitude,
                work_info,
            )
            workplaces.append(workplace)

        if free_time_activity_info:
            free_time_place = FreeTimePlace(
                int(category_id),
                category_name,
                name,
                latitude,
                longitude,
                free_time_activity_info,
            )
            free_time_places.append(free_time_place)

    return workplaces, free_time_places
