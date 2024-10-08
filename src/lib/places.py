import json


def get_all_places(file_path: str) -> dict:
    places_info = dict()
    with open(file_path, "r") as places_file:
        places_info = json.load(places_file)
    return places_info
