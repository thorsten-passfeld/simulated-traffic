# NOTE: Every waypoint is seen as a sampled GPS location
from math import isclose

from .position import Position


class DailyRoute:
    def __init__(self):
        self._route_waypoints = list()

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        string_representation = ""
        for i, position in enumerate(self._route_waypoints):
            string_representation += f"{i+1}.\t{position}\n"
        return string_representation

    def add_waypoint(self, position: Position):
        self._route_waypoints.append(position)

    def is_roughly_equal_to_last_waypoint(self, pos: Position):
        last_waypoint = self._route_waypoints[-1]
        return isclose(pos.lat, last_waypoint.lat) and isclose(pos.lon, last_waypoint.lon)

    def get_waypoints(self) -> list:
        return self._route_waypoints

    def get_waypoints_as_lat_lon(self) -> list:
        return [pos.to_lat_lon() for pos in self._route_waypoints]

    def get_waypoints_as_lon_lat(self) -> list:
        return [pos.to_lon_lat() for pos in self._route_waypoints]

    def to_dict(self) -> dict:
        output = dict()
        output["coords"] = list()
        output["times"] = list()
        for position in self._route_waypoints:
            output["coords"].append([position.lat, position.lon])
            output["times"].append(position.timestamp)
        return output

    # For later visualization
    def to_linestring(self) -> dict:
        linestring_info = dict()
        linestring_info["type"] = "LineString"
        linestring_info["coordinates"] = list()
        for position in self._route_waypoints:
            linestring_info["coordinates"].append([position.lat, position.lon])
        return linestring_info
