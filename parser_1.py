from classes import Connection, Zone, ZoneMetadata
from map import Map


ZONE_TYPES = ["normal", "blocked", "restricted", "priority"]


def parse_metadata(value: str) -> tuple[str, dict[str, str]]:
    if "[" not in value and "]" not in value:
        return value.strip(), {}

    if value.count("[") != 1 or value.count("]") != 1:
        raise ValueError("invalid metadata brackets")
    if not value.endswith("]"):
        raise ValueError("metadata must be at the end of the line")

    main, metadata_text = value[:-1].split("[", 1)
    main = main.strip()
    metadata = {}

    for part in metadata_text.split():
        if part.count("=") != 1:
            raise ValueError(f"invalid metadata tag: {part}")
        key, val = part.split("=", 1)
        if not key or not val:
            raise ValueError(f"invalid metadata tag: {part}")
        if key in metadata:
            raise ValueError(f"duplicate metadata tag: {key}")
        metadata[key] = val

    return main, metadata


def positive_integer(value: str, field_name: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise ValueError(
            f"{field_name} must be a positive integer"
        ) from None

    if number <= 0:
        raise ValueError(f"{field_name} must be a positive integer")
    return number


def valid_zone_name(name: str) -> bool:

    return bool(name) and "-" not in name and not any(
        char.isspace() for char in name
    )


def parse_zone(line: str, data: Map, zone_name: str) -> Zone:
    value = line.split(":", 1)[1].strip()
    main, metadata_values = parse_metadata(value)

    allowed_metadata = {"zone", "color", "max_drones"}
    for key in metadata_values:
        if key not in allowed_metadata:
            raise ValueError(f"unknown zone metadata: {key}")

    parts = main.split()
    if len(parts) != 3:
        raise ValueError("zone must contain a name and two coordinates")

    name, x_value, y_value = parts
    if not valid_zone_name(name):
        raise ValueError(f"invalid zone name: {name}")
    if name in data.zone_by_name:
        raise ValueError(f"duplicate zone name: {name}")

    try:
        x = int(x_value)
        y = int(y_value)
    except ValueError:
        raise ValueError("zone coordinates must be integers") from None

    zone_type = metadata_values.get("zone", "normal").lower()
    if zone_type not in ZONE_TYPES:
        raise ValueError(f"invalid zone type: {zone_type}")

    color = metadata_values.get("color", "none")
    if not color or any(char.isspace() for char in color):
        raise ValueError("color must be a single word")

    max_drones = 1
    if zone_name == "hub:" and "max_drones" in metadata_values:
        max_drones = positive_integer(
            metadata_values["max_drones"], "max_drones"
        )

    metadata = ZoneMetadata(zone_type, color, max_drones)
    zone = Zone(name, x, y, metadata)
    data.zone_by_name[name] = zone
    return zone


def parse_connection(line: str, data: Map) -> Connection:
    value = line.split(":", 1)[1].strip()
    main, metadata_values = parse_metadata(value)

    allowed_metadata = {"max_link_capacity"}
    for key in metadata_values:
        if key not in allowed_metadata:
            raise ValueError(f"unknown connection metadata: {key}")

    if main.count("-") != 1 or any(char.isspace() for char in main):
        raise ValueError("connection must use the format <zone1>-<zone2>")

    name_a, name_b = main.split("-", 1)
    if not valid_zone_name(name_a) or not valid_zone_name(name_b):
        raise ValueError("connection contains an invalid zone name")
    if name_a not in data.zone_by_name:
        raise ValueError(f"undefined zone in connection: {name_a}")
    if name_b not in data.zone_by_name:
        raise ValueError(f"undefined zone in connection: {name_b}")

    zone_a = data.zone_by_name[name_a]
    zone_b = data.zone_by_name[name_b]
    for connection in data.connections:
        same_order = (
            connection.zone_a is zone_a and connection.zone_b is zone_b
        )
        reverse_order = (
            connection.zone_a is zone_b and connection.zone_b is zone_a
        )
        if same_order or reverse_order:
            raise ValueError(f"duplicate connection: {name_a}-{name_b}")

    max_link_capacity = 1
    if "max_link_capacity" in metadata_values:
        max_link_capacity = positive_integer(
            metadata_values["max_link_capacity"],
            "max_link_capacity",
        )

    return Connection(zone_a, zone_b, max_link_capacity)


def parse_map_file(filename: str) -> Map:
    data = Map()
    found_nb_drones = False
    found_start = False
    found_end = False
    first_definition = True

    try:
        with open(filename, "r") as file:
            lines = file.readlines()
    except (OSError, UnicodeError) as error:
        raise ValueError(f"cannot read map file: {error}")

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue

        try:
            if first_definition and not line.startswith("nb_drones:"):
                raise ValueError("first definition must be nb_drones")
            first_definition = False

            if line.startswith("nb_drones:"):
                if found_nb_drones:
                    raise ValueError("nb_drones is defined more than once")
                value = line.split(":", 1)[1].strip()
                if not value or len(value.split()) != 1:
                    raise ValueError("invalid nb_drones definition")
                data.nb_drones = positive_integer(value, "nb_drones")
                found_nb_drones = True

            elif line.startswith("start_hub:"):
                if found_start:
                    raise ValueError("start_hub is defined more than once")
                data.start_hub = parse_zone(line, data, "start_hub:")
                found_start = True

            elif line.startswith("end_hub:"):
                if found_end:
                    raise ValueError("end_hub is defined more than once")
                data.end_hub = parse_zone(line, data, "end_hub:")
                found_end = True

            elif line.startswith("hub:"):
                data.zones.append(parse_zone(line, data, "hub:"))

            elif line.startswith("connection:"):
                data.connections.append(parse_connection(line, data))

            else:
                raise ValueError("unknown definition")
        except ValueError as error:
            raise ValueError(f"line {line_number}: {error}") from None

    if first_definition:
        raise ValueError("line 1: map file is empty")
    if not found_start:
        raise ValueError(
            f"line {len(lines) + 1}: missing start_hub definition"
        )
    if not found_end:
        raise ValueError(
            f"line {len(lines) + 1}: missing end_hub definition"
        )

    data.build_neighbors()
    return data
