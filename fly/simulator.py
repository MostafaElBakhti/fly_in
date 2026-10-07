"""Simulate drone movements one turn at a time."""
from copy import copy
import sys
from collections import Counter

from classes import Drone, Zone
from map import Map


class DeadlockError(Exception):
    pass

class Simulator:

    def __init__(self, map_data: Map, paths: list[list[Zone]]) -> None:
        self.map_data = map_data
        self.paths = paths
        # self.paths = [
        #     P1, P2, P3, P4, P5
        # ]
        # P1 = START → B → D → F → END
        # P2 = START → A → D → F → END
        # P3 = START → B → D → E → END
        # P4 = START → A → D → E → END
        # P5 = START → B → C → E → END
        self.drones = [
            Drone(i + 1, map_data.start_hub, map_data.end_hub)
            for i in range(map_data.nb_drones)
        ] 
        # D1 D2 D3 D4 D5 D6 D7 D8 D9 D10
        self.history: list[dict[str, tuple[float, float]]] = []
        # self.turns = 0

    def assign_paths(self) -> None:
        """Balance drones over routes using path cost and assigned count."""
        if not self.paths:
            raise ValueError("No valid paths found for assignment.")
        path_counts = [0] * len(self.paths)
        path_costs = [self.map_data.path_cost(path) for path in self.paths]
        for drone in self.drones:
            best_idx = 0
            min_eta = float("inf")
            for idx in range(len(self.paths)):
                eta = path_costs[idx] + path_counts[idx]
                if eta < min_eta:
                    min_eta = eta
                    best_idx = idx
            drone.path = self.paths[best_idx]
            path_counts[best_idx] += 1

    def _select_paths(self) -> None:
        """Compare schedules for each prefix of candidate routes."""
        if len(self.paths) <= 1:
            return
        best_paths = None
        best_turns = float("inf")
        for count in range(1, len(self.paths) + 1):
            candidate_paths = self.paths[:count]
            # candidate_paths = [
            #     [START, B, D, F, END]
            # ]
            trial = Simulator(self.map_data, candidate_paths)
            trial.assign_paths()
            try:
                turns = trial._simulate(record_output=False)
            except DeadlockError:
                continue
            if turns < best_turns:
                best_turns = turns
                best_paths = candidate_paths
        # for path in best_paths:
        #     print([zone.name for zone in path])

        if best_paths is None:
            raise DeadlockError(
                "No candidate route set can deliver all drones."
            )
        self.paths = best_paths
        # self.assign_paths()
    def _validate_paths(self) -> None:
        start = self.map_data.start_hub
        end = self.map_data.end_hub

        if start is None or end is None:
            raise ValueError("The map must have a start hub and an end hub.")
        if not self.paths:
            sys.exit("Error: no valid path connects start_hub to end_hub.")

        for path in self.paths:
            if not path or path[0] is not start:
                raise ValueError("A route must begin at the start hub.")
            if path[-1] is not end:
                raise ValueError("A route must finish at the end hub.")

            for source, destination in zip(path, path[1:]):
                if destination.metadata.zone == "blocked":
                    raise ValueError("A route enters a blocked zone.")
                if destination not in source.neighbors:
                    raise ValueError("A route uses a missing connection.")

    def run(self) -> int:
        """Print only movement turns on stdout; return the total turn count."""
        self._validate_paths() 
        self._select_paths() # gets the best paths 
        self.assign_paths() # assign for each drone a path 
        self.history.clear() # clear the last history 
        self.save_turn() # save the turn after completing phase 1 and phase 2
        self.turns = self._simulate() # simulate the best distrubition
        print(f"Final turns: {self.turns}", file=sys.stderr)
        return self.turns

    def save_turn(self) -> None:
        """Save drone coordinates; in-flight drones use link midpoints."""
        positions: dict[str, tuple[float, float]] = {}
        for drone in self.drones:
            x, y = float(drone.current_zone.x), float(drone.current_zone.y)
            if drone.pending_zone is not None:
                x = (x + drone.pending_zone.x) / 2
                y = (y + drone.pending_zone.y) / 2
            positions[drone.name] = (x, y)
        self.history.append(positions)

    def _plan_turn(
        self, current_drones: list[Drone], ignore_current: bool,
        waiting: set[int] | None = None,
    ) -> tuple[list[Drone], list[str]] | None:
        """Try one turn on copies, keeping the real drones unchanged."""

        drones = [copy(drone) for drone in current_drones]
        waiting = waiting or set()
        start_hub = self.map_data.start_hub
        end_hub = self.map_data.end_hub
        zone_occupancy = Counter(
            drone.current_zone for drone in drones if drone.transit_turns == 0
        )
        zone_reservations = Counter()
        link_usage = Counter()
        moved_this_turn = set()
        moves_this_turn = {}

        # Phase 1: 
        for drone in drones:
            if drone.transit_turns == 0:
                continue
            next_zone = drone.pending_zone
            if next_zone is None or drone.pending_connection is None:
                raise ValueError("In-flight drone has no destination.")
            zone_occupancy[next_zone] += 1
            drone.position += 1
            drone.current_zone = next_zone
            drone.transit_turns = 0
            drone.pending_zone = None
            drone.pending_connection = None
            drone.finished = next_zone is end_hub
            moved_this_turn.add(drone.id)
            moves_this_turn[drone.id] = f"{drone.name}-{next_zone.name}"

        # Phase 2
        progress = True
        while progress:
            progress = False
            for drone in drones:
                if (
                    drone.finished or drone.id in moved_this_turn
                    or drone.id in waiting
                ):
                    continue
                if drone.position + 1 >= len(drone.path):
                    continue
                next_zone = drone.path[drone.position + 1]
                curr_zone = drone.current_zone
                connection = curr_zone.neighbors[next_zone]
                if link_usage[connection] >= connection.max_link_capacity:
                    continue

                restricted = next_zone.metadata.zone == "restricted"
                is_hub = next_zone in (start_hub, end_hub)
                occupancy = zone_occupancy[next_zone]
                if restricted:
                    if ignore_current:  
                        occupancy = 0
                    occupancy += zone_reservations[next_zone]
                if not is_hub and occupancy >= next_zone.metadata.max_drones:
                    continue

                zone_occupancy[curr_zone] -= 1
                link_usage[connection] += 1
                moved_this_turn.add(drone.id)
                progress = True
                if restricted:
                    drone.transit_turns = 1
                    drone.pending_zone = next_zone
                    drone.pending_connection = connection
                    zone_reservations[next_zone] += 1
                    moves_this_turn[drone.id] = (
                        f"{drone.name}-{curr_zone.name}-{next_zone.name}"
                    )
                else:
                    zone_occupancy[next_zone] += 1
                    drone.position += 1
                    drone.current_zone = next_zone
                    drone.finished = next_zone is end_hub
                    moves_this_turn[drone.id] = (
                        f"{drone.name}-{next_zone.name}"
                    )

        for zone, occupancy in zone_occupancy.items():
            if zone not in (start_hub, end_hub):
                if occupancy > zone.metadata.max_drones:
                    return None
        output = [moves_this_turn[key] for key in sorted(moves_this_turn)]
        if not output and any(not drone.finished for drone in drones):
            return None
        return drones, output

    def _simulate(self, record_output: bool = True) -> int:
        """Finish arrivals, decide departures, and commit one safe turn."""
        # start_hub = self.map_data.start_hub
        # end_hub = self.map_data.end_hub
        # if start_hub is None or end_hub is None:
        #     raise ValueError("The map must have a start hub and an end hub.")
        # for drone in self.drones:
        #     if not drone.path or drone.path[0] is not start_hub:
        #         raise ValueError(f"{drone.name} has an invalid route.")
        #     if drone.path[-1] is not end_hub:
        #         raise ValueError(f"{drone.name} has an invalid destination.")
        #     for source, destination in zip(drone.path, drone.path[1:]):
        #         if destination.metadata.zone == "blocked":
        #             raise ValueError("A route enters a blocked zone.")
        #         if destination not in source.neighbors:
        #             raise ValueError("A route uses a missing connection.")

        turn = 1
        guaranteed_next_turn = None
        while any(not drone.finished for drone in self.drones):

            waiting = set()
            planned = None
            preview = None
            while True:
                planned = self._plan_turn(self.drones, True, waiting)
                preview = None  
                if planned is not None:
                    preview = self._plan_turn(planned[0], False)
                if preview is not None:
                    break

                departures = [
                    drone.id for drone in self.drones
                    if not drone.finished and not drone.transit_turns
                    and drone.id not in waiting
                ]
                if not departures:
                    break
                waiting.add(max(departures))
            if planned is None or preview is None or not planned[1]:

                planned = guaranteed_next_turn
                if planned is None:
                    planned = self._plan_turn(
                        self.drones, ignore_current=False,
                    )
                if planned is not None:
                    preview = self._plan_turn(planned[0], ignore_current=False)
            if planned is None or preview is None or not planned[1]:
                raise DeadlockError(f"No safe drone movement on turn {turn}.")

            next_drones, moves_this_turn = planned
            for drone, next_drone in zip(self.drones, next_drones):
                drone.position = next_drone.position
                drone.current_zone = next_drone.current_zone
                drone.finished = next_drone.finished
                drone.transit_turns = next_drone.transit_turns
                drone.pending_zone = next_drone.pending_zone
                drone.pending_connection = next_drone.pending_connection
            guaranteed_next_turn = preview
            if record_output:
                print(" ".join(moves_this_turn))
                self.save_turn()

                # i = 0
                # for zone, _ in self.map_data.zone_by_name.items():
                #     print(zone)
                #     i += 1
                #     if i == 1:
                #         break

                # for idx , drone in enumerate(self.drones):
                #     print("**" * 5)
                #     print(f" in turn {turn} : the drone  {idx +1} is in {drone.name} ")
                #     print("**" * 5)
                # for  path in (self.paths):
                #     print(path)
            turn += 1
        return turn - 1
