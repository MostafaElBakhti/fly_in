from map import Map
from simulator import Simulator
import pygame  # type: ignore[reportMissingImports]


class Visualizer:
    def __init__(self, map_data: Map, simulation: Simulator):
        pygame.init()

        self.map = map_data
        self.simulation = simulation

        self.height = 1200
        self.width = 800

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

        margin = 100

        self.usable_width = self.width - margin * 2
        self.usable_height = self.height - margin * 2

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            self.screen.fill((30, 30, 30))

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
