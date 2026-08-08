class Zone:
    def __init__(self,name,x,y,zone_type,max_drones):
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = zone_type
        self.max_drones = max_drones

zone = Zone("corridorA", 4, 3, "priority", 2)