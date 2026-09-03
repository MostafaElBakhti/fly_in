from typing import Dict, List, Optional
from classes import Zone, ZoneMetadata, Connection


class ParseError(Exception):
    """Raised when the input file violates the expected format."""


class Map:
    """Holds the parsed zone/connection graph and drone count."""

    def __init__(self) -> None:
        self.nb_drones: int = 0
        self.start_hub: Optional[Zone] = None
        self.end_hub: Optional[Zone] = None
        self.zones: List[Zone] = []
        self.connections: List[Connection] = []
        self.zone_by_name: Dict[str, Zone] = {}

    def build_neighbors(self) -> None:
        """Populate each zone's neighbors dict from self.connections."""
        for connection in self.connections:
            connection.zone_a.neighbors[connection.zone_b] = connection
            connection.zone_b.neighbors[connection.zone_a] = connection

    def dijkstra(self) -> Optional[List[Zone]]:
        """Return the lowest-cost path from start_hub to end_hub, or None."""
        assert self.start_hub is not None and self.end_hub is not None
        distances: Dict[Zone, float] = {}
        previous: Dict[Zone, Optional[Zone]] = {}

        for zone in self.zone_by_name.values():
            distances[zone] = float("inf")
            previous[zone] = None

        distances[self.start_hub] = 0

        unvisited = {
            zone for zone in self.zone_by_name.values()
            if zone.metadata.zone != "blocked"
        }

        while unvisited:
            current = min(
                unvisited,
                key=lambda zone: (
                    distances[zone],
                    0 if zone.metadata.zone == "priority" else 1,
                ),
            )

            if distances[current] == float("inf"):
                break

            unvisited.remove(current)

            if current == self.end_hub:
                break

            for neighbor, _connection in current.neighbors.items():
                cost = 2 if neighbor.metadata.zone == "restricted" else 1
                new_distance = distances[current] + cost

                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous[neighbor] = current
                elif new_distance == distances[neighbor] and neighbor.metadata.zone == "priority":
                    previous[neighbor] = current

        if distances[self.end_hub] == float("inf"):
            return None

        path: List[Zone] = []
        node: Optional[Zone] = self.end_hub
        while node is not None:
            path.append(node)
            node = previous[node]
        path.reverse()
        return path


class Parser:
    """Parses a map definition file into a Map object."""

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.map = Map()

    def parse(self) -> Map:
        with open(self.filepath, "r") as f:
            lines = f.readlines()

        if not lines:
            raise ParseError("Empty input file")

        for line_no, raw_line in enumerate(lines, start=1):
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            try:
                self._parse_line(line)
            except ValueError as exc:
                raise ParseError(f"Line {line_no}: {exc} -> '{raw_line.strip()}'") from exc

        self._validate()
        self.map.build_neighbors()
        return self.map

    def _parse_line(self, line: str) -> None:
        if line.startswith("nb_drones"):
            self._parse_nb_drones(line)
        elif line.startswith("start_hub:"):
            zone = self._parse_zone(line)
            if self.map.start_hub is not None:
                raise ValueError("Duplicate start_hub definition")
            self.map.start_hub = zone
        elif line.startswith("end_hub:"):
            zone = self._parse_zone(line)
            if self.map.end_hub is not None:
                raise ValueError("Duplicate end_hub definition")
            self.map.end_hub = zone
        elif line.startswith("hub:"):
            self.map.zones.append(self._parse_zone(line))
        elif line.startswith("connection:"):
            self._parse_connection(line)
        else:
            raise ValueError("Unrecognized line format")

    def _parse_nb_drones(self, line: str) -> None:
        _, value = line.split(":", 1)
        nb = int(value.strip())
        if nb <= 0:
            raise ValueError("nb_drones must be a positive integer")
        self.map.nb_drones = nb

    @staticmethod
    def _validate_name(name: str) -> None:
        if "-" in name or " " in name or not name:
            raise ValueError(f"Invalid zone name: {name!r}")

    def _parse_zone(self, line: str) -> Zone:
        value = line.split(":", 1)[1].strip()

        zone_type = "normal"
        color = "none"
        max_drones = 1

        if "[" in value:
            if not value.endswith("]"):
                raise ValueError("Malformed metadata block")
            main, metadata_block = value.split("[", 1)
            main = main.strip()
            metadata_block = metadata_block.rstrip("]")

            for part in metadata_block.split():
                if "=" not in part:
                    raise ValueError(f"Malformed metadata tag: {part}")
                key, val = part.split("=", 1)
                if key == "zone":
                    zone_type = val
                elif key == "color":
                    color = val
                elif key == "max_drones":
                    max_drones = int(val)
                else:
                    raise ValueError(f"Unknown zone metadata key: {key}")
        else:
            main = value

        parts = main.split()
        if len(parts) != 3:
            raise ValueError("Expected '<name> <x> <y>'")
        name, x_str, y_str = parts
        self._validate_name(name)

        if name in self.map.zone_by_name:
            raise ValueError(f"Duplicate zone name: {name}")

        zone = Zone(name, int(x_str), int(y_str), ZoneMetadata(zone_type, color, max_drones))
        self.map.zone_by_name[name] = zone
        return zone

    def _parse_connection(self, line: str) -> None:
        value = line.split(":", 1)[1].strip()
        max_link_capacity = 1

        if "[" in value:
            if not value.endswith("]"):
                raise ValueError("Malformed metadata block")
            main, metadata_block = value.split("[", 1)
            main = main.strip()
            metadata_block = metadata_block.rstrip("]")
            for part in metadata_block.split():
                if "=" not in part:
                    raise ValueError(f"Malformed connection metadata tag: {part}")
                key, val = part.split("=", 1)
                if key == "max_link_capacity":
                    max_link_capacity = int(val)
                else:
                    raise ValueError(f"Unknown connection metadata key: {key}")
        else:
            main = value

        if main.count("-") != 1:
            raise ValueError(f"Malformed connection: {main}")
        name_a, name_b = main.split("-")

        if name_a == name_b:
            raise ValueError(f"Self-loop connection not allowed: {name_a}")
        if name_a not in self.map.zone_by_name:
            raise ValueError(f"Connection references undefined zone: {name_a}")
        if name_b not in self.map.zone_by_name:
            raise ValueError(f"Connection references undefined zone: {name_b}")

        zone_a = self.map.zone_by_name[name_a]
        zone_b = self.map.zone_by_name[name_b]

        for connection in self.map.connections:
            if {connection.zone_a, connection.zone_b} == {zone_a, zone_b}:
                raise ValueError("Duplicate connection")

        self.map.connections.append(Connection(zone_a, zone_b, max_link_capacity))

    def _validate(self) -> None:
        if self.map.start_hub is None:
            raise ParseError("Missing start_hub definition")
        if self.map.end_hub is None:
            raise ParseError("Missing end_hub definition")


if __name__ == "__main__":
    parser = Parser("map.txt")
    data = parser.parse()
    path = data.dijkstra()
    if path is None:
        print("No path")
    else:
        print(" -> ".join(zone.name for zone in path))