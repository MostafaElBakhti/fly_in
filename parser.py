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
            main ,metadata = value.split("[")
            main = main.strip()
            name, x, y = main.split()
            x = int(x)
            y = int(y)
            metadata = metadata.rstrip("]")
            print('-------------')

        elif line.startswith("end_hub:"):
            ...
        elif line.startswith("hub:"):
            ...

    except:
        print("not found")

print(data.nb_drones)
# nb_drones: 5