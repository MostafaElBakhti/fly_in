from classes import Zone, ZoneMetadata, Connection

class Map:

    def __init__(self):
        self.nb_drones = 0
        self.start_hub = None
        self.end_hub = None
        self.zones = []
        self.connections = []
        self.zone_by_name = {}

    def build_neighbors(self):
        for connection in  self.connections:
            zone_a = connection.zone_a
            zone_b = connection.zone_b

            zone_a.neighbors[zone_b] = connection
            zone_b.neighbors[zone_a] = connection

    def dijkstra(self):

        distances = {}
        previous = {}

        for zone in self.zone_by_name.values():
            distances[zone] = float("inf")
            revious[zone] = None

        distances[self.start_hub] = 0
        unvisited = set(self.zone_by_name.values())


        while unvisited:

            current = min(
                unvisited,
                key=lambda zone : (
                    distances[zone],
                    0 if zone.metadata.zone == "priority" else 1
                )
            )
        
        if distances[current] == float("inf"):
            break

        unvisited.remove(current)

        if current == self.end_hub:
            break


    # def dijkstra(self):
        distances = {}
        previous = {}

        for zone in self.zone_by_name.values():
            distances[zone] = float("inf")
            previous[zone] = None

        distances[self.start_hub] = 0

        unvisited = set(self.zone_by_name.values())

        while unvisited:

            current = min(
                unvisited,
                key=lambda zone: (
                    distances[zone],
                    0 if zone.metadata.zone == "priority" else 1
                )
            )

            if distances[current] == float("inf"):
                break

            unvisited.remove(current)

            if current == self.end_hub:
                break

            for neighbor, connection in current.neighbors.items():

                if neighbor.metadata.zone == "blocked":
                    continue

                if neighbor.metadata.zone == "restricted":
                    cost = 2
                else:
                    cost = 1

                new_distance = distances[current] + cost

                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous[neighbor] = current

                elif new_distance == distances[neighbor]:
                    if neighbor.metadata.zone == "priority":
                        previous[neighbor] = current

        if distances[self.end_hub] == float("inf"):
            return None

        path = []
        current = self.end_hub

        while current is not None:
            path.append(current)
            current = previous[current]

        path.reverse()

        return path

data = Map()

with open("map1.txt", "r") as f:
    lines = f.readlines()

    if not lines :
            print("nothing to print")

# def get_neighbors(data):
#     for connection in data.connections:




def parse_zone(line):
    value = line.split(":", 1)[1].strip()

    zone_type = "normal"
    color = "none"
    max_drones = 1

    if "[" in value:
        main, zonemetadata = value.split("[", 1)

        main = main.strip()
        zonemetadata = zonemetadata.rstrip("]")

        parts = zonemetadata.split()

        for part in parts:
            key, value = part.split("=", 1)

            if key == "zone":
                zone_type = value

            elif key == "color":
                color = value

            elif key == "max_drones":
                max_drones = int(value)

    else:
        main = value

    name, x, y = main.split()

    x = int(x)
    y = int(y)

    metadata = ZoneMetadata(zone_type, color, max_drones)

    zone = Zone(name, x, y, metadata)

    if name in data.zone_by_name:
        raise ValueError(f"Duplicate zone name: {name}")

    data.zone_by_name[name] = zone
    return zone

for line in lines:
    line = line.strip()

    # print(line)
    try:



        if line.startswith("nb_drones"):
            key , value = line.split(":", 1)
            # print(f"key: {key} --- value:{value}")
            nb_drones = int(value.strip())
            # print(nb_drones)
            data.nb_drones = nb_drones
        elif line.startswith("start_hub:"):
            data.start_hub = parse_zone(line)

        elif line.startswith("end_hub:"):
            data.end_hub = parse_zone(line)

        elif line.startswith("hub:"):
            data.zones.append(parse_zone(line))

        elif line.startswith("connection:"):
            key, value = line.split(":", 1)
            value = value.strip()
            # print(key , value)

            max_link_capacity = 1

            if "[" in value:
                main, connectionmetadata = value.split("[", 1)

                main = main.strip()
                connectionmetadata = connectionmetadata.rstrip("]")

                key , value = connectionmetadata.split("=", 1)

                if key == "max_link_capacity":
                    max_link_capacity = int(value)
            else:
                main = value

            name_a, name_b = main.split("-")

            if name_a not in data.zone_by_name:
                raise ValueError(f"Connection references undefined zone: {name_a}")
            if name_b not in data.zone_by_name:
                raise ValueError(f"Connection references undefined zone: {name_b}")

            zone_a = data.zone_by_name[name_a]
            zone_b = data.zone_by_name[name_b]

            for connection in data.connections:
                if (
                    connection.zone_a == zone_a and connection.zone_b == zone_b
                ) or (
                    connection.zone_a == zone_b and connection.zone_b == zone_a
                ):
                    raise ValueError("Duplicate connection")

            connection = Connection(zone_a, zone_b, max_link_capacity)
            data.connections.append(connection)



    except:
        print("not found")

# for test in data.connections:
#     print(test.zone_a.name, test.zone_b.name)
# print(data.nb_drones)
# # nb_drones: 5

data.build_neighbors()
data.dijkstra()

# for zone in data.zone_by_name.values():
#     print(f"\nZone: {zone.name}")

#     for neighbor, connection in zone.neighbors.items():
#         print(
#             f"  neighbor: {neighbor.name} "
#             f"| capacity: {connection.max_link_capacity}"
#         )