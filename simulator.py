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
                eta = cost + path_counts[idx]
                if eta < min_eta:
                    min_eta = eta
                    best_idx = idx

            drone.path = self.paths[best_idx]
            path_counts[best_idx] += 1


    def _select_paths(self) : 
        if len(self.paths) <= 1:
            return 
        
        best_paths = None
        best_turns = float("inf")
        for count in range(1,len(self.paths) + 1):
            condidate_paths = self.paths[:count]
            trial = Simulator(self.map_data, condidate_paths)
            trial.assign_paths()
            try:
                trial._simulate(emit_output=False)
            except DeadlockError:
                continue
            
    
    def _simulate(self, emit_output: bool = True) -> None:

        start_hub = self.map_data.start_hub
        if start_hub is None:
            raise ValueError("The map has no start hub.")

        zone_occupancy = {
            zone: [] for zone in self.map_data.zone_by_name.values()
        }
        zone_occupancy[start_hub] = list(self.drones)

        zone_reservations = {
            zone: [] for zone in self.map_data.zone_by_name.values()
        }

        connection_transit = {conn: 0 for conn in self.map_data.connections}

        turn = 1
        while any(not drone.finished for drone in self.drones):
            moves_this_turn = []
            moved_this_turn = set()

            link_usage = connection_transit.copy()
            for drone in self.drones:
                if drone.finished or drone.transit_turns != 1:
                    continue
                
                next_zone = drone.pending_zone
                connection = drone.pending_connection
                if next_zone is None or connection is None:
                    raise ValueError("In-flight drone has no destination.")

                zone_reservations[next_zone].remove(drone)
                zone_occupancy[next_zone].append(drone)
                connection_transit[connection] -= 1

                drone.position += 1