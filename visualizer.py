from collections import defaultdict
import math
import os

from classes import Zone
from map import Map
from simulator import Simulator

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import pygame  # noqa: E402


class Visualizer:
    """Display the map and replay recorded drone movements."""

    BACKGROUND = (10, 15, 28)
    SURFACE = (18, 26, 43)
    SURFACE_LIGHT = (25, 36, 57)
    BORDER = (49, 65, 89)
    TEXT = (235, 241, 250)
    MUTED = (145, 160, 183)
    ACCENT = (62, 207, 181)
    ZONE_RINGS = {
        "normal": (93, 114, 145),
        "priority": (69, 161, 255),
        "restricted": (255, 159, 67),
        "blocked": (235, 87, 87),
    }
    DRONE_COLORS = (
        (255, 190, 73),
        (71, 205, 255),
        (177, 121, 255),
        (255, 116, 151),
        (103, 224, 151),
        (255, 137, 74),
    )

    def __init__(self, map_data: Map, simulation: Simulator) -> None:
        """Set up the replay window for map_data and simulation."""
        pygame.init()

        self.map = map_data
        self.simulation = simulation

        self.screen = pygame.display.set_mode(
            (1280, 820),
            pygame.RESIZABLE
        )

        pygame.display.set_caption("Fly In | Mission Replay")

        self.running = True
        self.progress = 0.0
        self.speed = 1.0
        self.turn = 0
        self.paused = False
        self.clock = pygame.time.Clock()
        self.control_rects: dict[str, pygame.Rect] = {}

        zones = list(self.map.zone_by_name.values())

        self.min_x = min(zone.x for zone in zones)
        self.max_x = max(zone.x for zone in zones)
        self.min_y = min(zone.y for zone in zones)
        self.max_y = max(zone.y for zone in zones)

        self.map_width = self.max_x - self.min_x
        self.map_height = self.max_y - self.min_y

        self.update_layout()

    def update_layout(self) -> None:
        """Recompute scale and sizes from the current window size."""
        self.width, self.height = self.screen.get_size()

        outer = max(14, min(28, self.width // 55))
        header_height = 82
        footer_height = 86
        self.compact = self.width < 940
        panel_width = 0 if self.compact else min(292, self.width // 4)

        map_right = self.width - outer - panel_width
        if panel_width:
            map_right -= 18
        self.map_rect = pygame.Rect(
            outer,
            header_height,
            max(100, map_right - outer),
            max(100, self.height - header_height - footer_height),
        )
        self.side_rect = pygame.Rect(
            self.width - outer - panel_width,
            header_height,
            panel_width,
            self.map_rect.height,
        )
        self.footer_rect = pygame.Rect(
            outer,
            self.height - footer_height + 12,
            self.width - outer * 2,
            footer_height - 24,
        )

        padding = max(52, min(90, self.map_rect.width // 8))
        usable_width = max(1, self.map_rect.width - padding * 2)
        usable_height = max(1, self.map_rect.height - padding * 2)

        scale_x = usable_width / max(1, self.map_width)
        scale_y = usable_height / max(1, self.map_height)
        self.scale = min(scale_x, scale_y)

        self.offset_x = self.map_rect.x + (
            self.map_rect.width - self.map_width * self.scale
        ) / 2
        self.offset_y = self.map_rect.y + (
            self.map_rect.height - self.map_height * self.scale
        ) / 2

        self.zone_radius = max(15, min(28, int(self.scale * 0.16)))
        self.line_width = max(2, min(5, self.zone_radius // 6))

        self.title_font = pygame.font.SysFont("arial", 26, bold=True)
        self.heading_font = pygame.font.SysFont("arial", 17, bold=True)
        self.body_font = pygame.font.SysFont("arial", 14)
        self.small_font = pygame.font.SysFont("arial", 12)
        self.drone_font = pygame.font.SysFont("arial", 11, bold=True)

    def map_to_screen(self, x: float, y: float) -> tuple[int, int]:
        """Return screen pixel coordinates for map coordinates x and y."""
        screen_x = (x - self.min_x) * self.scale + self.offset_x
        screen_y = (y - self.min_y) * self.scale + self.offset_y

        return int(screen_x), int(screen_y)

    def get_zone_color(self, zone: Zone) -> pygame.Color:
        """Return a safe display color for a zone."""
        try:
            color = pygame.Color(zone.metadata.color)
            if zone.metadata.color.lower() == "none":
                raise ValueError
            return color
        except ValueError:
            return pygame.Color(104, 123, 151)

    def draw_panel(
        self,
        rect: pygame.Rect,
        color: tuple[int, int, int] | None = None,
        radius: int = 18,
    ) -> None:
        """Draw a bordered rounded panel."""
        pygame.draw.rect(
            self.screen, color or self.SURFACE, rect,
            border_radius=radius,
        )
        pygame.draw.rect(
            self.screen, self.BORDER, rect, 1, border_radius=radius,
        )

    def blit_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        position: tuple[int, int],
        anchor: str = "topleft",
    ) -> pygame.Rect:
        """Render text with a named rect anchor and return its rect."""
        image = font.render(text, True, color)
        rect = image.get_rect()
        setattr(rect, anchor, position)
        self.screen.blit(image, rect)
        return rect

    def draw_background(self) -> None:
        """Draw the page background and a subtle map grid."""
        self.screen.fill(self.BACKGROUND)
        self.draw_panel(self.map_rect)
        grid_color = (23, 34, 53)
        spacing = 44
        for x in range(
            self.map_rect.left + spacing,
            self.map_rect.right,
            spacing,
        ):
            pygame.draw.line(
                self.screen,
                grid_color,
                (x, self.map_rect.top + 1),
                (x, self.map_rect.bottom - 1),
            )
        for y in range(
            self.map_rect.top + spacing,
            self.map_rect.bottom,
            spacing,
        ):
            pygame.draw.line(
                self.screen,
                grid_color,
                (self.map_rect.left + 1, y),
                (self.map_rect.right - 1, y),
            )

    def draw_header(self) -> None:
        """Draw the title and current mission state."""
        self.blit_text("FLY IN", self.title_font, self.TEXT, (28, 20))
        self.blit_text(
            "Mission control / route replay",
            self.body_font,
            self.MUTED,
            (29, 51),
        )
        status = "PAUSED" if self.paused else "IN FLIGHT"
        if self.turn >= len(self.simulation.history) - 1:
            status = "MISSION COMPLETE"
        status_width = self.body_font.size(status)[0] + 42
        status_rect = pygame.Rect(
            self.width - status_width - 28, 25, status_width, 32,
        )
        pygame.draw.rect(
            self.screen, (21, 58, 58), status_rect, border_radius=16,
        )
        pygame.draw.circle(
            self.screen,
            self.ACCENT,
            (status_rect.x + 16, status_rect.centery),
            4,
        )
        self.blit_text(
            status,
            self.small_font,
            self.TEXT,
            (status_rect.x + 27, status_rect.centery),
            "midleft",
        )

    def draw_connections(self) -> None:
        """Draw each connection once, including capacity badges."""
        for connection in self.map.connections:
            start = self.map_to_screen(
                connection.zone_a.x, connection.zone_a.y,
            )
            end = self.map_to_screen(
                connection.zone_b.x, connection.zone_b.y,
            )
            pygame.draw.line(
                self.screen,
                (27, 39, 61),
                start,
                end,
                self.line_width + 5,
            )
            pygame.draw.line(
                self.screen,
                (75, 96, 125),
                start,
                end,
                self.line_width,
            )
            if connection.max_link_capacity > 1:
                midpoint = (
                    (start[0] + end[0]) // 2,
                    (start[1] + end[1]) // 2,
                )
                badge = pygame.Rect(0, 0, 28, 20)
                badge.center = midpoint
                pygame.draw.rect(
                    self.screen,
                    self.SURFACE_LIGHT,
                    badge,
                    border_radius=10,
                )
                self.blit_text(
                    f"x{connection.max_link_capacity}",
                    self.small_font,
                    self.TEXT,
                    badge.center,
                    "center",
                )

    def draw_zones(self) -> None:
        """Draw zones with type rings, readable labels, and hub tags."""
        for zone in self.map.zone_by_name.values():
            x, y = self.map_to_screen(zone.x, zone.y)
            zone_type = zone.metadata.zone
            ring = self.ZONE_RINGS.get(zone_type, self.ZONE_RINGS["normal"])
            is_hub = zone in (self.map.start_hub, self.map.end_hub)

            pygame.draw.circle(
                self.screen,
                (7, 12, 23),
                (x + 3, y + 5),
                self.zone_radius + 5,
            )
            pygame.draw.circle(
                self.screen,
                self.ACCENT if is_hub else ring,
                (x, y),
                self.zone_radius + 4,
            )
            pygame.draw.circle(
                self.screen,
                self.get_zone_color(zone),
                (x, y),
                self.zone_radius,
            )
            pygame.draw.circle(
                self.screen,
                (230, 238, 248),
                (x - self.zone_radius // 3, y - self.zone_radius // 3),
                max(2, self.zone_radius // 7),
            )
            if zone_type == "blocked":
                offset = int(self.zone_radius * 0.7)
                pygame.draw.line(
                    self.screen,
                    (255, 235, 235),
                    (x - offset, y - offset),
                    (x + offset, y + offset),
                    3,
                )

            text = self.body_font.render(zone.name, True, self.TEXT)
            text_rect = text.get_rect(
                center=(x, y - self.zone_radius - 18),
            )
            label_rect = text_rect.inflate(16, 8)
            pygame.draw.rect(
                self.screen,
                (12, 19, 32),
                label_rect,
                border_radius=7,
            )
            self.screen.blit(text, text_rect)
            if is_hub:
                tag = "START" if zone is self.map.start_hub else "GOAL"
                self.blit_text(
                    tag,
                    self.small_font,
                    self.MUTED,
                    (x, y + self.zone_radius + 12),
                    "midtop",
                )

    def update_animation(self, dt: float) -> None:
        """Advance the replay at the selected playback speed."""
        history = self.simulation.history

        if not history or self.turn >= len(history) - 1:
            self.paused = True
            return

        self.progress += dt * self.speed

        if self.progress >= 1.0:
            self.progress = 0.0
            self.turn += 1

            if self.turn >= len(history) - 1:
                self.paused = True

    def draw_drones(self) -> None:
        """Draw drones between the current and next saved positions."""
        history = self.simulation.history

        if not history:
            return

        current = history[self.turn]
        following = history[min(self.turn + 1, len(history) - 1)]
        eased = self.progress * self.progress * (3.0 - 2.0 * self.progress)
        grouped: dict[tuple[int, int], list[str]] = defaultdict(list)

        for name, (start_x, start_y) in current.items():
            end_x, end_y = following.get(name, (start_x, start_y))
            x = start_x + (end_x - start_x) * eased
            y = start_y + (end_y - start_y) * eased
            position = self.map_to_screen(x, y)
            grouped[position].append(name)

        radius = max(10, min(15, self.zone_radius // 2 + 2))
        for base_position, drones in grouped.items():
            count = len(drones)
            orbit = 0 if count == 1 else radius + 6
            for index, name in enumerate(drones):
                angle = -math.pi / 2 + (2 * math.pi * index / count)
                position = (
                    int(base_position[0] + math.cos(angle) * orbit),
                    int(base_position[1] + math.sin(angle) * orbit),
                )
                drone_id = int(name[1:])
                color = self.DRONE_COLORS[
                    (drone_id - 1) % len(self.DRONE_COLORS)
                ]
                pygame.draw.circle(
                    self.screen, (5, 9, 17), position, radius + 4,
                )
                pygame.draw.circle(self.screen, color, position, radius)
                pygame.draw.circle(
                    self.screen, (255, 255, 255), position, radius, 1,
                )
                self.blit_text(
                    str(drone_id),
                    self.drone_font,
                    (16, 23, 35),
                    position,
                    "center",
                )

    def delivered_count(self) -> int:
        """Return the number of drones visible at the destination."""
        history = self.simulation.history
        end = self.map.end_hub
        if not history or end is None:
            return 0
        target = (float(end.x), float(end.y))
        return sum(
            position == target
            for position in history[self.turn].values()
        )

    def draw_stat(
        self,
        label: str,
        value: str,
        x: int,
        y: int,
        width: int,
    ) -> None:
        """Draw one compact statistic card."""
        rect = pygame.Rect(x, y, width, 58)
        pygame.draw.rect(
            self.screen, self.SURFACE_LIGHT, rect, border_radius=12,
        )
        self.blit_text(
            label.upper(), self.small_font, self.MUTED, (x + 12, y + 9),
        )
        self.blit_text(
            value, self.heading_font, self.TEXT, (x + 12, y + 29),
        )

    def draw_sidebar(self) -> None:
        """Draw mission statistics, legend, and keyboard help."""
        if self.compact:
            return
        self.draw_panel(self.side_rect)
        x = self.side_rect.x + 18
        width = self.side_rect.width - 36
        self.blit_text(
            "MISSION OVERVIEW",
            self.heading_font,
            self.TEXT,
            (x, self.side_rect.y + 20),
        )
        total_turns = max(0, len(self.simulation.history) - 1)
        stat_width = (width - 10) // 2
        stat_y = self.side_rect.y + 58
        self.draw_stat(
            "Turn", f"{self.turn} / {total_turns}",
            x, stat_y, stat_width,
        )
        self.draw_stat(
            "Delivered",
            f"{self.delivered_count()} / {self.map.nb_drones}",
            x + stat_width + 10,
            stat_y,
            stat_width,
        )
        self.draw_stat(
            "Zones", str(len(self.map.zone_by_name)),
            x, stat_y + 68, stat_width,
        )
        self.draw_stat(
            "Routes", str(len(self.simulation.paths)),
            x + stat_width + 10,
            stat_y + 68,
            stat_width,
        )

        legend_y = stat_y + 158
        self.blit_text(
            "ZONE TYPES", self.heading_font, self.TEXT, (x, legend_y),
        )
        zone_types = ("normal", "priority", "restricted", "blocked")
        for index, zone_type in enumerate(zone_types):
            item_y = legend_y + 38 + index * 34
            pygame.draw.circle(
                self.screen,
                self.ZONE_RINGS[zone_type],
                (x + 8, item_y + 7),
                7,
            )
            self.blit_text(
                zone_type.capitalize(),
                self.body_font,
                self.MUTED,
                (x + 25, item_y),
            )

        help_y = self.side_rect.bottom - 113
        pygame.draw.line(
            self.screen,
            self.BORDER,
            (x, help_y),
            (x + width, help_y),
        )
        self.blit_text(
            "KEYBOARD", self.small_font, self.MUTED, (x, help_y + 18),
        )
        self.blit_text(
            "Space  Play / pause",
            self.body_font,
            self.TEXT,
            (x, help_y + 42),
        )
        self.blit_text(
            "Arrows  Step     R  Restart",
            self.body_font,
            self.TEXT,
            (x, help_y + 68),
        )

    def draw_button(
        self,
        name: str,
        label: str,
        center: tuple[int, int],
        width: int = 50,
        active: bool = False,
    ) -> None:
        """Draw and register a footer control button."""
        rect = pygame.Rect(0, 0, width, 38)
        rect.center = center
        color = self.ACCENT if active else self.SURFACE_LIGHT
        text_color = (9, 25, 28) if active else self.TEXT
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        if not active:
            pygame.draw.rect(
                self.screen, self.BORDER, rect, 1, border_radius=10,
            )
        self.blit_text(
            label, self.heading_font, text_color, rect.center, "center",
        )
        self.control_rects[name] = rect

    def draw_footer(self) -> None:
        """Draw the timeline and playback controls."""
        self.draw_panel(self.footer_rect)
        self.control_rects.clear()
        center_y = self.footer_rect.centery
        start_x = self.footer_rect.x + 38
        self.draw_button("previous", "<", (start_x, center_y))
        self.draw_button(
            "play",
            "PLAY" if self.paused else "PAUSE",
            (start_x + 73, center_y),
            78,
            not self.paused,
        )
        self.draw_button("next", ">", (start_x + 145, center_y))
        self.draw_button("reset", "RESET", (start_x + 220, center_y), 68)

        speed_x = self.footer_rect.right - 156
        self.draw_button("slower", "-", (speed_x, center_y), 38)
        self.blit_text(
            f"{self.speed:g}x",
            self.body_font,
            self.TEXT,
            (speed_x + 48, center_y),
            "midleft",
        )
        self.draw_button("faster", "+", (speed_x + 118, center_y), 38)

        timeline_left = start_x + 270
        timeline_right = speed_x - 30
        if timeline_right - timeline_left > 80:
            pygame.draw.line(
                self.screen,
                self.BORDER,
                (timeline_left, center_y),
                (timeline_right, center_y),
                5,
            )
            total = max(1, len(self.simulation.history) - 1)
            completion = min(1.0, (self.turn + self.progress) / total)
            progress_right = int(
                timeline_left
                + (timeline_right - timeline_left) * completion
            )
            pygame.draw.line(
                self.screen,
                self.ACCENT,
                (timeline_left, center_y),
                (progress_right, center_y),
                5,
            )
            pygame.draw.circle(
                self.screen, self.TEXT, (progress_right, center_y), 7,
            )

    def draw_tooltip(self) -> None:
        """Show zone metadata when the pointer is near a zone."""
        mouse = pygame.mouse.get_pos()
        hovered = None
        for zone in self.map.zone_by_name.values():
            point = self.map_to_screen(zone.x, zone.y)
            if math.dist(mouse, point) <= self.zone_radius + 8:
                hovered = zone
                break
        if hovered is None:
            return
        text = (
            f"{hovered.name}  |  {hovered.metadata.zone.capitalize()}"
            f"  |  Capacity {hovered.metadata.max_drones}"
        )
        text_width = self.body_font.size(text)[0]
        rect = pygame.Rect(mouse[0] + 16, mouse[1] + 18, text_width + 24, 38)
        if rect.right > self.width - 10:
            rect.right = mouse[0] - 12
        if rect.bottom > self.height - 10:
            rect.bottom = mouse[1] - 12
        pygame.draw.rect(self.screen, (7, 12, 22), rect, border_radius=9)
        pygame.draw.rect(
            self.screen, self.BORDER, rect, 1, border_radius=9,
        )
        self.blit_text(
            text, self.body_font, self.TEXT, rect.center, "center",
        )

    def reset(self) -> None:
        """Return to turn zero and pause."""
        self.turn = 0
        self.progress = 0.0
        self.paused = True

    def toggle_playback(self) -> None:
        """Toggle playback, restarting after a completed replay."""
        last_turn = max(0, len(self.simulation.history) - 1)
        if self.turn >= last_turn:
            self.turn = 0
            self.progress = 0.0
        self.paused = not self.paused

    def step(self, direction: int) -> None:
        """Pause and move by one recorded turn."""
        last_turn = max(0, len(self.simulation.history) - 1)
        self.turn = max(0, min(last_turn, self.turn + direction))
        self.progress = 0.0
        self.paused = True

    def change_speed(self, faster: bool) -> None:
        """Move between the supported playback rates."""
        speeds = (0.5, 1.0, 1.5, 2.0, 3.0)
        current = min(
            range(len(speeds)),
            key=lambda index: abs(speeds[index] - self.speed),
        )
        change = 1 if faster else -1
        index = max(0, min(len(speeds) - 1, current + change))
        self.speed = speeds[index]

    def handle_click(self, position: tuple[int, int]) -> None:
        """Run the action associated with a clicked footer control."""
        action = next(
            (
                name
                for name, rect in self.control_rects.items()
                if rect.collidepoint(position)
            ),
            None,
        )
        if action == "play":
            self.toggle_playback()
        elif action == "previous":
            self.step(-1)
        elif action == "next":
            self.step(1)
        elif action == "reset":
            self.reset()
        elif action == "slower":
            self.change_speed(False)
        elif action == "faster":
            self.change_speed(True)

    def run(self) -> None:
        """Play the simulation and handle window and input events."""
        while self.running:
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.VIDEORESIZE:
                    self.update_layout()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_click(event.pos)

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.toggle_playback()
                    elif event.key == pygame.K_RIGHT:
                        self.step(1)
                    elif event.key == pygame.K_LEFT:
                        self.step(-1)
                    elif event.key == pygame.K_r:
                        self.reset()
                    elif event.key in (
                        pygame.K_PLUS,
                        pygame.K_EQUALS,
                        pygame.K_KP_PLUS,
                    ):
                        self.change_speed(True)
                    elif event.key in (
                        pygame.K_MINUS,
                        pygame.K_KP_MINUS,
                    ):
                        self.change_speed(False)

            if not self.running:
                break

            if not self.paused:
                self.update_animation(dt)

            self.draw_background()
            self.draw_header()
            self.draw_connections()
            self.draw_zones()
            self.draw_drones()
            self.draw_sidebar()
            self.draw_footer()
            self.draw_tooltip()

            pygame.display.flip()

        pygame.quit()
