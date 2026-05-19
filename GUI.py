import pygame
import math


NODE_TYPE_COLORS: dict[str, tuple[int, int, int]] = {
    "center": (11, 133, 120),
    "residential": (8, 196, 24),
    "market": (12, 96, 166),
    "industrial": (209, 151, 17),
    "out": (150, 150, 150),
    "junction": (100, 100, 100)
}

# Registry of available connection types for the UI.
# Add new types here; the panel will pick them up automatically.
CONNECTION_TYPES: list[dict] = [
    {"name": "Highway", "color": (80, 80, 80),    "dash": False},
    {"name": "Passenger Rail",  "color": (173, 9, 232),  "dash": False},
    {"name": "Freight Rail",    "color": (122, 82, 13), "dash": False},
]

CONNECTION_TYPE_STYLES: dict[str, dict] = {t["name"]: t for t in CONNECTION_TYPES}

BASE_NODE_RADIUS      = 10
NODE_RADIUS_PER_LEVEL = 3
BASE_CONNECTION_WIDTH      = 2
CONNECTION_WIDTH_PER_LEVEL = 1
CONNECTION_OFFSET = 6

# Zoom settings
ZOOM_MIN = 0.3
ZOOM_MAX = 4.0
ZOOM_STEP = 0.1

# Panel sizing — expressed as fractions of window width so they scale.
PANEL_WIDTH_FRACTION  = 0.16   # panel takes ~16 % of window width
PANEL_WIDTH_MIN       = 160
PANEL_WIDTH_MAX       = 280

# Colors (RGB)
C_BG         = (230, 230, 230)
C_PANEL_BG   = (245, 245, 245)
C_PANEL_EDGE = (180, 180, 180)
C_BTN        = (210, 210, 210)
C_BTN_ACTIVE = (70, 130, 220)
C_BTN_TEXT   = (30, 30, 30)
C_BTN_TEXT_A = (255, 255, 255)
C_LEVEL_BG   = (220, 220, 220)
C_LEVEL_TEXT = (30, 30, 30)
C_STATUS_OK  = (200, 230, 200)
C_STATUS_WAIT= (255, 240, 180)
C_STATUS_TEXT= (30, 30, 30)
C_SELECT_RING= (255, 215, 0)
C_PREVIEW    = (150, 150, 150)
C_HINT       = (120, 120, 120)

# Playback control colors
C_PAUSE_BTN        = (200, 80, 60)   # red-ish when playing (click to pause)
C_PAUSE_BTN_PAUSED = (11, 133, 120)  # teal when paused (click to play)
C_SPEED_BTN        = (70, 130, 220)
C_SPEED_BTN_MAX    = (209, 151, 17)  # amber at top speed

# Title screen colors
C_TITLE_BG        = (15, 20, 30)
C_TITLE_ACCENT     = (11, 133, 120)
C_TITLE_ACCENT2    = (70, 130, 220)
C_TITLE_TEXT       = (220, 225, 235)
C_TITLE_SUBTEXT    = (140, 150, 165)
C_START_BTN        = (11, 133, 120)
C_START_BTN_HOVER  = (14, 170, 153)
C_START_BTN_TEXT   = (255, 255, 255)

SPEED_STEPS = [1, 2, 3, 4]


# ---------------------------------------------------------------------------
# Responsive helpers
# ---------------------------------------------------------------------------

def _scale(reference: float, surface: pygame.Surface, axis: str = "h") -> int:
    if axis == "h":
        factor = surface.get_height() / 900
    else:
        factor = surface.get_width() / 1200
    return max(1, int(reference * factor))


def _font(size_ref: int, surface: pygame.Surface, bold: bool = False) -> pygame.font.Font:
    size = _scale(size_ref - 6, surface)
    return pygame.font.Font(pygame.font.get_default_font(), size)


class TitleScreen:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.started = False
        self._btn_rect: pygame.Rect | None = None
        self._tick = 0

        self._deco_offsets = [
            (0, 0), (0, -1.0), (0, 1.0),
            (-1.0,  0), (1.0,  0), (0.707,  0.707),
            (-0.707, 0.707), (-0.707, -0.707), (0.707, -0.707)
        ]
        self._deco_conns = [
            (0, 1), (0, 2), (0, 3), (0, 4),
            (0, 5), (0, 6), (0, 7), (0, 8),
            (3, 5), (1, 6), (2, 4), (3, 6),
            (4, 5), (4, 8), (1, 7), (7, 3),
            (1, 8), (2, 6), (2, 5), (2, 8),
            (7, 4)
        ]

    def handle_event(self, event) -> bool:
        if self.started:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._btn_rect and self._btn_rect.collidepoint(event.pos):
                self.started = True
                return True

        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.started = True
            return True

        return False

    def update(self) -> bool:
        if self.started:
            return True

        self._tick += 1
        sw, sh = self.surface.get_size()
        cx, cy = sw // 2, sh // 2

        self.surface.fill(C_TITLE_BG)

        net_cy  = cy - _scale(80, self.surface)
        text_cy = cy + _scale(40, self.surface)

        self._draw_decorative_network(cx, net_cy)
        self._draw_title(cx, text_cy)
        self._draw_start_button(cx, text_cy)
        self._draw_hint(cx, sh)

        return False

    def _to_screen(self, offset, radius, cx, cy):
        return (int(offset[0] * radius + cx), int(offset[1] * radius + cy))

    def _draw_decorative_network(self, cx, cy):
        orbit_r = _scale(300, self.surface)
        screen_nodes = [self._to_screen(p, orbit_r, cx, cy) for p in self._deco_offsets]

        for a, b in self._deco_conns:
            pygame.draw.line(self.surface, (30, 50, 70),
                             screen_nodes[a], screen_nodes[b], 2)

        colors = [
            NODE_TYPE_COLORS["center"],
            NODE_TYPE_COLORS["residential"],
            NODE_TYPE_COLORS["market"],
            NODE_TYPE_COLORS["residential"],
            NODE_TYPE_COLORS["market"],
            NODE_TYPE_COLORS["industrial"],
            NODE_TYPE_COLORS["residential"],
            NODE_TYPE_COLORS["market"],
            NODE_TYPE_COLORS["industrial"],
        ]
        node_r = max(5, _scale(8, self.surface))
        for i, sp in enumerate(screen_nodes):
            color = colors[i % len(colors)]
            pygame.draw.circle(self.surface, color, sp, node_r)
            pygame.draw.circle(self.surface, color, sp, node_r + max(2, node_r // 2), 1)

    def _draw_title(self, cx, cy):
        font_title = _font(90, self.surface, bold=True)
        font_sub   = _font(40, self.surface)

        title_surf = font_title.render("Mini Transit", True, C_TITLE_TEXT)
        title_rect = title_surf.get_rect(center=(cx, cy - _scale(10, self.surface)))
        self.surface.blit(title_surf, title_rect)

        uw = title_rect.width + _scale(20, self.surface)
        ux = cx - uw // 2
        uy = title_rect.bottom + _scale(6, self.surface)
        pygame.draw.line(self.surface, C_TITLE_ACCENT, (ux, uy), (ux + uw, uy), 3)

        sub_surf = font_sub.render("An Educational Transit Building Game", True, C_TITLE_SUBTEXT)
        sub_rect = sub_surf.get_rect(center=(cx, uy + _scale(26, self.surface)))
        self.surface.blit(sub_surf, sub_rect)

    def _draw_start_button(self, cx, cy):
        font_btn = _font(26, self.surface, bold=True)
        mouse_pos = pygame.mouse.get_pos()

        bw = _scale(180, self.surface, "w")
        bh = _scale(48, self.surface)
        btn_top = cy + _scale(80, self.surface)
        btn_rect = pygame.Rect(cx - bw // 2, btn_top, bw, bh)
        self._btn_rect = btn_rect

        hovered = btn_rect.collidepoint(mouse_pos)
        color = C_START_BTN_HOVER if hovered else C_START_BTN

        pygame.draw.rect(self.surface, color, btn_rect, border_radius=8)
        pygame.draw.rect(self.surface, C_TITLE_ACCENT2, btn_rect, width=1, border_radius=8)

        label = font_btn.render("START", True, C_START_BTN_TEXT)
        self.surface.blit(label, label.get_rect(center=btn_rect.center))

    def _draw_hint(self, cx, sh):
        font_hint = _font(16, self.surface)
        hint = font_hint.render("or press  Enter / Space", True, C_TITLE_SUBTEXT)
        self.surface.blit(hint, hint.get_rect(center=(cx, sh - _scale(28, self.surface))))


class GUI:
    NEED_DISPLAY_NAMES: dict[str, str] = {
        "c": "City Center",
        "r": "Residential",
        "m": "Commercial",
        "i": "Industrial",
        "o": "Out of City",
    }

    def __init__(self, surface: pygame.Surface):
        self.surface = surface

        # Interaction state
        self.selected_node   = None
        self.active_type_idx = 0
        self.active_level    = 1
        self.hovered_node    = None
        self.hovered_conn    = None
        self._type_btn_rects: list[pygame.Rect] = []
        self.game_speed = 1
        self.paused = True
        self.speed_changed = False  # set to True when speed cycles; game loop should reset its skip counter and clear this

        # Zoom and pan state
        self.zoom = 1.0
        self._pan_offset = [0.0, 0.0]  # world-space pan in unscaled units

        # Playback button rects (populated each frame by _draw_panel)
        self._pause_btn_rect: pygame.Rect | None = None
        self._speed_btn_rect: pygame.Rect | None = None

        # Level button rects (populated each frame by _draw_panel)
        self._level_minus_rect: pygame.Rect | None = None
        self._level_plus_rect:  pygame.Rect | None = None

        self._hovered_type_idx: int | None = None

        # Flash / insufficient-funds feedback
        import time as _time
        self._flash_message: str | None = None
        self._flash_expires: float = 0.0
        self._flash_shake_node: int | None = None
        self._flash_shake_start: float = 0.0
        self._time = _time

    # ------------------------------------------------------------------
    # Responsive layout helpers
    # ------------------------------------------------------------------

    def _panel_width(self) -> int:
        sw = self.surface.get_width()
        return max(PANEL_WIDTH_MIN, min(PANEL_WIDTH_MAX, int(sw * PANEL_WIDTH_FRACTION)))

    def _panel_padding(self) -> int:
        return max(8, _scale(14, self.surface))

    def _btn_height(self) -> int:
        return max(28, _scale(36, self.surface))

    def _btn_gap(self) -> int:
        return max(4, _scale(8, self.surface))

    def _level_box_h(self) -> int:
        return max(36, _scale(48, self.surface))

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def canvas_rect(self) -> pygame.Rect:
        w = self.surface.get_width()
        h = self.surface.get_height()
        return pygame.Rect(0, 0, w - self._panel_width(), h)

    def handle_event(self, event, nodes, on_connect, on_upgrade_connection):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            # ── Playback controls ──────────────────────────────────────
            if self._pause_btn_rect and self._pause_btn_rect.collidepoint(pos):
                self.paused = not self.paused
                return True

            if self._speed_btn_rect and self._speed_btn_rect.collidepoint(pos):
                current_idx = SPEED_STEPS.index(self.game_speed) if self.game_speed in SPEED_STEPS else 0
                self.game_speed = SPEED_STEPS[(current_idx + 1) % len(SPEED_STEPS)]
                self.speed_changed = True
                return True

            # ── Level buttons ──────────────────────────────────────────
            if self._level_minus_rect and self._level_minus_rect.collidepoint(pos):
                self.active_level = max(1, self.active_level - 1)
                return True

            if self._level_plus_rect and self._level_plus_rect.collidepoint(pos):
                self.active_level = min(10, self.active_level + 1)
                return True

            # ── Connection type buttons ────────────────────────────────
            for i, rect in enumerate(self._type_btn_rects):
                if rect.collidepoint(pos):
                    self.active_type_idx = i
                    return True

            # Any remaining click inside the panel is consumed here so it
            # never bleeds through to canvas / node logic below.
            if not self.canvas_rect().collidepoint(pos):
                return True

            if self.canvas_rect().collidepoint(pos):
                clicked = self._node_at(nodes, pos)  # now returns an index
                if clicked is None:
                    self.selected_node = None
                elif self.selected_node is None:
                    self.selected_node = clicked
                elif clicked == self.selected_node:  # was `is`, now `==`
                    self.selected_node = None
                else:
                    type_name = CONNECTION_TYPES[self.active_type_idx]["name"]
                    success = on_connect(nodes[self.selected_node], nodes[clicked], type_name, self.active_level)
                    if not success:
                        ct_name = CONNECTION_TYPES[self.active_type_idx]["name"]
                        dx = nodes[clicked].position[0] - nodes[self.selected_node].position[0]
                        dy = nodes[clicked].position[1] - nodes[self.selected_node].position[1]
                        dist = math.hypot(dx, dy) / 10
                        cost = self.CONNECTION_COSTS.get(ct_name, 0) * self.active_level * dist
                        self.show_flash(
                            f"Insufficient funds  (need ${cost:,.1f}M)",
                            shake_node=self.selected_node
                        )
                        # keep selected_node so the player can see what failed
                    else:
                        self.selected_node = None

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if self.canvas_rect().collidepoint(event.pos):
                self.selected_node = None
                return True

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.selected_node = None
                return True

            # ── Upgrade hovered connection ─────────────────────────────
            if event.key == pygame.K_x and self.hovered_conn is not None:
                all_conns = getattr(self, '_cached_all_conns', [])
                if self.hovered_conn < len(all_conns):
                    on_upgrade_connection(all_conns[self.hovered_conn])
                return True

        elif event.type == pygame.MOUSEWHEEL:
            # Only zoom when the cursor is over the canvas
            mouse_pos = pygame.mouse.get_pos()
            if self.canvas_rect().collidepoint(mouse_pos):
                old_zoom = self.zoom
                new_zoom = max(ZOOM_MIN, min(ZOOM_MAX, self.zoom + event.y * ZOOM_STEP))

                # Zoom toward the cursor position so it stays fixed on screen.
                # Convert cursor to canvas-center-relative coords before/after.
                canvas = self.canvas_rect()
                cx = canvas.width  / 2
                cy = self.surface.get_height() / 2

                # Screen offset of cursor from canvas center
                dx = mouse_pos[0] - cx
                dy = mouse_pos[1] - cy

                # Adjust pan so the world point under the cursor stays put.
                # The world coordinate under the cursor before zoom:
                #   world_x = dx / (ps * old_zoom) - pan_offset[0]
                # We want that same world_x to map to the same screen dx after zoom:
                #   dx / (ps * new_zoom) - pan_offset[0]' = world_x
                # Solving: pan_offset[0]' = dx/ps * (1/new_zoom - 1/old_zoom) + pan_offset[0]
                # So the delta to add is dx/ps * (1/new_zoom - 1/old_zoom)
                self.zoom = new_zoom
                ps = self._pos_scale_base()
                self._pan_offset[0] += dx / ps * (1.0 / new_zoom - 1.0 / old_zoom)
                self._pan_offset[1] += dy / ps * (1.0 / new_zoom - 1.0 / old_zoom)
                return True



        elif event.type == pygame.MOUSEMOTION:
            if self.canvas_rect().collidepoint(event.pos):
                self.hovered_node = self._node_at(nodes, event.pos)
                if self.hovered_node is None:
                    self.hovered_conn = self._connection_at(nodes, event.pos)
                else:
                    self.hovered_conn = None
                self._hovered_type_idx = None  # cursor is on canvas, not panel
            else:
                self.hovered_node = None
                self.hovered_conn = None
                # Check if hovering a connection type button
                self._hovered_type_idx = None
                for i, rect in enumerate(self._type_btn_rects):
                    if rect.collidepoint(event.pos):
                        self._hovered_type_idx = i
                        break
        return False

    def update(self, nodes: list, money: float, moneyPerDay: float):
        self.surface.fill(C_TITLE_BG)
        canvas = self.canvas_rect()

        old_clip = self.surface.get_clip()
        self.surface.set_clip(canvas)

        self._draw_connections(nodes)
        self._draw_preview(nodes)
        self._draw_nodes(nodes)
        self._draw_flash()

        self.surface.set_clip(old_clip)
        self._draw_node_tooltip(nodes)
        self._draw_connection_tooltip(nodes)
        self._draw_panel(nodes, money, moneyPerDay)
        self._draw_zoom_indicator()
        self._draw_connection_preview_tooltip(nodes)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _draw_zoom_indicator(self):
        """Small zoom level label in the bottom-left of the canvas."""
        font = _font(16, self.surface)
        label = font.render(f"zoom: {self.zoom:.1f}x  (scroll to zoom)", True, C_HINT)
        self.surface.blit(label, (8, self.surface.get_height() - label.get_height() - 6))

    def _draw_node_tooltip(self, nodes: list):
        if self.hovered_node is None:
            return
        node = nodes[self.hovered_node]

        font_title = _font(25, self.surface, bold=True)
        font_body = _font(20, self.surface)
        pad = 10
        line_h = font_body.get_height()

        title_text = f"{node.nodeType.displayName}  (Lv. {node.level})"

        need_lines = []
        for need_key, (people, goods) in node.needs.items():
            display_name = self.NEED_DISPLAY_NAMES.get(need_key, need_key)
            if people > 0:
                need_lines.append((display_name, "People", people))
            if goods > 0:
                need_lines.append((display_name, "Goods", goods))

        met, total = node.ratioNeedsMet()

        bar_h = max(4, _scale(5, self.surface))
        bar_row_h = bar_h + 8

        n_text_lines = len(need_lines) + 1
        box_h = (font_title.get_height() + pad
                 + n_text_lines * (line_h + 2)
                 + (line_h + 2)
                 + pad * 2 - (0 if need_lines else 18))
        box_w = max(160, _scale(200, self.surface))

        mx, my = pygame.mouse.get_pos()
        tx = mx + 14
        ty = my - box_h // 2
        canvas_w = self.canvas_rect().width
        if tx + box_w > canvas_w:
            tx = mx - box_w - 10
        ty = max(4, min(ty, self.surface.get_height() - box_h - 4))

        box = pygame.Rect(tx, ty, box_w, box_h)
        pygame.draw.rect(self.surface, (255, 255, 255), box, border_radius=8)
        pygame.draw.rect(self.surface, (180, 180, 180), box, width=1, border_radius=8)

        y = ty + pad
        title_surf = font_title.render(title_text, True, (30, 30, 30))
        self.surface.blit(title_surf, (tx + pad, y))
        y += font_title.get_height() + 4

        pygame.draw.line(self.surface, (200, 200, 200),
                         (tx + pad, y), (tx + box_w - pad, y), 1)
        y += 6

        if need_lines:
            needs_title = font_body.render("Needs:", True, (0, 0, 0))
            self.surface.blit(needs_title, (tx + pad, y))
            y += line_h + 2

            for display_name, sub_label, amount in need_lines:
                label = font_body.render(f"{display_name} — {sub_label}: {amount}", True, (60, 60, 60))
                self.surface.blit(label, (tx + pad, y))
                y += line_h + 2

            pct = int(met / total * 100) if total > 0 else 0
            fulfilled_label = font_body.render(f"Need Fulfilled: {pct}%", True, (60, 60, 60))
            self.surface.blit(fulfilled_label, (tx + pad, y))
            y += line_h + 2
            bar_total_w = box_w - pad * 2
            bar_rect = pygame.Rect(tx + pad, y, bar_total_w, bar_h)
            pygame.draw.rect(self.surface, (210, 210, 210), bar_rect, border_radius=2)
            fill_w = int(bar_total_w * pct / 100)
            if fill_w > 0:
                fill_color = (11, 133, 120) if pct >= 80 else (209, 151, 17) if pct >= 40 else (200, 80, 60)
                pygame.draw.rect(self.surface, fill_color,
                                 pygame.Rect(tx + pad, y, fill_w, bar_h), border_radius=2)
            y += bar_row_h
        else:
            no_needs = font_body.render("No Needs", True, (150, 150, 150))
            self.surface.blit(no_needs, (tx + pad, y))

    def _pos_scale_base(self) -> float:
        """Base scale factor without zoom applied."""
        canvas = self.canvas_rect()
        return min(canvas.width / 1200, self.surface.get_height() / 900)

    def _pos_scale(self) -> float:
        return self._pos_scale_base() * self.zoom

    def _to_screen(self, pos):
        cx = self.canvas_rect().width  / 2
        cy = self.surface.get_height() / 2
        s  = self._pos_scale()
        return (
            int((pos[0] + self._pan_offset[0]) * s + cx),
            int((pos[1] + self._pan_offset[1]) * s + cy),
        )

    def _node_radius(self, node) -> int:
        base = _scale(BASE_NODE_RADIUS, self.surface)
        per_level = _scale(NODE_RADIUS_PER_LEVEL, self.surface)
        return max(2, int((base + node.level * per_level) * self.zoom))

    def _node_at(self, nodes, screen_pos):
        for i, node in enumerate(nodes):
            sp = self._to_screen(node.position)
            self._last_node_positions[i] = sp
            radius = self._node_radius(node)
            if math.hypot(screen_pos[0] - sp[0], screen_pos[1] - sp[1]) <= radius + 4:
                return i
        return None

    def _node_color(self, node_type):
        return NODE_TYPE_COLORS.get(node_type.name, (180, 180, 180))

    def _connection_style(self, conn_type):
        return CONNECTION_TYPE_STYLES.get(conn_type.name, {"color": (100, 100, 100), "dash": None})

    def _draw_dashed_line(self, color, start, end, width, dash_length=10):
        dx, dy = end[0] - start[0], end[1] - start[1]
        length = math.hypot(dx, dy)
        if length == 0:
            return
        steps = int(length / dash_length)
        for i in range(0, steps, 2):
            s = (start[0] + dx * i / steps,                start[1] + dy * i / steps)
            e = (start[0] + dx * min(i+1, steps) / steps,  start[1] + dy * min(i+1, steps) / steps)
            pygame.draw.line(self.surface, color, s, e, width)

    def _offset_line(self, p1, p2, offset):
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        length = math.hypot(dx, dy)
        if length == 0:
            return p1, p2
        px, py = -dy / length * offset, dx / length * offset
        return (p1[0] + px, p1[1] + py), (p2[0] + px, p2[1] + py)

    def _gather_connection_pairs(self, nodes):
        pair_map: dict[frozenset, list] = {}
        seen = set()
        for node in nodes:
            for conn in node.connections:
                if id(conn) in seen:
                    continue
                seen.add(id(conn))
                key = frozenset([id(conn.nodes[0]), id(conn.nodes[1])])
                pair_map.setdefault(key, []).append(conn)
        return pair_map

    def _draw_connections(self, nodes):
        pair_map = self._gather_connection_pairs(nodes)

        for key, connections in pair_map.items():
            n = len(connections)
            for i, c in enumerate(connections):
                offset = (i - (n - 1) / 2) * CONNECTION_OFFSET * self.zoom
                p1 = self._to_screen(c.nodes[0].position)
                p2 = self._to_screen(c.nodes[1].position)
                op1, op2 = self._offset_line(p1, p2, offset)
                style = self._connection_style(c.type)
                base_color = style.get("color", (100, 100, 100))
                width = max(1, int((BASE_CONNECTION_WIDTH + c.level * CONNECTION_WIDTH_PER_LEVEL) * self.zoom))
                dash_len = max(4, int(10 * self.zoom))

                # Tint toward red based on fullness (max of people/goods load ratio)
                cap_people, cap_goods = c.capacity
                load_people, load_goods = c.load
                used_people = cap_people - load_people
                used_goods = cap_goods - load_goods
                p_ratio = (used_people / cap_people) if cap_people > 0 else 0.0
                g_ratio = (used_goods / cap_goods) if cap_goods > 0 else 0.0
                full_ratio = max(p_ratio, g_ratio)  # 0.0 = empty, 1.0 = full
                full_ratio = max(0.0, min(1.0, full_ratio))
                full_ratio = 0 if full_ratio < 0.5 else full_ratio

                # Blend base_color → red by up to 50%
                red = (200, 80, 60)
                t = full_ratio  # 0.0 → 0.5
                color = tuple(int(base_color[j] * (1 - t) + red[j] * t) for j in range(3))

                if style.get("dash"):
                    self._draw_dashed_line(color, op1, op2, width,
                                           style.get("dash") if isinstance(style.get("dash"), int) else dash_len)
                else:
                    pygame.draw.line(self.surface, color, op1, op2, width)

    def _draw_preview(self, nodes):
        if self.selected_node is None:
            return
        p1 = self._to_screen(nodes[self.selected_node].position)
        mx, my = pygame.mouse.get_pos()
        p2 = (mx, my) if self.hovered_node is None else self._to_screen(nodes[self.hovered_node].position)
        self._draw_dashed_line(C_PREVIEW, p1, p2, 1, 8)

    def _draw_nodes(self, nodes):
        self._last_node_positions = {}
        for i, node in enumerate(nodes):
            sp = self._to_screen(node.position)
            radius = self._node_radius(node)
            base_color = self._node_color(node.nodeType)

            # Tint darker based on unmet needs (0% unmet = original, 100% unmet = 50% darker)
            met, total = node.ratioNeedsMet()
            if total > 0:
                unmet_ratio = 1.0 - (met / total)  # 0.0 = all met, 1.0 = none met
            else:
                unmet_ratio = 0.0
            dark_factor = 1.0 - (unmet_ratio * 0.5)  # ranges from 1.0 down to 0.5
            color = tuple(int(c * dark_factor) for c in base_color)

            if i == self.selected_node:
                pygame.draw.circle(self.surface, C_SELECT_RING, sp, radius + 6, 2)
            elif i == self.hovered_node and self.selected_node is not None:
                pygame.draw.circle(self.surface, (200, 200, 255), sp, radius + 5, 2)

            pygame.draw.circle(self.surface, color, sp, radius)

    # --- Panel --------------------------------------------------------

    def _draw_panel(self, nodes, money: float, moneyPerDay: float):
        sw = self.surface.get_width()
        sh = self.surface.get_height()

        pw      = self._panel_width()
        pad     = self._panel_padding()
        btn_h   = self._btn_height()
        btn_gap = self._btn_gap()
        lvl_h   = self._level_box_h()

        font_md = _font(20, self.surface)
        font_sm = _font(16, self.surface)
        font_lg = _font(28, self.surface)

        px = sw - pw
        panel_rect = pygame.Rect(px, 0, pw, sh)

        pygame.draw.rect(self.surface, C_PANEL_BG,  panel_rect)
        pygame.draw.line(self.surface, C_PANEL_EDGE, (px, 0), (px, sh), 1)

        x  = px + pad
        bw = pw - pad * 2
        y  = pad

        # ── Playback controls ──────────────────────────────────────────
        ctrl_btn_w = (bw - btn_gap) // 2

        # Pause / Play button
        pause_rect = pygame.Rect(x, y, ctrl_btn_w, btn_h)
        self._pause_btn_rect = pause_rect
        pause_color = C_PAUSE_BTN_PAUSED if self.paused else C_PAUSE_BTN
        pygame.draw.rect(self.surface, pause_color, pause_rect, border_radius=6)
        pause_label = "> Play" if self.paused else "|| Pause"
        p_surf = font_md.render(pause_label, True, C_BTN_TEXT_A)
        self.surface.blit(p_surf, p_surf.get_rect(center=pause_rect.center))

        # Speed button
        speed_rect = pygame.Rect(x + ctrl_btn_w + btn_gap, y, bw - ctrl_btn_w - btn_gap, btn_h)
        self._speed_btn_rect = speed_rect
        speed_color = C_SPEED_BTN_MAX if self.game_speed == SPEED_STEPS[-1] else C_SPEED_BTN
        pygame.draw.rect(self.surface, speed_color, speed_rect, border_radius=6)
        speed_label = f"x{self.game_speed}"
        s_surf = font_md.render(speed_label, True, C_BTN_TEXT_A)
        self.surface.blit(s_surf, s_surf.get_rect(center=speed_rect.center))

        y += btn_h + pad

        # Divider
        pygame.draw.line(self.surface, C_PANEL_EDGE, (x, y), (x + bw, y), 1)
        y += pad

        # ── Money display ──
        font_money_label = _font(16, self.surface)
        font_money_val = _font(30, self.surface, bold=True)

        money_label_surf = font_money_label.render("BALANCE", True, C_HINT)
        self.surface.blit(money_label_surf, money_label_surf.get_rect(centerx=px + pw // 2, y=y))
        y += money_label_surf.get_height() + 2

        money_color = (11, 133, 120) if money >= 0 else (200, 80, 60)
        money_str = f"${money:,.2f}M"
        money_surf = font_money_val.render(money_str, True, money_color)

        font_money_day = _font(16, self.surface)
        day_color = (11, 133, 120) if moneyPerDay >= 0 else (200, 80, 60)
        day_sign = "+" if moneyPerDay >= 0 else ""
        day_str = f"{day_sign}${moneyPerDay * 1000:,.2f}k / day"
        day_surf = font_money_day.render(day_str, True, day_color)

        pill_h = font_money_val.get_height() + day_surf.get_height() + pad + 6
        pill_rect = pygame.Rect(x, y, bw, pill_h)
        pygame.draw.rect(self.surface, C_LEVEL_BG, pill_rect, border_radius=8)
        self.surface.blit(money_surf, money_surf.get_rect(centerx=pill_rect.centerx,
                                                          y=pill_rect.y + pad // 2))
        self.surface.blit(day_surf, day_surf.get_rect(centerx=pill_rect.centerx,
                                                      y=pill_rect.y + pad // 2 + font_money_val.get_height() + 2))
        y += pill_rect.height + pad

        # ── City needs met bar ─────────────────────────────────────────
        # Compute aggregate needs met across all nodes
        total_met = 0.0
        total_needed = 0.0
        for node in nodes:
            m, t = node.ratioNeedsMet()
            total_met += m
            total_needed += t
        needs_pct = int(total_met / total_needed * 100) if total_needed > 0 else 100

        needs_label_surf = font_money_label.render("CITY NEEDS MET", True, C_HINT)
        self.surface.blit(needs_label_surf,
                          needs_label_surf.get_rect(centerx=px + pw // 2, y=y))
        y += needs_label_surf.get_height() + 2

        # Color: green → amber → orange → red
        if needs_pct >= 80:
            needs_color = (11, 133, 120)  # teal/green
        elif needs_pct >= 60:
            needs_color = (209, 151, 17)  # amber
        elif needs_pct >= 40:
            needs_color = (220, 100, 40)  # orange
        else:
            needs_color = (200, 80, 60)  # red

        needs_pill_h = font_money_val.get_height() + 10
        needs_pill_rect = pygame.Rect(x, y, bw, needs_pill_h)
        pygame.draw.rect(self.surface, C_LEVEL_BG, needs_pill_rect, border_radius=8)

        pct_surf = font_money_val.render(f"{needs_pct}%", True, needs_color)
        self.surface.blit(pct_surf, pct_surf.get_rect(
            centerx=needs_pill_rect.centerx,
            y=needs_pill_rect.y + 4
        ))
        y += needs_pill_h + 4

        # Progress bar
        bar_h_needs = max(6, _scale(8, self.surface))
        bar_rect_needs = pygame.Rect(x, y, bw, bar_h_needs)
        pygame.draw.rect(self.surface, (200, 200, 200), bar_rect_needs, border_radius=4)
        fill_w_needs = int(bw * needs_pct / 100)
        if fill_w_needs > 0:
            pygame.draw.rect(self.surface, needs_color,
                             pygame.Rect(x, y, fill_w_needs, bar_h_needs), border_radius=4)
        y += bar_h_needs + pad

        # Divider before connection controls
        pygame.draw.line(self.surface, C_PANEL_EDGE,
                         (x, y), (x + bw, y), 1)
        y += pad

        # ── Title ──
        lbl = font_md.render("New Connection", True, C_BTN_TEXT)
        self.surface.blit(lbl, (x, y))
        y += lbl.get_height() + pad // 2

        # ── Type buttons ──
        lbl = font_sm.render("Type", True, C_HINT)
        self.surface.blit(lbl, (x, y))
        y += lbl.get_height() + 4

        self._type_btn_rects = []
        for i, ct in enumerate(CONNECTION_TYPES):
            rect = pygame.Rect(x, y, bw, btn_h)
            self._type_btn_rects.append(rect)
            active = (i == self.active_type_idx)
            pygame.draw.rect(self.surface, C_BTN_ACTIVE if active else C_BTN, rect, border_radius=6)
            tc = C_BTN_TEXT_A if active else C_BTN_TEXT
            t  = font_md.render(ct["name"], True, tc)
            self.surface.blit(t, t.get_rect(center=rect.center))
            y += btn_h + btn_gap

        y += pad // 2

        self._draw_type_tooltip()

        # ── Level — now controlled by clickable − / + buttons ──
        lbl = font_sm.render("Level", True, C_HINT)
        self.surface.blit(lbl, (x, y))
        y += lbl.get_height() + 4

        lvl_rect = pygame.Rect(x, y, bw, lvl_h)
        pygame.draw.rect(self.surface, C_LEVEL_BG, lvl_rect, border_radius=6)

        # − button (left third)
        minus_w = lvl_h  # square
        minus_rect = pygame.Rect(lvl_rect.x, lvl_rect.y, minus_w, lvl_h)
        minus_color = C_BTN if self.active_level > 1 else (200, 200, 200)
        pygame.draw.rect(self.surface, minus_color, minus_rect, border_radius=6)
        minus_surf = font_lg.render("−", True, C_BTN_TEXT if self.active_level > 1 else C_HINT)
        self.surface.blit(minus_surf, minus_surf.get_rect(center=minus_rect.center))
        self._level_minus_rect = minus_rect

        # + button (right third)
        plus_rect = pygame.Rect(lvl_rect.right - minus_w, lvl_rect.y, minus_w, lvl_h)
        plus_color = C_BTN if self.active_level < 10 else (200, 200, 200)
        pygame.draw.rect(self.surface, plus_color, plus_rect, border_radius=6)
        plus_surf = font_lg.render("+", True, C_BTN_TEXT if self.active_level < 10 else C_HINT)
        self.surface.blit(plus_surf, plus_surf.get_rect(center=plus_rect.center))
        self._level_plus_rect = plus_rect

        # Level number (centre)
        num = font_lg.render(str(self.active_level), True, C_LEVEL_TEXT)
        self.surface.blit(num, num.get_rect(center=lvl_rect.center))

        y += lvl_h + pad

        # ── Status ──
        if self.selected_node is not None:
            status_color = C_STATUS_WAIT
            lines = ["node selected —", "click another to connect"]
        else:
            status_color = C_STATUS_OK
            lines = ["click a node to", "start a connection"]

        line_h   = font_sm.get_height()
        status_h = line_h * len(lines) + pad * 2
        srect = pygame.Rect(x, y, bw, status_h)
        pygame.draw.rect(self.surface, status_color, srect, border_radius=6)
        for j, line in enumerate(lines):
            t = font_sm.render(line, True, C_STATUS_TEXT)
            self.surface.blit(t, t.get_rect(centerx=srect.centerx,
                                             y=srect.y + pad + j * (line_h + 2)))
        y += status_h + pad // 2

        # ── Hint ──
        hint = font_sm.render("esc / right-click: cancel", True, C_HINT)
        self.surface.blit(hint, hint.get_rect(centerx=px + pw // 2, y=y))

    _CONNECTION_HIT_RADIUS = 8

    def _connection_at(self, nodes: list, screen_pos):
        best_idx = None
        best_dist = self._CONNECTION_HIT_RADIUS + 1
        seen = set()
        all_conns = []
        for node in nodes:
            for conn in node.connections:
                if id(conn) in seen:
                    continue
                seen.add(id(conn))
                all_conns.append(conn)
        self._cached_all_conns = all_conns

        # Build the same pair_map as _draw_connections so we can
        # replicate the lateral offset for each parallel connection.
        pair_map: dict[frozenset, list] = {}
        for conn in all_conns:
            key = frozenset([id(conn.nodes[0]), id(conn.nodes[1])])
            pair_map.setdefault(key, []).append(conn)

        for i, conn in enumerate(all_conns):
            key = frozenset([id(conn.nodes[0]), id(conn.nodes[1])])
            siblings = pair_map[key]
            n = len(siblings)
            sibling_idx = siblings.index(conn)
            offset = (sibling_idx - (n - 1) / 2) * CONNECTION_OFFSET * self.zoom

            p1 = self._to_screen(conn.nodes[0].position)
            p2 = self._to_screen(conn.nodes[1].position)
            op1, op2 = self._offset_line(p1, p2, offset)

            # Point-to-segment distance instead of point-to-midpoint.
            dx, dy = op2[0] - op1[0], op2[1] - op1[1]
            seg_len_sq = dx * dx + dy * dy
            if seg_len_sq == 0:
                dist = math.hypot(screen_pos[0] - op1[0], screen_pos[1] - op1[1])
            else:
                t = max(0.0, min(1.0, (
                        (screen_pos[0] - op1[0]) * dx +
                        (screen_pos[1] - op1[1]) * dy
                ) / seg_len_sq))
                closest_x = op1[0] + t * dx
                closest_y = op1[1] + t * dy
                dist = math.hypot(screen_pos[0] - closest_x, screen_pos[1] - closest_y)

            if dist < best_dist:
                best_dist = dist
                best_idx = i

        return best_idx

    def _draw_connection_tooltip(self, nodes: list):
        if self.hovered_conn is None:
            return
        seen = set()
        all_conns = []
        for node in nodes:
            for conn in node.connections:
                if id(conn) in seen:
                    continue
                seen.add(id(conn))
                all_conns.append(conn)
        if self.hovered_conn >= len(all_conns):
            self.hovered_conn = None
            return
        conn = all_conns[self.hovered_conn]

        font_title = _font(25, self.surface, bold=True)
        font_body = _font(20, self.surface)
        font_hint = _font(17, self.surface)
        pad = 10
        bar_h = max(4, _scale(5, self.surface))
        line_h = font_body.get_height()
        hint_line_h = font_hint.get_height()

        cap_people, cap_goods = conn.capacity
        load_people, load_goods = conn.load

        load_people = cap_people - load_people
        load_goods = cap_goods - load_goods

        title_text = conn.type.name.capitalize()

        # ── Compute upgrade cost/upkeep for display ──────────────────
        ct_name = conn.type.name
        dx = conn.nodes[1].position[0] - conn.nodes[0].position[0]
        dy = conn.nodes[1].position[1] - conn.nodes[0].position[1]
        distance = math.hypot(dx, dy) / 10
        upgrade_cost   = self.CONNECTION_COSTS.get(ct_name, 0) * 1 * distance  # cost of +1 level
        upgrade_upkeep = self.CONNECTION_UPKEEP_COSTS.get(ct_name, 0) * 1 * distance

        # extra rows: upgrade cost, upkeep delta, hint
        upgrade_rows = 2
        hint_rows = 1

        box_h = (font_title.get_height() + pad
                 + 6
                 + (line_h + 2)                        # Level row
                 + 2 * (line_h + 2 + bar_h + 6)        # People / Goods bars
                 + 6                                    # divider gap
                 + upgrade_rows * (line_h + 2)          # upgrade cost rows
                 + 6                                    # small gap before hint
                 + hint_line_h + 4                      # "press X to upgrade" hint
                 + pad)
        box_w = max(200, _scale(230, self.surface))

        mx, my = pygame.mouse.get_pos()
        tx = mx + 14
        ty = my - box_h // 2
        canvas_w = self.canvas_rect().width
        if tx + box_w > canvas_w:
            tx = mx - box_w - 10
        ty = max(4, min(ty, self.surface.get_height() - box_h - 4))

        box = pygame.Rect(tx, ty, box_w, box_h)
        pygame.draw.rect(self.surface, (255, 255, 255), box, border_radius=8)
        pygame.draw.rect(self.surface, (180, 180, 180), box, width=1, border_radius=8)

        y = ty + pad

        title_surf = font_title.render(title_text, True, (30, 30, 30))
        self.surface.blit(title_surf, (tx + pad, y))
        y += font_title.get_height() + 4

        pygame.draw.line(self.surface, (200, 200, 200),
                         (tx + pad, y), (tx + box_w - pad, y), 1)
        y += 6

        level_surf = font_body.render(f"Level: {conn.level}", True, (60, 60, 60))
        self.surface.blit(level_surf, (tx + pad, y))
        y += line_h + 2

        bar_total_w = box_w - pad * 2
        for label, load, cap in [("People", load_people, cap_people),
                                 ("Goods", load_goods, cap_goods)]:
            lbl_surf = font_body.render(f"{label}: {int(load)}/{int(cap)}", True, (60, 60, 60))
            self.surface.blit(lbl_surf, (tx + pad, y))
            y += line_h + 2

            pct = (load / cap) if cap > 0 else 0
            bar_rect = pygame.Rect(tx + pad, y, bar_total_w, bar_h)
            pygame.draw.rect(self.surface, (210, 210, 210), bar_rect, border_radius=2)
            fill_w = int(bar_total_w * min(pct, 1.0))
            if fill_w > 0:
                fill_color = ((200, 80, 60) if pct >= 1.0 else
                              (209, 151, 17) if pct >= 0.75 else
                              (11, 133, 120))
                pygame.draw.rect(self.surface, fill_color,
                                 pygame.Rect(tx + pad, y, fill_w, bar_h),
                                 border_radius=2)
            y += bar_h + 6

        # ── Upgrade section ──────────────────────────────────────────
        pygame.draw.line(self.surface, (200, 200, 200),
                         (tx + pad, y), (tx + box_w - pad, y), 1)
        y += 6

        upgrade_rows_data = [
            ("Upgrade cost",   f"${upgrade_cost:,.2f}M",              (200, 80, 60)),
            ("Upkeep delta",   f"+${upgrade_upkeep * 1000:,.3f}k/day", (209, 151, 17)),
        ]
        for label, val, color in upgrade_rows_data:
            lbl_surf = font_body.render(label, True, (80, 80, 80))
            val_surf = font_body.render(val, True, color)
            self.surface.blit(lbl_surf, (tx + pad, y))
            self.surface.blit(val_surf, (tx + box_w - pad - val_surf.get_width(), y))
            y += line_h + 2

        # ── "Press X to upgrade" hint ────────────────────────────────
        y += 4
        hint_surf = font_hint.render("Press  X  to upgrade", True, (70, 130, 220))
        self.surface.blit(hint_surf, hint_surf.get_rect(centerx=tx + box_w // 2, y=y))

    CONNECTION_COSTS = {
        "Passenger Rail": 75,
        "Freight Rail": 15,
        "Highway": 10,
    }
    CONNECTION_UPKEEP_COSTS = {
        "Passenger Rail": 0.0125,
        "Freight Rail": 0.05 / 365.0,
        "Highway": 0.035 / 365.0,
    }

    def _draw_type_tooltip(self):
        if self._hovered_type_idx is None:
            return
        if self._hovered_type_idx >= len(self._type_btn_rects):
            return

        import util
        ct = CONNECTION_TYPES[self._hovered_type_idx]
        name = ct["name"]
        btn_rect = self._type_btn_rects[self._hovered_type_idx]

        cap_people, cap_goods = util.connectionTypes[name].capacity
        cost = self.CONNECTION_COSTS.get(name, 0)
        upkeep = self.CONNECTION_UPKEEP_COSTS.get(name, 0)

        font_title = _font(22, self.surface, bold=True)
        font_body = _font(18, self.surface)
        pad = 8
        line_h = font_body.get_height()

        rows = [
            f"People cap: {cap_people}",
            f"Goods cap:  {cap_goods}",
            f"Cost:   ${cost * self.active_level}M / mi",
            f"Upkeep: ${upkeep * self.active_level * 1000:.4f}k / mi / day",
        ]

        title_surf = font_title.render(name, True, (30, 30, 30))
        max_text_w = max(title_surf.get_width(),
                         max(font_body.render(r, True, (0, 0, 0)).get_width() for r in rows))
        box_w = max_text_w + pad * 2
        box_h = font_title.get_height() + 4 + 1 + 6 + len(rows) * (line_h + 2) + pad * 2

        # Position: below the hovered button, right-aligned to the panel left edge
        tx = btn_rect.left - box_w - 6
        ty = btn_rect.top

        # Keep on screen vertically
        sh = self.surface.get_height()
        if ty + box_h > sh - 4:
            ty = sh - box_h - 4

        box = pygame.Rect(tx, ty, box_w, box_h)
        pygame.draw.rect(self.surface, (255, 255, 255), box, border_radius=8)
        pygame.draw.rect(self.surface, (180, 180, 180), box, width=1, border_radius=8)

        y = ty + pad
        self.surface.blit(title_surf, (tx + pad, y))
        y += font_title.get_height() + 4
        pygame.draw.line(self.surface, (200, 200, 200),
                         (tx + pad, y), (tx + box_w - pad, y), 1)
        y += 6

        divider_row = 2  # draw a divider before cost rows
        for i, row in enumerate(rows):
            if i == divider_row:
                pygame.draw.line(self.surface, (220, 220, 220),
                                 (tx + pad, y - 3), (tx + box_w - pad, y - 3), 1)
            color = (60, 60, 60) if i >= divider_row else (80, 80, 80)
            surf = font_body.render(row, True, color)
            self.surface.blit(surf, (tx + pad, y))
            y += line_h + 2

    def _draw_connection_preview_tooltip(self, nodes: list):
        """Projected build cost, upkeep, and daily income when hovering a target node."""
        if self.selected_node is None or self.hovered_node is None:
            return
        if self.hovered_node == self.selected_node:
            return

        node_a = nodes[self.selected_node]
        node_b = nodes[self.hovered_node]

        dx = node_b.position[0] - node_a.position[0]
        dy = node_b.position[1] - node_a.position[1]
        # Divide by whatever constant maps your world coords → miles/km.
        # 100 is a reasonable default; tune to match your game's scale.
        distance = math.hypot(dx, dy) / 10

        ct_name = CONNECTION_TYPES[self.active_type_idx]["name"]
        level = self.active_level
        build_cost = self.CONNECTION_COSTS.get(ct_name, 0) * level * distance
        daily_upkeep = self.CONNECTION_UPKEEP_COSTS.get(ct_name, 0) * level * distance

        font_title = _font(22, self.surface, bold=True)
        font_body = _font(18, self.surface)
        pad = 10
        line_h = font_body.get_height()

        rows = [
            ("Build cost", f"${build_cost:,.2f}M", (200, 80, 60)),
            ("Daily upkeep", f"-${daily_upkeep * 1000:,.3f}k / day", (209, 151, 17)),
        ]

        title_text = f"Build {ct_name}  (Lv.{level})"
        title_surf = font_title.render(title_text, True, (30, 30, 30))

        max_row_w = max(
            font_body.render(label + "  " + val, True, (0, 0, 0)).get_width()
            for label, val, _ in rows
        )
        box_w = max(title_surf.get_width(), max_row_w) + pad * 2
        box_h = (pad
                 + font_title.get_height() + 4
                 + 1 + 6  # divider
                 + len(rows) * (line_h + 4)
                 + pad)

        # Anchor tooltip near the hovered node, offset so it doesn't cover it.
        sp = self._to_screen(node_b.position)
        node_r = self._node_radius(node_b)
        tx = sp[0] + node_r + 12
        ty = sp[1] - box_h // 2

        canvas_w = self.canvas_rect().width
        sh = self.surface.get_height()
        if tx + box_w > canvas_w - 4:
            tx = sp[0] - node_r - box_w - 12
        ty = max(4, min(ty, sh - box_h - 4))

        box = pygame.Rect(tx, ty, box_w, box_h)
        pygame.draw.rect(self.surface, (255, 255, 255), box, border_radius=8)
        pygame.draw.rect(self.surface, (180, 180, 180), box, width=1, border_radius=8)

        y = ty + pad
        self.surface.blit(title_surf, (tx + pad, y))
        y += font_title.get_height() + 4

        pygame.draw.line(self.surface, (200, 200, 200),
                         (tx + pad, y), (tx + box_w - pad, y), 1)
        y += 6

        for label, val, color in rows:
            lbl_surf = font_body.render(label, True, (80, 80, 80))
            val_surf = font_body.render(val, True, color)
            self.surface.blit(lbl_surf, (tx + pad, y))
            self.surface.blit(val_surf, (tx + box_w - pad - val_surf.get_width(), y))
            y += line_h + 4

    def show_lose_screen(self, days_survived: int):
        """
        Render a blocking modal lose screen over the live game canvas.

        The city network remains visible behind a semi-transparent dark overlay.

        Returns:
            True  – player wants to restart (clicked 'Play Again' or pressed Enter/Space)
            False – player wants to quit   (closed the window or pressed Escape/Q)
        """
        sw, sh = self.surface.get_size()
        cx, cy = sw // 2, sh // 2

        # Capture the current frame so the background stays frozen (not live-updating).
        background_snapshot = self.surface.copy()

        # Overlay surface — semi-transparent dark wash over the whole window.
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((10, 14, 22, 190))  # dark navy, ~75% opaque

        # Modal dimensions
        modal_w = min(_scale(420, self.surface, "w"), sw - _scale(60, self.surface, "w"))
        modal_h = _scale(340, self.surface)
        modal_x = cx - modal_w // 2
        modal_y = cy - modal_h // 2

        font_heading = _font(72, self.surface, bold=True)
        font_sub = _font(24, self.surface)
        font_score = _font(44, self.surface, bold=True)
        font_score_lbl = _font(18, self.surface)
        font_btn = _font(24, self.surface, bold=True)
        font_hint = _font(14, self.surface)

        clock = pygame.time.Clock()

        while True:
            clock.tick(10)
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        return True
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        return False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_rect.collidepoint(event.pos):
                        return True
                    if event.button == 1 and quit_rect.collidepoint(event.pos):
                        return False

            # ── Frozen background + dark wash ────────────────────────────
            self.surface.blit(background_snapshot, (0, 0))
            self.surface.blit(overlay, (0, 0))

            # ── Modal card ────────────────────────────────────────────────
            pad = _scale(24, self.surface)

            # Drop shadow
            shadow_surf = pygame.Surface((modal_w + 16, modal_h + 16), pygame.SRCALPHA)
            shadow_surf.fill((0, 0, 0, 0))
            pygame.draw.rect(shadow_surf, (0, 0, 0, 100),
                             pygame.Rect(8, 8, modal_w, modal_h), border_radius=14)
            self.surface.blit(shadow_surf, (modal_x - 8, modal_y - 8))

            # Card body
            card = pygame.Rect(modal_x, modal_y, modal_w, modal_h)
            pygame.draw.rect(self.surface, (22, 28, 40), card, border_radius=14)

            # Red accent bar at top of card
            accent_bar = pygame.Rect(modal_x, modal_y, modal_w, _scale(5, self.surface))
            pygame.draw.rect(self.surface, (200, 80, 60), accent_bar,
                             border_radius=14)  # pygame clips bottom corners automatically

            # Card border
            pygame.draw.rect(self.surface, (55, 65, 85), card, width=1, border_radius=14)

            # ── Content layout (top-to-bottom inside card) ────────────────
            y = modal_y + _scale(28, self.surface)

            # "GAME OVER"
            heading_surf = font_heading.render("GAME OVER", True, (220, 70, 55))
            self.surface.blit(heading_surf, heading_surf.get_rect(centerx=cx, y=y))
            y += heading_surf.get_height() + _scale(4, self.surface)

            # Thin divider line
            pygame.draw.line(self.surface, (55, 65, 85),
                             (modal_x + pad, y), (modal_x + modal_w - pad, y), 1)
            y += _scale(12, self.surface)

            # Subtitle
            sub_surf = font_sub.render("Your city ran out of funds.", True, (120, 130, 150))
            self.surface.blit(sub_surf, sub_surf.get_rect(centerx=cx, y=y))
            y += sub_surf.get_height() + _scale(18, self.surface)

            # Score pill background
            pill_w = _scale(180, self.surface, "w")
            pill_h = _scale(72, self.surface)
            pill_rect = pygame.Rect(cx - pill_w // 2, y, pill_w, pill_h)
            pygame.draw.rect(self.surface, (30, 38, 55), pill_rect, border_radius=10)
            pygame.draw.rect(self.surface, (55, 65, 85), pill_rect, width=1, border_radius=10)

            lbl_surf = font_score_lbl.render("DAYS SURVIVED", True, (90, 105, 130))
            self.surface.blit(lbl_surf, lbl_surf.get_rect(centerx=cx, y=pill_rect.y + _scale(8, self.surface)))

            score_surf = font_score.render(str(days_survived), True, (220, 225, 235))
            self.surface.blit(score_surf, score_surf.get_rect(
                centerx=cx, y=pill_rect.y + lbl_surf.get_height() + _scale(8, self.surface)))

            y += pill_h + _scale(22, self.surface)

            # ── Buttons (Play Again + Quit side by side) ──────────────────
            btn_gap = _scale(10, self.surface)
            btn_w = (modal_w - pad * 2 - btn_gap) // 2
            btn_h = _scale(42, self.surface)

            restart_rect = pygame.Rect(modal_x + pad, y, btn_w, btn_h)
            quit_rect = pygame.Rect(modal_x + pad + btn_w + btn_gap, y, btn_w, btn_h)

            # Keep btn_rect pointing at restart for the keyboard shortcut hit-test above.
            btn_rect = restart_rect

            restart_hovered = restart_rect.collidepoint(mouse_pos)
            quit_hovered = quit_rect.collidepoint(mouse_pos)

            restart_color = (14, 170, 153) if restart_hovered else (11, 133, 120)
            quit_color = (75, 55, 55) if quit_hovered else (55, 40, 40)

            pygame.draw.rect(self.surface, restart_color, restart_rect, border_radius=8)
            pygame.draw.rect(self.surface, (11, 133, 120), restart_rect, width=1, border_radius=8)
            r_label = font_btn.render("PLAY AGAIN", True, (255, 255, 255))
            self.surface.blit(r_label, r_label.get_rect(center=restart_rect.center))

            pygame.draw.rect(self.surface, quit_color, quit_rect, border_radius=8)
            pygame.draw.rect(self.surface, (90, 60, 60), quit_rect, width=1, border_radius=8)
            q_label = font_btn.render("QUIT", True, (200, 160, 160))
            self.surface.blit(q_label, q_label.get_rect(center=quit_rect.center))

            # Also handle quit button click (separate from the event loop above)

            # ── Keyboard hint ─────────────────────────────────────────────
            hint_y = modal_y + modal_h + _scale(8, self.surface)
            hint_surf = font_hint.render("Enter / Space — restart   ·   Esc — quit", True, (70, 82, 100))
            self.surface.blit(hint_surf, hint_surf.get_rect(centerx=cx, y=hint_y))

            pygame.display.flip()

    def show_flash(self, message: str, shake_node: int | None = None):
        """Show a timed error pill on the canvas. Optionally wobble a node."""
        self._flash_message = message
        self._flash_expires = self._time.monotonic() + 2.5
        self._flash_shake_node = shake_node
        self._flash_shake_start = self._time.monotonic()

    def _draw_flash(self):
        """Render error flash pill and node shake ring. Called each frame from update()."""
        if self._flash_message is None:
            return
        now = self._time.monotonic()
        if now >= self._flash_expires:
            self._flash_message = None
            self._flash_shake_node = None
            return

        remaining = self._flash_expires - now
        # Fade out over the final 0.5 s
        alpha_frac = min(1.0, remaining / 0.5)
        a = int(230 * alpha_frac)

        font = _font(20, self.surface, bold=True)
        text_surf = font.render(self._flash_message, True, (255, 255, 255))

        h_pad, v_pad = 16, 10
        pill_w = text_surf.get_width() + h_pad * 2
        pill_h = text_surf.get_height() + v_pad * 2

        canvas = self.canvas_rect()
        pill_x = canvas.left + (canvas.width - pill_w) // 2
        pill_y = _scale(20, self.surface)

        pill_surf = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
        pygame.draw.rect(pill_surf, (170, 45, 35, a),
                         pill_surf.get_rect(), border_radius=10)
        pygame.draw.rect(pill_surf, (220, 85, 65, a),
                         pill_surf.get_rect(), width=1, border_radius=10)
        # Warning icon rendered as text (✕ or !)
        warn_font = _font(20, self.surface)
        warn_surf = warn_font.render("!", True, (255, 215, 60))
        warn_bg = pygame.Surface((warn_surf.get_width() + 6, warn_surf.get_height() + 2),
                                 pygame.SRCALPHA)
        warn_bg.blit(warn_surf, (3, 1))
        pill_surf.blit(warn_bg, (h_pad - warn_bg.get_width(), v_pad))
        pill_surf.blit(text_surf, (h_pad, v_pad))
        self.surface.blit(pill_surf, (pill_x, pill_y))

        # Shake ring on the source node
        if self._flash_shake_node is not None:
            elapsed = now - self._flash_shake_start
            shake_dur = 0.5
            if elapsed < shake_dur:
                # Oscillate ring radius
                t = elapsed / shake_dur
                ring_r = int(6 + 4 * math.sin(t * math.pi * 6) * (1 - t))
                ring_a = int(255 * (1 - t) * alpha_frac)
                ring_color = (220, 80, 60, ring_a)

                # We need the node's screen position — stored from last _draw_nodes call
                node_sp = getattr(self, '_last_node_positions', {}).get(self._flash_shake_node)
                if node_sp:
                    ring_surf = pygame.Surface(
                        (ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(ring_surf, ring_color,
                                       (ring_r + 2, ring_r + 2), ring_r, 2)
                    self.surface.blit(ring_surf,
                                      (node_sp[0] - ring_r - 2,
                                       node_sp[1] - ring_r - 2))