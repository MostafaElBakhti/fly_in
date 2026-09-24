from classes import Drone


class Simulator:

    def __init__(self, map_data, paths):
        self.map_data = map_data
        self.paths = paths
        self.drones = [
            Drone(i + 1, map_data.start_hub, map_data.end_hub)
            for i in range(map_data.nb_drones)
        ]
        self.history = []

    def assign_paths(self):
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

    def run(self):
        self.assign_paths()

        # zone_occupancy: drones physically sitting in a zone right now
        zone_occupancy = {
            zone: [] for zone in self.map_data.zone_by_name.values()
        }
        zone_occupancy[self.map_data.start_hub] = list(self.drones)

        # zone_reservations: drones mid-flight whose destination is this
        # zone (reserved the instant they depart, since a restricted move
        # can't wait for room to open up on arrival)
        zone_reservations = {
            zone: [] for zone in self.map_data.zone_by_name.values()
        }

        # connections currently being traversed by an in-flight drone
        connection_transit = {conn: 0 for conn in self.map_data.connections}

        self.record_snapshot(turn=0)

        turn = 1
        while any(not drone.finished for drone in self.drones):
            moves_this_turn = []

            # --- Phase 1: land every drone that was mid-flight ---
            for drone in self.drones:
                if drone.finished or drone.transit_turns != 1:
                    continue

                next_zone = drone.pending_zone
                connection = drone.pending_connection

                zone_reservations[next_zone].remove(drone)
                zone_occupancy[next_zone].append(drone)
                connection_transit[connection] -= 1

                drone.position += 1
                drone.current_zone = next_zone
                drone.transit_turns = 0
                drone.pending_zone = None
                drone.pending_connection = None

                moves_this_turn.append(f"{drone.name}-{next_zone.name}")

                if next_zone == self.map_data.end_hub:
                    drone.finished = True

            # --- Phase 2: let free drones attempt a new move.
            # Resolved as a fixed point: a drone only moves once its
            # destination is CONFIRMED to have room (not assumed), so a
            # drone vacating a zone this turn can free a slot for another
            # drone queued behind it within the same turn, but a drone
            # that fails to move never phantom-frees its old spot. ---
            link_usage = {conn: 0 for conn in self.map_data.connections}
            decided = set()
            progress = True

            while progress:
                progress = False

                for drone in self.drones:
                    if (
                        drone.finished
                        or drone.transit_turns != 0
                        or drone in decided
                    ):
                        continue

                    if drone.position + 1 >= len(drone.path):
                        continue

                    next_zone = drone.path[drone.position + 1]
                    curr_zone = drone.current_zone
                    connection = curr_zone.neighbors[next_zone]

                    used = link_usage[connection] + connection_transit[connection]
                    if used >= connection.max_link_capacity:
                        continue

                    is_hub = next_zone in (
                        self.map_data.start_hub,
                        self.map_data.end_hub,
                    )
                    occ = len(zone_occupancy[next_zone]) + len(
                        zone_reservations[next_zone]
                    )
                    if not (is_hub or occ < next_zone.metadata.max_drones):
                        continue

                    # Commit now, so later drones (this pass or the next)
                    # immediately see the freed slot / used-up capacity.
                    zone_occupancy[curr_zone].remove(drone)
                    link_usage[connection] += 1
                    decided.add(drone)
                    progress = True

                    if next_zone.metadata.zone == "restricted":
                        drone.transit_turns = 1
                        drone.pending_zone = next_zone
                        drone.pending_connection = connection
                        zone_reservations[next_zone].append(drone)
                        connection_transit[connection] += 1
                        moves_this_turn.append(
                            f"{drone.name}-{curr_zone.name}-{next_zone.name}"
                        )
                    else:
                        drone.position += 1
                        drone.current_zone = next_zone
                        zone_occupancy[next_zone].append(drone)
                        moves_this_turn.append(f"{drone.name}-{next_zone.name}")

                        if next_zone == self.map_data.end_hub:
                            drone.finished = True

            # Print move trace matching specified turn output format
            if moves_this_turn:
                print(" ".join(moves_this_turn))

            self.record_snapshot(turn=turn)
            turn += 1

    def record_snapshot(self, turn):
        snapshot = {
            "turn": turn,
            "positions": {
                drone.name: drone.current_zone for drone in self.drones
            },
        }
        self.history.append(snapshot)