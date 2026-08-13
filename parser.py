from classes import Zone, ZoneMetadata

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

for line in lines:
    line = line.strip()

    print(line)
    try:
        if line.startswith("nb_drones"):
            key , value = line.split(":", 1)
            print(f"key: {key} --- value:{value}")
            nb_drones = int(value.strip())
            print(nb_drones)
            data.nb_drones = nb_drones
        elif line.startswith("start_hub:"):
            key, value = line.split(":", 1)
            print('-------------')
            value = value.strip()
            # print(key , value)
            main ,zonemetadata = value.split("[")
            main = main.strip()
            name, x, y = main.split()
            x = int(x)
            y = int(y)


            zonemetadata = zonemetadata.rstrip("]")
            print(main)
            print(zonemetadata)

            parts = zonemetadata.split()
            print(parts)


            zone = "normal"
            color = "none"
            max_drones = 1

            for part in parts:
                key , value = part.split("=")
                if key == "zone":
                    zone = value
                elif key == "color":
                    color = value
                elif key == "max_drones":
                    max_drones = int(value)
                print(key , value)
            metadata = ZoneMetadata(zone, color, max_drones)
            print('-------------')

            print(metadata.__dict__)
            print('-------------')

            print('-------------')

        elif line.startswith("end_hub:"):
            ...
        elif line.startswith("hub:"):
            ...

    except:
        print("not found")

print(data.nb_drones)
# nb_drones: 5