import math
from typing import Any, Dict, List, Tuple
import pygame
from graph import Graph

# Palette
BG_COLOR = (24, 24, 37)            # Dark slate
EDGE_COLOR = (88, 91, 112)         # Gray
EDGE_RESTRICTED = (243, 139, 168)  # Red-pink
NODE_DEFAULT = (137, 180, 250)     # Soft blue
NODE_START = (166, 227, 161)       # Green
NODE_END = (243, 139, 168)         # Red
NODE_RESTRICTED = (250, 179, 135)  # Orange
DRONE_COLOR = (249, 226, 175)      # Gold
DRONE_TRANSIT = (250, 179, 135)    # Orange tint for restricted transit
TEXT_COLOR = (205, 214, 244)
BAR_BG = (17, 17, 27)


class Visualizer:
    def __init__(
        self,
        graph: Graph,
        history: List[Dict[str, Any]],
        width: int = 1440,
        height: int = 850,
    ) -> None:
        pygame.init()
        pygame.font.init()

        display_info = pygame.display.Info()
        if display_info.current_w > 0 and display_info.current_h > 0:
            width = min(width, int(display_info.current_w * 0.92))
            height = min(height, int(display_info.current_h * 0.88))

        self.graph = graph
        self.history = history
        self.width = width
        self.height = height
        self.is_fullscreen = False

        self.screen = pygame.display.set_mode(
            (self.width, self.height), pygame.RESIZABLE
        )
        pygame.display.set_caption("Fly-In Simulation Visualizer")

        num_nodes = max(len(self.graph.nodes), 1)
        if num_nodes > 20:
            self.node_radius = 14
            self.drone_radius = 8
            font_size = 11
        elif num_nodes > 10:
            self.node_radius = 18
            self.drone_radius = 10
            font_size = 12
        else:
            self.node_radius = 22
            self.drone_radius = 12
            font_size = 14

        self.font = pygame.font.SysFont("Arial", font_size, bold=True)
        self.drone_font = pygame.font.SysFont(
            "Arial", max(font_size - 2, 9), bold=True
        )
        self.title_font = pygame.font.SysFont("Arial", 18, bold=True)

        self.current_frame_idx = 0
        self.prev_frame_idx = 0
        self.anim_progress = 1.0
        self.anim_duration_ms = 450.0

        self.total_frames = len(history)
        self.auto_play = False
        self.clock = pygame.time.Clock()

        self.node_positions: Dict[str, Tuple[int, int]] = (
            self._compute_screen_coords()
        )

    def _compute_screen_coords(self) -> Dict[str, Tuple[int, int]]:
        """Maps arbitrary graph coordinates to current window pixel space."""
        margin_x, margin_y = 85, 65
        bottom_bar_height = 90
        usable_h = max(self.height - bottom_bar_height - (margin_y * 2), 100)
        usable_w = max(self.width - (margin_x * 2), 100)

        xs = [
            float(metadata.get("x", 0))
            for metadata in self.graph.nodes.values()
        ]
        ys = [
            float(metadata.get("y", 0))
            for metadata in self.graph.nodes.values()
        ]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        range_x = max(max_x - min_x, 1.0)
        range_y = max(max_y - min_y, 1.0)

        coords: Dict[str, Tuple[int, int]] = {}
        for name, data in self.graph.nodes.items():
            raw_x = float(data.get("x", 0))
            raw_y = float(data.get("y", 0))

            norm_x = (raw_x - min_x) / range_x
            norm_y = (raw_y - min_y) / range_y

            px = int(margin_x + norm_x * usable_w)
            py = int(
                self.height - bottom_bar_height - margin_y - norm_y * usable_h
            )
            coords[name] = (px, py)

        return coords

    def _step_to_frame(self, new_idx: int) -> None:
        if new_idx != self.current_frame_idx:
            self.prev_frame_idx = self.current_frame_idx
            self.current_frame_idx = new_idx
            self.anim_progress = 0.0

    def run(self) -> None:
        """Main Pygame event loop."""
        running = True
        auto_timer = 0

        while running:
            dt = self.clock.tick(60)
            auto_timer += dt

            if self.anim_progress < 1.0:
                self.anim_progress = min(
                    1.0, self.anim_progress + dt / self.anim_duration_ms
                )

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode(
                        (self.width, self.height), pygame.RESIZABLE
                    )
                    self.node_positions = self._compute_screen_coords()
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RIGHT, pygame.K_SPACE):
                        self._step_to_frame(
                            min(
                                self.current_frame_idx + 1,
                                self.total_frames - 1,
                            )
                        )
                    elif event.key == pygame.K_LEFT:
                        self._step_to_frame(max(self.current_frame_idx - 1, 0))
                    elif event.key == pygame.K_r:
                        self._step_to_frame(0)
                    elif event.key == pygame.K_a:
                        self.auto_play = not self.auto_play
                    elif event.key == pygame.K_f:
                        self.is_fullscreen = not self.is_fullscreen
                        if self.is_fullscreen:
                            self.screen = pygame.display.set_mode(
                                (0, 0), pygame.FULLSCREEN
                            )
                        else:
                            self.screen = pygame.display.set_mode(
                                (1440, 850), pygame.RESIZABLE
                            )
                        self.width, self.height = self.screen.get_size()
                        self.node_positions = self._compute_screen_coords()

            if self.auto_play and auto_timer > 500:
                auto_timer = 0
                if self.current_frame_idx < self.total_frames - 1:
                    self._step_to_frame(self.current_frame_idx + 1)
                else:
                    self.auto_play = False

            self._draw()
            pygame.display.flip()

        pygame.quit()

    def _draw(self) -> None:
        self.screen.fill(BG_COLOR)
        self._draw_edges()
        self._draw_nodes()
        self._draw_drones()
        self._draw_ui()

    def _draw_edges(self) -> None:
        drawn_edges = set()
        for u in self.graph.adj_list:
            for v, meta in self.graph.adj_list[u]:
                edge_id = tuple(sorted([u, v]))
                if edge_id in drawn_edges:
                    continue
                drawn_edges.add(edge_id)

                p1 = self.node_positions[u]
                p2 = self.node_positions[v]

                max_link = float(meta.get("max_link_capacity", float("inf")))
                color = (
                    EDGE_RESTRICTED
                    if max_link < float("inf")
                    else EDGE_COLOR
                )
                thickness = 3 if max_link < float("inf") else 2

                pygame.draw.line(self.screen, color, p1, p2, thickness)

    def _draw_nodes(self) -> None:
        color_map = {
            "green": (166, 227, 161),
            "red": (243, 139, 168),
            "yellow": (249, 226, 175),
            "gold": (255, 215, 0),
            "blue": (137, 180, 250),
            "orange": (250, 179, 135),
            "purple": (203, 166, 247),
            "violet": (180, 190, 254),
            "cyan": (148, 226, 213),
            "brown": (186, 135, 89),
            "maroon": (165, 66, 85),
            "darkred": (190, 40, 60),
            "crimson": (220, 20, 60),
            "black": (69, 71, 90),
            "rainbow": (245, 194, 231),
        }

        for name, (x, y) in self.node_positions.items():
            meta = self.graph.nodes[name]
            role = meta.get("zone", "normal")
            custom_color = str(meta.get("color", "")).lower()

            if custom_color in color_map:
                color = color_map[custom_color]
            elif role == "start_hub":
                color = NODE_START
            elif role == "end_hub":
                color = NODE_END
            elif role == "restricted":
                color = NODE_RESTRICTED
            elif role == "priority":
                color = (255, 215, 0)
            else:
                color = NODE_DEFAULT

            pygame.draw.circle(self.screen, color, (x, y), self.node_radius)
            pygame.draw.circle(
                self.screen, (255, 255, 255), (x, y), self.node_radius, 2
            )

            label_text = f"{name}"
            max_drones = meta.get("max_drones")
            if max_drones:
                label_text += f" ({max_drones})"

            label = self.font.render(label_text, True, TEXT_COLOR)
            self.screen.blit(
                label,
                (x - label.get_width() // 2, y + self.node_radius + 4),
            )

    def _get_drone_target_pos(
        self, data: Dict[str, Any]
    ) -> Tuple[int, int]:
        """Returns the zone coordinates for a drone in a given frame."""
        if data["is_in_transit"] and data["transit_target"]:
            return self.node_positions[str(data["transit_target"])]
        return self.node_positions[str(data["location"])]

    def _draw_drones(self) -> None:
        curr_frame = self.history[self.current_frame_idx]
        prev_frame = self.history[self.prev_frame_idx]

        # Group drones by their target anchor to calculate orbital offsets
        anchors: Dict[Tuple[int, int], List[int]] = {}
        for drone_id, data in curr_frame["drones"].items():
            pos = self._get_drone_target_pos(data)
            anchors.setdefault(pos, []).append(drone_id)

        target_coords: Dict[int, Tuple[int, int]] = {}
        for pos, ids in anchors.items():
            count = len(ids)
            orbit_radius = (
                self.node_radius * 0.75
                if count <= 6
                else self.node_radius * 1.15
            )
            for idx, drone_id in enumerate(ids):
                offset_x, offset_y = 0, 0
                if count > 1:
                    angle = (2 * math.pi / count) * idx
                    offset_x = int(math.cos(angle) * orbit_radius)
                    offset_y = int(math.sin(angle) * orbit_radius)
                target_coords[drone_id] = (
                    pos[0] + offset_x,
                    pos[1] + offset_y,
                )

        # Render with smooth interpolation from previous turn
        t = self.anim_progress
        for drone_id, curr_data in curr_frame["drones"].items():
            tx, ty = target_coords[drone_id]
            prev_data = prev_frame["drones"].get(drone_id, curr_data)
            px, py = self._get_drone_target_pos(prev_data)

            dx = int(px + (tx - px) * t)
            dy = int(py + (ty - py) * t)

            in_transit = curr_data["is_in_transit"]
            fill_color = DRONE_TRANSIT if in_transit else DRONE_COLOR

            pygame.draw.circle(
                self.screen, fill_color, (dx, dy), self.drone_radius
            )
            border_color = (255, 255, 255) if in_transit else (0, 0, 0)
            border_width = 2 if in_transit else 1
            pygame.draw.circle(
                self.screen,
                border_color,
                (dx, dy),
                self.drone_radius,
                border_width,
            )

            txt = self.drone_font.render(f"D{drone_id}", True, (0, 0, 0))
            self.screen.blit(
                txt,
                (dx - txt.get_width() // 2, dy - txt.get_height() // 2),
            )

    def _draw_ui(self) -> None:
        bar_rect = pygame.Rect(0, self.height - 90, self.width, 90)
        pygame.draw.rect(self.screen, BAR_BG, bar_rect)
        pygame.draw.line(
            self.screen,
            (69, 71, 90),
            (0, self.height - 90),
            (self.width, self.height - 90),
            2,
        )

        frame = self.history[self.current_frame_idx]
        max_turn = self.history[-1]["turn"]

        turn_text = f"Turn: {frame['turn']} / {max_turn}"
        state_text = "[PLAYING]" if self.auto_play else "[PAUSED]"
        t_surf = self.title_font.render(
            f"{turn_text}  {state_text}", True, TEXT_COLOR
        )
        self.screen.blit(t_surf, (20, self.height - 80))

        events = (
            " ".join(frame["events"])
            if frame["events"]
            else "None (Initial State)"
        )
        if len(events) > 95:
            events = events[:92] + "..."
        e_surf = self.font.render(f"Moves: {events}", True, (166, 227, 161))
        self.screen.blit(e_surf, (20, self.height - 45))

        controls = (
            "[SPACE/->] Next | [<-] Prev | [A] Auto | "
            "[R] Reset | [F] Fullscreen"
        )
        c_surf = self.font.render(controls, True, (147, 153, 178))
        self.screen.blit(
            c_surf, (self.width - c_surf.get_width() - 20, self.height - 45)
        )
