class ZoneMetadata:
    """Store a zone's type, color, and drone capacity."""

    def __init__(
        self, zone: str = "normal", color: str = "none", max_drones: int = 1,
    ) -> None:
        """Set the zone type, display color, and capacity."""
        self.zone = zone
        self.color = color
        self.max_drones = max_drones


class Zone:
    """Represent a map zone and its neighbors."""

    def __init__(
        self, name: str, x: int, y: int, metadata: ZoneMetadata,
    ) -> None:
        """Create a zone with a name, coordinates, and metadata."""
        self.name = name
        self.x = x
        self.y = y
        self.metadata = metadata
        self.neighbors: dict[Zone, Connection] = {}


class Connection:
    """Represent a link between two zones with a capacity limit."""

    def __init__(
        self, zone_a: Zone, zone_b: Zone, max_link_capacity: int = 1,
    ) -> None:
        """Set the linked zones and maximum simultaneous crossings."""
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity


class Drone:
    """Track a drone's route, position, and movement state."""

    def __init__(
        self, id: int, current_zone: Zone, destination: Zone,
        path: list[Zone] | None = None,
    ) -> None:
        """Set the drone's ID, starting zone, destination, and route."""
        self.id = id
        self.current_zone = current_zone
        self.destination = destination
        self.path = path if path is not None else []
        self.position = 0
        self.finished = False
        self.transit_turns = 0
        self.pending_zone: Zone | None = None
        self.pending_connection: Connection | None = None

    @property
    def name(self) -> str:
        """Return the drone ID prefixed with D."""
        return f"D{self.id}"
