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
        elif line.startswith("start_hub"):
            ...

    except:
        print("not found")


# nb_drones: 5