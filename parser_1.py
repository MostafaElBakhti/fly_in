from classes import Connection, Zone, ZoneMetadata
from map import Map


def parse_zone(line, data, zone_name):
    value = line.split(":", 1)[1].strip()
    zones = ["normal", "blocked", "restricted", "priority"]
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
        
    zone_type = zone_type.lower()
    if zone_type not in zones:
        raise ValueError("invalid zone type")

    name, x, y = main.split()
    if " " in name or "-" in name:
        raise ValueError("Invalid zone name")
    if zone_name == "hub:":
        if max_drones < 0 :
            raise ValueError("max_drones must be positive integers")
    try:
        x = int(x)
        y = int(y)
    except ValueError:
        raise ValueError("enter a valid integer coordinates")
    metadata = ZoneMetadata(zone_type, color, max_drones)
    zone = Zone(name, x, y, metadata)

    if name in data.zone_by_name:
        raise ValueError(f"Duplicate zone name: {name}")

    data.zone_by_name[name] = zone
    return zone


def parse_connection(line, data ):
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
        nm = ""
        if line.startswith("nb_drones:"):
            try:
                nb = int(line.split(":", 1)[1].strip())

                if nb <= 0:
                    raise ValueError( "nb_drones must be positive or more than 0" )
                data.nb_drones = nb
            except ValueError as er: 
                print(f"Invalid nb_drones: {er}")
                exit(0)

        elif line.startswith("start_hub:"):
            nm = "start_hub:"
            try:
                data.start_hub = parse_zone(line, data , nm)
                # data.start_hub.metadata.max_drones = data.nb_drones
                
                # print(data.start_hub.metadata.max_drones)
            except ValueError as er :
                print(er)
                exit(0)
        elif line.startswith("end_hub:"):
            nm = "end_hub:"
            try:
                data.end_hub = parse_zone(line, data , nm)
                # data.end_hub.metadata.max_drones = data.nb_drones

                # print(data.end_hub.metadata.max_drones)
            except ValueError as er:
                print(er)
                exit(0)
        elif line.startswith("hub:"):
            nm = "hub:"
            try:
                data.zones.append(parse_zone(line, data, nm))
            except ValueError as er:
                print(er)
                exit(0)
        # elif line.startswith("connection:"):
        #     data.connections.append(parse_connection(line, data))

    data.build_neighbors()
    return data
