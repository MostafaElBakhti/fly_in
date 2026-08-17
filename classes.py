class Zone:
    def __init__(self,name,x,y,metadata):
        self.name = name
        self.x = x
        self.y = y
        self.metadata = metadata
        self.neighbors = {}

class ZoneMetadata:
    def __init__(self,zone="normal", color="none", max_drones=1):
        self.zone = zone
        self.color = color 
        self.max_drones = max_drones

class Connection:

    def __init__(self, zone_a, zone_b, max_link_capacity=1):
        self.zone_a = zone_a  #//object
        self.zone_b = zone_b  #//object
        self.max_link_capacity = max_link_capacity



class Drone:

    def __init__(self, id, current_zone, destination):
        self.id = id
        self.current_zone = current_zone
        self.destination = destination

# meta1 = ZoneMetadata("normal","green",2)
# meta2 = ZoneMetadata("normal","green",2)

# zone1 = Zone("slak", 2,2,meta)
# zone2 = Zone("ino", 2,2,meta)

# connection = Connection(zone1,zone2,2)

# print(connection.zone_a.name)


