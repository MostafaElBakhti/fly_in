"""A simple Pygame display: one saved simulation turn at a time."""
import pygame

from map import Map


class InteractiveVisualizer:
    """Draw the map and use the arrow keys to browse drone positions."""

    def __init__(
        self, map_data: Map,
        history: list[dict[str, tuple[float, float]]],
    ) -> None:
        """Keep the saved turns and fit map coordinates into the window."""
        self.map_data = map_data
        self.history = history
        self.current_frame = 0
        zones = list(map_data.zone_by_name.values())
        self.center_x = (min(z.x for z in zones) + max(z.x for z in zones)) / 2
        self.center_y = (min(z.y for z in zones) + max(z.y for z in zones)) / 2
        width = max(z.x for z in zones) - min(z.x for z in zones)
        height = max(z.y for z in zones) - min(z.y for z in zones)
        self.scale = min(740 / max(width, 1), 380 / max(height, 1))

    def point(self, x: float, y: float) -> tuple[int, int]:
        """Convert map coordinates to pixels, with positive Y pointing up."""
        return (
            int(500 + (x - self.center_x) * self.scale),
            int(320 - (y - self.center_y) * self.scale),
        )

    def text(self, message: str, x: int, y: int) -> None:
        """Draw centered text with a background so edges remain readable."""
        label = self.font.render(message, True, "black", "white")
        self.screen.blit(label, label.get_rect(center=(x, y)))

    def draw(self) -> None:
        """Draw connections, colored zones, and drones for the current turn."""
        self.screen.fill("white")
        self.text(
            f"Turn {self.current_frame} / {len(self.history) - 1}", 500, 25,
        )
        self.text("Left: previous | Right / Space: next | Esc: quit", 500, 55)

        for connection in self.map_data.connections:
            a, b = connection.zone_a, connection.zone_b
            start, end = self.point(a.x, a.y), self.point(b.x, b.y)
            pygame.draw.line(self.screen, "gray", start, end, 2)
            x, y = self.point((a.x + b.x) / 2, (a.y + b.y) / 2)
            self.text(f"cap:{connection.max_link_capacity}", x, y - 14)

        for zone in self.map_data.zone_by_name.values():
            x, y = self.point(zone.x, zone.y)
            try:
                color = pygame.Color(zone.metadata.color)
            except ValueError:
                color = pygame.Color("lightgray")
            pygame.draw.circle(self.screen, color, (x, y), 18)
            pygame.draw.circle(self.screen, "black", (x, y), 18, 2)
            kind = zone.metadata.zone
            capacity = str(zone.metadata.max_drones)
            if zone is self.map_data.start_hub:
                kind, capacity = "START", "unlimited"
            elif zone is self.map_data.end_hub:
                kind, capacity = "END", "unlimited"
            self.text(zone.name, x, y - 48)
            self.text(f"{kind}", x, y - 19)
            self.text(f"max:{capacity}", x, y - 30)


        # Drones sharing a position use one badge, so they do not overlap.
        groups: dict[tuple[float, float], list[str]] = {}
        for name, position in self.history[self.current_frame].items():
            groups.setdefault(position, []).append(name)
        for (map_x, map_y), names in groups.items():
            x, y = self.point(map_x, map_y)
            pygame.draw.circle(self.screen, "purple", (x, y), 10)
            label = ", ".join(names[:3])
            if len(names) > 3:
                label += f" (+{len(names) - 3})"
            self.text(label, x, y + 30)
        self.text("Purple dots: drones (on a link while in transit)", 500, 600)
        pygame.display.flip()

    def show(self) -> None:
        """Handle keyboard events until the user closes the window."""
        try:
            pygame.display.init()
            pygame.font.init()
            self.screen = pygame.display.set_mode((1000, 640))
            pygame.display.set_caption("Fly-in")
            self.font = pygame.font.Font(None, 20)
            clock = pygame.time.Clock()
            running = True
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                        elif event.key == pygame.K_LEFT:
                            self.current_frame = max(0, self.current_frame - 1)
                        elif event.key in (pygame.K_RIGHT, pygame.K_SPACE):
                            self.current_frame = min(
                                len(self.history) - 1, self.current_frame + 1,
                            )
                self.draw()
                clock.tick(30)
        except pygame.error as error:
            raise ValueError(f"Cannot open Pygame display: {error}") from error
        finally:
            pygame.quit()
