from map import Map
from simulator import Simulator
import pygame  # type: ignore[reportMissingImports]


class Visualizer:
    def __init__(self, map_data: Map, simulation: Simulator):
        pygame.init()

        self.map = map_data
        self.simulation = simulation

        self.screen = pygame.display.set_mode(
            (2000, 1800),
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

        self.margin = 60
        self.update_layout()

    def update_layout(self):
        """Recompute scale and sizes from the current window size."""
        self.width, self.height = self.screen.get_size()

        usable_width = self.width - self.margin * 2
        usable_height = self.height - self.margin * 2

        scale_x = usable_width / max(1, self.map_width)
        scale_y = usable_height / max(1, self.map_height)
        self.scale = min(scale_x, scale_y)

        # Center the map in the window
        self.offset_x = (self.width - self.map_width * self.scale) / 2
        self.offset_y = (self.height - self.map_height * self.scale) / 2

        # Sizes come from the distance between two grid units,
        # so zones can never be bigger than the space between them
        self.zone_radius = max(2, min(20, int(self.scale * 0.35)))
        self.line_width = max(1, self.zone_radius // 4)

        self.font_size = max(12, min(20, self.zone_radius * 2))
        self.font = pygame.font.Font(None, self.font_size)
        self.show_labels = self.zone_radius >= 8

    def map_to_screen(self, x, y):
        screen_x = (x - self.min_x) * self.scale + self.offset_x
        screen_y = (y - self.min_y) * self.scale + self.offset_y

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
                connection_key = tuple(sorted((zone.name, neighbor.name)))

                if connection_key in drawn:
                    continue

                drawn.add(connection_key)

                start = self.map_to_screen(zone.x, zone.y)
                end = self.map_to_screen(neighbor.x, neighbor.y)

                pygame.draw.line(
                    self.screen,
                    (120, 120, 120),
                    start,
                    end,
                    self.line_width
                )

    def draw_zones(self):
        for zone in self.map.zone_by_name.values():
            x, y = self.map_to_screen(zone.x, zone.y)

            pygame.draw.circle(
                self.screen,
                self.get_zone_color(zone),
                (x, y),
                self.zone_radius
            )

            if not self.show_labels:
                continue

            text = self.font.render(zone.name, True, (255, 255, 255))
            text_rect = text.get_rect(
                center=(x, y - self.zone_radius - self.font_size // 2)
            )
            self.screen.blit(text, text_rect)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.update_layout()

            self.screen.fill((30, 30, 30))

            # Connections first, zones on top
            self.draw_connections()
            self.draw_zones()

            pygame.display.flip()

            self.clock.tick(60)

        pygame.quit()