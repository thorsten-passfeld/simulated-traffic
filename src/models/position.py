from datetime import datetime


class Position:
    def __init__(self, latitude: float, longitude: float, time_point: datetime = None):
        self.lat = latitude
        self.lon = longitude
        if time_point:
            self.timestamp = time_point.timestamp()
        else:
            self.timestamp = None

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        string_representation = f"(Latitude: {self.lat}, Longitude: {self.lon})"
        if self.timestamp:
            string_representation += f"\t-\t{self.timestamp}"
        return string_representation

    def to_lat_lon(self):
        return (self.lat, self.lon)

    def to_lon_lat(self):
        return (self.lon, self.lat)
