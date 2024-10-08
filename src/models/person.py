from .place import Workplace
from .position import Position
from .route import DailyRoute


class Person:
    def __init__(
        self,
        p_id: int,
        home_location: Position,
        workplace: Workplace,
        favorite_free_time_places: list,
    ):
        self.id = p_id
        self.home_location = home_location
        self.workplace = workplace
        self.favorite_free_time_places = favorite_free_time_places

        self._past_routes = list()

    def add_route(self, route: DailyRoute):
        self._past_routes.append(route)

    def get_all_routes(self) -> list:
        return self._past_routes

    def get_all_routes_as_dicts(self) -> list:
        all_daily_routes = list()
        for daily_route in self._past_routes:
            daily_route_info = daily_route.to_dict()
            daily_route_info["person"] = self.id
            all_daily_routes.append(daily_route_info)
        return all_daily_routes
