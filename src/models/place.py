class Place:
    def __init__(
        self,
        category_id: int,
        category_name: str,
        name: str,
        latitude: float,
        longitude: float,
    ):
        self.category_id = category_id
        self.category_name = category_name
        self.name = name
        self.latitude = latitude
        self.longitude = longitude

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"(Category ID: {self.category_id}; Category Name: {self.category_name}; Name: {self.name}; Latitude: {self.latitude}; Longitude: {self.longitude}"

    def __eq__(self, other_place):
        return (
            self.category_id == other_place.category_id
            and self.category_name == other_place.category_name
            and self.name == other_place.name
            and self.latitude == other_place.latitude
            and self.longitude == other_place.longitude
        )


class Workplace(Place):
    def __init__(
        self,
        category_id: int,
        category_name: str,
        name: str,
        latitude: float,
        longitude: float,
        work_info: dict,
    ):
        super().__init__(
            category_id,
            category_name,
            name,
            latitude,
            longitude,
        )
        self.max_workers = work_info["MaxWorkers"]
        self.start_time_from = work_info["StartTimeFrom"]
        self.start_time_to = work_info["StartTimeTo"]
        self.current_people = 0

    def __str__(self):
        return f"{super().__str__()}; Max workers: {self.max_workers}; Start_time between: {self.start_time_from}-{self.start_time_to}; Current people: {self.current_people}"


class FreeTimePlace(Place):
    def __init__(
        self,
        category_id: int,
        category_name: str,
        name: str,
        latitude: float,
        longitude: float,
        free_time_activity_info: dict,
    ):
        super().__init__(
            category_id,
            category_name,
            name,
            latitude,
            longitude,
        )
        self.typical_stay_duration_hours = free_time_activity_info["TypicalStayDurationHours"]

    def __str__(self):
        return f"{super().__str__()}; Typical stay duration: {self.typical_stay_duration_hours}h)"
