class ZoneMetadata:
    def __init__(self, zone="normal", color="none", max_drones=1):
        self.zone = zone
        self.color = color
        self.max_drones = max_drones


class Zone:
    def __init__(self, name, x, y, metadata):
        self.name = name
        self.x = x
        self.y = y
        self.metadata = metadata
        self.neighbors = {}


class Connection:
    def __init__(self, zone_a, zone_b, max_link_capacity=1):
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity


class Drone:
    def __init__(self, id, current_zone, destination, path=None):
        self.id = id
        self.current_zone = current_zone
        self.destination = destination
        self.path = path if path is not None else []
        self.position = 0
        self.transit_turns = 0
        self.finished = False

    @property
    def name(self):
        return f"D{self.id}"