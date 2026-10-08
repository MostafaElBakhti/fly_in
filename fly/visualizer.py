from map import Map
from simulator import Simulator
import pygame  # type: ignore[reportMissingImports]


class Visualizer:
    def __init__(self, map_data: Map, simulation: Simulator):
        pygame.init()

        self.map = map_data
        self.simulation = simulation

        self.width = 800
        self.height = 1200

        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.RESIZABLE
        )

        pygame.display.set_caption("Fly In")

        self.running = True
        self.progress = 0.0
        self.speed = 0.01
        self.turn = 0
        self.clock = pygame.time.Clock()

        zones = list(self.map.zone_by_name.values())

        self.min_x = min(zone.x for zone in zones)
        self.max_x = max(zone.x for zone in zones)
        self.min_y = min(zone.y for zone in zones)
        self.max_y = max(zone.y for zone in zones)

        self.map_width = self.max_x - self.min_x
        self.map_height = self.max_y - self.min_y

        self.margin = 100

        self.usable_width = self.width - self.margin * 2
        self.usable_height = self.height - self.margin * 2

        scale_x = self.usable_width / max(1, self.map_width)
        scale_y = self.usable_height / max(1, self.map_height)

        self.scale = min(scale_x, scale_y)

        self.visual_scale = self.scale / 50

        self.zone_radius = max(6, int(20 * self.visual_scale))
        self.line_width = max(1, int(3 * self.visual_scale))

        self.font_size = max(10, int(18 * self.visual_scale))
        self.font = pygame.font.Font(None, self.font_size)

    def map_to_screen(self, x, y):
        screen_x = (x - self.min_x) * self.scale + self.margin
        screen_y = (y - self.min_y) * self.scale + self.margin

        return int(screen_x), int(screen_y)

    def get_zone_color(self, zone):
        color = zone.metadata.color

        if not color:
            return pygame.Color(200, 200, 200)

        color = str(color).strip()

        # Allow colors like: bbb
        if len(color) == 3 and all(c in "0123456789abcdefABCDEF" for c in color):
            color = "#" + "".join(c * 2 for c in color)

        # Allow colors like: FF0000
        elif len(color) == 6 and all(c in "0123456789abcdefABCDEF" for c in color):
            color = "#" + color

        try:
            return pygame.Color(color)
        except ValueError:
            return pygame.Color(200, 200, 200)

    def draw_connections(self):
        drawn = set()

        for zone in self.map.zone_by_name.values():
            for neighbor in zone.neighbors:

                connection_key = tuple(
                    sorted((zone.name, neighbor.name))
                )

                if connection_key in drawn:
                    continue

                drawn.add(connection_key)

                start = self.map_to_screen(
                    zone.x,
                    zone.y
                )

                end = self.map_to_screen(
                    neighbor.x,
                    neighbor.y
                )

                pygame.draw.line(
                    self.screen,
                    (120, 120, 120),
                    start,
                    end,
                    self.line_width
                )

    def draw_zones(self):
        for zone in self.map.zone_by_name.values():
            x, y = self.map_to_screen(
                zone.x,
                zone.y
            )

            color = self.get_zone_color(zone)

            pygame.draw.circle(
                self.screen,
                color,
                (x, y),
                self.zone_radius
            )

            text = self.font.render(
                zone.name,
                True,
                (255, 255, 255)
            )

            text_rect = text.get_rect(
                center=(
                    x,
                    y - self.zone_radius - self.font_size
                )
            )

            self.screen.blit(
                text,
                text_rect
            )

    def run(self):
        while self.running:

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    self.running = False

            self.screen.fill((30, 30, 30))

            # Connections first
            self.draw_connections()

            # Zones on top
            self.draw_zones()

            pygame.display.flip()

            self.clock.tick(60)

        pygame.quit()


#     def draw(self):
#         self.screen.fill((30, 30, 30))

#         speed = 0.01
#         progress = 0.0
#         speed = 0.1

#         pygame.draw.line(
#             self.screen,
#             "white",
#             (200, 900),
#             (1200, 900),
#             10
#         )

#         pygame.draw.circle(
#             self.screen,
#             ("red"),
#             (200, 900),
#             100
#         )

#         pygame.draw.circle(
#             self.screen,
#             ("red"),
#             (1200, 900),
#             100
#         )

#         x = 200 + (1200 - 200 ) * self.progress
#         pygame.draw.circle(
#             self.screen,
#             ("green"),
#             (x, 900),
#             50
#         )

#         if self.progress <= 1.0:
#             self.progress += self.speed

#         pygame.display.flip()


#     def run(self):
#         while self.running:
#             for event in pygame.event.get():
#                 if event.type == pygame.QUIT:
#                     self.running = False
#             self.draw()
#             self.clock.tick(80)

#         pygame.quit()
