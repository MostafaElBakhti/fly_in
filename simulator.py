from map import Map
from classes import Drone, Zone


class Simulator:

    def __init__(self, map_data: Map , paths) -> None :
        self.map_data = map_data
        self.paths = paths
        self.drones = [
            Drone(i + 1 , map_data.start_hub , map_data.end_hub )
            for i in range(map_data.nb_drones)
        ]
        self.history = []

    def assign_paths(self) -> None :
        if not self.paths:
            raise ValueError("No valid paths found for assignment.")
        path_counts = [0] * len(self.paths)
        for drone in self.drones:
            best_idx = 0
            min_eta = float("inf")

            for idx, path in enumerate(self.paths):
                cost = self.map_data.path_cost(path)


    def _select_paths(self) : 
        if len(self.paths) <= 1:
            return 
        
        best_paths = None
        best_turns = float("inf")
        for count in range(1,len(self.paths) + 1):
            condidate_paths = self.paths[:count]
            trial = Simulator(self.map_data, condidate_paths)
            