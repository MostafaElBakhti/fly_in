class Zone:
    def __init__(self,name,x,y,metadata):
        self.name = name
        self.x = x
        self.y = y
        self.metadata = metadata

class ZoneMetadata:
    def __init__(self,zone="normal", color="none", max_drones=1):
        self.zone = zone
        self.color = color 
        self.max_drones = max_drones

class Connection:

    def __init__(self, zone_a, zone_b, max_link_capacity=1):
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity



class Drone:

    def __init__(self, id, current_zone, destination):
        self.id = id
        self.current_zone = current_zone
        self.destination = destination


# meta = Metadata(zone="normal" , color="green" , max_drones=3)
# print(meta.max_drones)
# zone_start = Zone("hub", 0, 0, meta)

# print(zone_start.metadata.color)

# zone_end = Zone("hub", 10, 10, "normal", 1)

# connection = Connection(zone_start, zone_end, 2)

# drone = Drone(1,zone_start,zone_end)

