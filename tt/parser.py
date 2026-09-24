from classes import Connection, Zone, ZoneMetadata
from map import Map


def parse_zone(line, data):
    value = line.split(":", 1)[1].strip()
    zone_type = "normal"
    color = "none"
    max_drones = 1

    if "[" in value:
        main, zonemetadata = value.split("[", 1)
        main = main.strip()
        zonemetadata = zonemetadata.rstrip("]")

        for part in zonemetadata.split():
            key, val = part.split("=", 1)
            if key == "zone":
                zone_type = val
            elif key == "color":
                color = val
            elif key == "max_drones":
                max_drones = int(val)
    else:
        main = value

    name, x, y = main.split()
    metadata = ZoneMetadata(zone_type, color, max_drones)
    zone = Zone(name, int(x), int(y), metadata)

    if name in data.zone_by_name:
        raise ValueError(f"Duplicate zone name: {name}")

    data.zone_by_name[name] = zone
    return zone


def parse_connection(line, data):
    value = line.split(":", 1)[1].strip()
    max_link_capacity = 1

    if "[" in value:
        main, conn_meta = value.split("[", 1)
        main = main.strip()
        conn_meta = conn_meta.rstrip("]")
        key, val = conn_meta.split("=", 1)
        if key == "max_link_capacity":
            max_link_capacity = int(val)
    else:
        main = value

    name_a, name_b = main.split("-")
    zone_a = data.zone_by_name[name_a]
    zone_b = data.zone_by_name[name_b]

    return Connection(zone_a, zone_b, max_link_capacity)


def parse_map_file(filename):
    """Read a map file and return a fully built Map instance."""
    data = Map()

    with open(filename, "r") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("nb_drones:"):
            data.nb_drones = int(line.split(":", 1)[1].strip())
        elif line.startswith("start_hub:"):
            data.start_hub = parse_zone(line, data)
        elif line.startswith("end_hub:"):
            data.end_hub = parse_zone(line, data)
        elif line.startswith("hub:"):
            data.zones.append(parse_zone(line, data))
        elif line.startswith("connection:"):
            data.connections.append(parse_connection(line, data))

    data.build_neighbors()
    return data
