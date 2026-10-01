from map import Map
from classes import Drone, Zone


class DeadlockError(Exception):
    """Raised when no drone can make further progress."""
    pass


class Simulator:

    def __init__(self, map_data: Map, paths: list[list[Zone]]) -> None:
        self.map_data = map_data
        self.paths = paths

        self.drones = [
            Drone(
                i + 1,
                map_data.start_hub,
                map_data.end_hub
            )
            for i in range(map_data.nb_drones)
        ]

        self.history = []


    def assign_paths(self) -> None:
        if not self.paths:
            raise ValueError("No valid paths found for assignment.")

        path_counts = [0] * len(self.paths)

        # Calculate each path cost only ONCE.
        path_costs = [
            self.map_data.path_cost(path)
            for path in self.paths
        ]

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

    # ============================================================
    # SELECT BEST NUMBER OF PATHS
    # ============================================================

    def _select_paths(self) -> None:
        if len(self.paths) <= 1:
            return

        best_paths = None
        best_turns = float("inf")

        for count in range(1, len(self.paths) + 1):
            candidate_paths = self.paths[:count]

            trial = Simulator(
                self.map_data,
                candidate_paths
            )

            trial.assign_paths()

            try:
                turns = trial._simulate(
                    emit_output=False
                )

            except DeadlockError:
                continue

            if turns < best_turns:
                best_turns = turns
                best_paths = candidate_paths

        if best_paths is None:
            raise DeadlockError(
                "No candidate route set can deliver all drones."
            )

        self.paths = best_paths

    # ============================================================
    # RUN
    # ============================================================

    def run(self) -> None:
        self._select_paths()
        self.assign_paths()
        self._simulate()

    # ============================================================
    # SIMULATION
    # ============================================================

    def _simulate(self, emit_output: bool = True) -> int:

        start_hub = self.map_data.start_hub
        end_hub = self.map_data.end_hub

        if start_hub is None:
            raise ValueError("The map has no start hub.")

        if end_hub is None:
            raise ValueError("The map has no end hub.")

        # --------------------------------------------------------
        # Occupancy
        # --------------------------------------------------------

        zone_occupancy = {
            zone: []
            for zone in self.map_data.zone_by_name.values()
        }

        zone_occupancy[start_hub] = list(self.drones)

        # --------------------------------------------------------
        # Reservations
        # --------------------------------------------------------

        zone_reservations = {
            zone: []
            for zone in self.map_data.zone_by_name.values()
        }

        # --------------------------------------------------------
        # Connection usage
        # --------------------------------------------------------

        connection_transit = {
            connection: 0
            for connection in self.map_data.connections
        }

        # Only drones actually flying on restricted connections.
        in_transit: set[Drone] = set()

        # Instead of:
        #
        # while any(not drone.finished ...)
        #
        # we keep a counter.
        finished_count = 0

        turn = 1

        # ========================================================
        # MAIN LOOP
        # ========================================================

        while finished_count < len(self.drones):

            moves_this_turn = []

            moved_this_turn: set[Drone] = set()

            # Copy the connection usage at the beginning
            # of the turn.
            link_usage = connection_transit.copy()

            # ====================================================
            # PHASE 1
            #
            # Finish restricted movements from the previous turn.
            # ====================================================

            # We only inspect drones that are actually in transit.
            arriving_drones = list(in_transit)

            for drone in arriving_drones:

                next_zone = drone.pending_zone
                connection = drone.pending_connection

                if next_zone is None or connection is None:
                    raise ValueError(
                        "In-flight drone has no destination."
                    )

                # Remove reservation.
                zone_reservations[next_zone].remove(drone)

                # Drone physically arrives.
                zone_occupancy[next_zone].append(drone)

                # Connection is no longer occupied.
                connection_transit[connection] -= 1

                # Drone is no longer in transit.
                in_transit.remove(drone)

                # Update drone.
                drone.position += 1
                drone.current_zone = next_zone

                drone.transit_turns = 0
                drone.pending_zone = None
                drone.pending_connection = None

                # IMPORTANT:
                # the drone already moved this turn.
                moved_this_turn.add(drone)

                moves_this_turn.append(
                    f"{drone.name}-{next_zone.name}"
                )

                # Check if it reached the destination.
                if next_zone == end_hub:
                    drone.finished = True
                    finished_count += 1

            # ====================================================
            # PHASE 2
            #
            # Start new movements.
            # ====================================================

            decided = moved_this_turn

            progress = True

            while progress:

                progress = False

                for drone in self.drones:

                    # --------------------------------------------
                    # Drone cannot move
                    # --------------------------------------------

                    if (
                        drone.finished
                        or drone.transit_turns != 0
                        or drone in decided
                    ):
                        continue

                    # --------------------------------------------
                    # No next zone
                    # --------------------------------------------

                    if drone.position + 1 >= len(drone.path):
                        continue

                    next_zone = drone.path[
                        drone.position + 1
                    ]

                    curr_zone = drone.current_zone

                    connection = curr_zone.neighbors[
                        next_zone
                    ]

                    # --------------------------------------------
                    # Connection capacity
                    # --------------------------------------------

                    used = link_usage[connection]

                    if used >= connection.max_link_capacity:
                        continue

                    # --------------------------------------------
                    # Zone capacity
                    # --------------------------------------------

                    is_hub = next_zone in (
                        start_hub,
                        end_hub
                    )

                    occupancy = (
                        len(zone_occupancy[next_zone])
                        +
                        len(zone_reservations[next_zone])
                    )

                    if not (
                        is_hub
                        or occupancy
                        < next_zone.metadata.max_drones
                    ):
                        continue

                    # ============================================
                    # MOVEMENT CONFIRMED
                    # ============================================

                    # Drone leaves current zone.
                    zone_occupancy[curr_zone].remove(drone)

                    # Connection used this turn.
                    link_usage[connection] += 1

                    # Drone cannot move again this turn.
                    decided.add(drone)

                    # Something changed, so another pass
                    # may allow another drone to move.
                    progress = True

                    # ============================================
                    # RESTRICTED ZONE
                    # ============================================

                    if next_zone.metadata.zone == "restricted":

                        drone.transit_turns = 1

                        drone.pending_zone = next_zone
                        drone.pending_connection = connection

                        # Reserve destination capacity.
                        zone_reservations[next_zone].append(
                            drone
                        )

                        # Connection remains occupied.
                        connection_transit[connection] += 1

                        # Remember exactly which drones
                        # are currently flying.
                        in_transit.add(drone)

                        moves_this_turn.append(
                            f"{drone.name}-"
                            f"{curr_zone.name}-"
                            f"{next_zone.name}"
                        )

                    # ============================================
                    # NORMAL / PRIORITY / END
                    # ============================================

                    else:

                        drone.position += 1
                        drone.current_zone = next_zone

                        zone_occupancy[next_zone].append(
                            drone
                        )

                        moves_this_turn.append(
                            f"{drone.name}-{next_zone.name}"
                        )

                        # ----------------------------------------
                        # Reached destination
                        # ----------------------------------------

                        if next_zone == end_hub:
                            drone.finished = True
                            finished_count += 1

            # ====================================================
            # DEADLOCK
            # ====================================================

            if not moves_this_turn:
                raise DeadlockError(
                    f"No drone can move on turn {turn}; "
                    "assigned routes block."
                )

            # ====================================================
            # OUTPUT
            # ====================================================

            if emit_output:
                print(" ".join(moves_this_turn))

            turn += 1

        # Return number of turns instead of saving thousands
        # of snapshots during trial simulations.
        return turn - 1