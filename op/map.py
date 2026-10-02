class Map:

    def __init__(self):
        self.nb_drones = 0
        self.start_hub = None
        self.end_hub = None
        self.zones = []
        self.connections = []
        self.zone_by_name = {}

    def build_neighbors(self):
        for connection in self.connections:
            zone_a = connection.zone_a
            zone_b = connection.zone_b

            zone_a.neighbors[zone_b] = connection
            zone_b.neighbors[zone_a] = connection

    def path_cost(self, path):
        cost = 0
        for zone in path[1:]:
            cost += 2 if zone.metadata.zone == "restricted" else 1
        return cost

    def path_priority(self, path):
        score = 0
        for zone in path:
            if zone.metadata.zone == "priority":
                score += 1
        return score

    def dijkstra(
        self,
        start=None,
        end=None,
        forbidden_connections=None,
        forbidden_nodes=None,
    ):
        if start is None:
            start = self.start_hub
        if end is None:
            end = self.end_hub

        forbidden_connections = forbidden_connections or set()
        forbidden_nodes = forbidden_nodes or set()

        distances = {}
        previous = {}
        priority_score = {}

        for zone in self.zone_by_name.values():
            distances[zone] = float("inf")
            previous[zone] = None
            priority_score[zone] = 0

        distances[start] = 0

        unvisited = set(
            zone
            for zone in self.zone_by_name.values()
            if zone.metadata.zone != "blocked" and zone not in forbidden_nodes
        )

        while unvisited:
            current = min(
                unvisited,
                key=lambda zone: (distances[zone], -priority_score[zone]),
            )

            if distances[current] == float("inf"):
                break

            unvisited.remove(current)

            if current == end:
                break

            for neighbor, connection in current.neighbors.items():
                if neighbor not in unvisited:
                    continue
                
                if (
                    connection in forbidden_connections
                    or neighbor in forbidden_nodes
                ):
                    continue

                if neighbor.metadata.zone == "blocked":
                    continue

                cost = 2 if neighbor.metadata.zone == "restricted" else 1
                new_distance = distances[current] + cost

                bonus = 1 if neighbor.metadata.zone == "priority" else 0
                new_score = priority_score[current] + bonus

                if new_distance < distances[neighbor] or (
                    new_distance == distances[neighbor]
                    and new_score > priority_score[neighbor]
                ):
                    distances[neighbor] = new_distance
                    priority_score[neighbor] = new_score
                    previous[neighbor] = current

        if distances[end] == float("inf"):
            return None

        path = []
        current = end
        while current is not None:
            path.append(current)
            current = previous[current]

        path.reverse()
        return path



    def find_all_paths(self, max_paths=5):
        first_path = self.dijkstra()
        if first_path is None:
            return []

        paths = [first_path]
        candidates = []

        while len(paths) < max_paths:
            previous_path = paths[-1]

            for i in range(len(previous_path) - 1): #3
                spur_node = previous_path[i]
                root_path = previous_path[:i + 1]

                forbidden_nodes = set(root_path[:-1])
                forbidden_connections = set()

                for path in paths:
                    if len(path) > i + 1 and path[:i + 1] == root_path:
                        zone_a = path[i] #S
                        zone_b = path[i + 1] #C
                        connection = zone_a.neighbors.get(zone_b)
                        if connection:
                            forbidden_connections.add(connection)
                        # forbidden_connections = {connection_S_C}
                spur_path = self.dijkstra(
                    start=spur_node,
                    end=self.end_hub,
                    forbidden_connections=forbidden_connections,
                    forbidden_nodes=forbidden_nodes,
                )

                if spur_path is None:
                    continue

                total_path = root_path[:-1] + spur_path

                if total_path not in paths and total_path not in candidates:
                    candidates.append(total_path)

            if not candidates:
                break

            best_path = min(
                candidates,
                key=lambda path: (
                    self.path_cost(path),
                    -self.path_priority(path),
                ),
            )

            candidates.remove(best_path)
            paths.append(best_path)

        return paths
