import math
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import numpy as np

class InteractiveVisualizer:

    def __init__(self, map_data, history):
        self.map_data = map_data
        self.history = history
        self.current_frame = 0
        self.drone_labels = []

        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.fig.subplots_adjust(bottom=0.15)

        self._draw_static_elements()

        self.drone_scatters = self.ax.scatter(
            [],
            [],
            color="#8e44ad",
            s=180,
            zorder=5,
            edgecolors="white",
            linewidth=1.5,
        )

        ax_prev = self.fig.add_axes([0.35, 0.03, 0.12, 0.05])
        ax_next = self.fig.add_axes([0.53, 0.03, 0.12, 0.05])

        self.btn_prev = Button(ax_prev, "Previous")
        self.btn_next = Button(ax_next, "Next")

        self.btn_prev.on_clicked(self.prev_turn)
        self.btn_next.on_clicked(self.next_turn)

        self.update(0)

    def _draw_static_elements(self):
        for conn in self.map_data.connections:
            x1, y1 = conn.zone_a.x, conn.zone_a.y
            x2, y2 = conn.zone_b.x, conn.zone_b.y
            self.ax.plot(
                [x1, x2],
                [y1, y2],
                color="#95a5a6",
                linestyle="--",
                linewidth=1.5,
                zorder=1,
            )

            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            self.ax.text(
                mid_x,
                mid_y,
                f"cap:{conn.max_link_capacity}",
                fontsize=8,
                color="#2c3e50",
                bbox=dict(
                    boxstyle="round,pad=0.2", fc="white", ec="#bdc3c7", alpha=0.9
                ),
                ha="center",
                va="center",
                zorder=2,
            )

        for zone in self.map_data.zone_by_name.values():
            if zone == self.map_data.start_hub:
                color, size, marker = "#2ecc71", 350, "s"
            elif zone == self.map_data.end_hub:
                color, size, marker = "#e74c3c", 350, "s"
            elif zone.metadata.zone == "priority":
                color, size, marker = "#f1c40f", 250, "o"
            elif zone.metadata.zone == "restricted":
                color, size, marker = "#e67e22", 250, "o"
            elif zone.metadata.zone == "blocked":
                color, size, marker = "#7f8c8d", 250, "X"
            else:
                color, size, marker = "#3498db", 250, "o"

            self.ax.scatter(
                zone.x,
                zone.y,
                color=color,
                s=size,
                marker=marker,
                zorder=3,
                edgecolors="black",
            )
            self.ax.annotate(
                f"{zone.name}\n[max:{zone.metadata.max_drones}]",
                (zone.x, zone.y),
                textcoords="offset points",
                xytext=(0, 15),
                ha="center",
                fontsize=8,
                fontweight="bold",
                zorder=4,
            )

        self.ax.set_xlabel("X Position")
        self.ax.set_ylabel("Y Position")
        self.ax.grid(True, linestyle=":", alpha=0.5)

    def update(self, frame_idx):
        for lbl in self.drone_labels:
            lbl.remove()
        self.drone_labels.clear()

        snapshot = self.history[frame_idx]
        turn = snapshot["turn"]
        positions = snapshot["positions"]

        zone_groups = {}
        for drone_name, zone in positions.items():
            zone_groups.setdefault(zone, []).append(drone_name)

        x_coords, y_coords = [], []

        for zone, drone_list in zone_groups.items():
            count = len(drone_list)
            for idx, drone_name in enumerate(drone_list):
                if count == 1:
                    offset_x, offset_y = 0, 0
                else:
                    angle = 2 * math.pi * idx / count
                    radius = 0.25
                    offset_x = radius * math.cos(angle)
                    offset_y = radius * math.sin(angle)

                dx = zone.x + offset_x
                dy = zone.y + offset_y
                x_coords.append(dx)
                y_coords.append(dy)

                lbl = self.ax.annotate(
                    drone_name,
                    (dx, dy),
                    fontsize=7,
                    fontweight="bold",
                    color="white",
                    ha="center",
                    va="center",
                    zorder=6,
                )
                self.drone_labels.append(lbl)

        if x_coords:
            self.drone_scatters.set_offsets(list(zip(x_coords, y_coords)))
        else:
            self.drone_scatters.set_offsets(np.empty((0, 2)))
        max_turns = self.history[-1]["turn"]
        self.ax.set_title(
            f"Interactive Drone Simulation — Turn {turn} / {max_turns}",
            fontsize=14,
            fontweight="bold",
        )
        self.fig.canvas.draw_idle()

    def next_turn(self, event):
        if self.current_frame < len(self.history) - 1:
            self.current_frame += 1
            self.update(self.current_frame)

    def prev_turn(self, event):
        if self.current_frame > 0:
            self.current_frame -= 1
            self.update(self.current_frame)

    def show(self):
        plt.show()
