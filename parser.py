from classes import Zone, ZoneMetadata, Connection

class Map:

    def __init__(self):
        self.nb_drones = 0
        self.start_hub = None
        self.end_hub = None
        self.zones = []
        self.connections = []

data = Map()

with open("map.txt", "r") as f:
    lines = f.readlines()

    if not lines :
            print("nothing to print")

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

            zone_a, zone_b = main.split("-")

            connection = Connection(zone_a, zone_b, max_link_capacity)
            data.connections.append(connection)

            for test in data.connections:
                print(test.__dict__)


        # test = Map()

        # elif line.startswith("start_hub:"):
        #     key, value = line.split(":", 1)
        #     print('-------------')
        #     value = value.strip()
        #     # print(key , value)
        #     main ,zonemetadata = value.split("[")
        #     main = main.strip()
        #     name, x, y = main.split()
        #     x = int(x)
        #     y = int(y)


        #     zonemetadata = zonemetadata.rstrip("]")
        #     print(main)
        #     print(zonemetadata)

        #     parts = zonemetadata.split()
        #     print(parts)


        #     zone = "normal"
        #     color = "none"
        #     max_drones = 1

        #     for part in parts:
        #         key , value = part.split("=")
        #         if key == "zone":
        #             zone = value
        #         elif key == "color":
        #             color = value
        #         elif key == "max_drones":
        #             max_drones = int(value)
        #         print(key , value)
        #     metadata = ZoneMetadata(zone, color, max_drones)
        #     print('-------------')

        #     print(metadata.__dict__)
        #     print('-------------')

        #     print('-------------')

        # elif line.startswith("end_hub:"):
        #     ...
        # elif line.startswith("hub:"):
        #     ...

    except:
        print("not found")

print(data.nb_drones)
# nb_drones: 5