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

JUNCTION_COSTS = { # $million per level
    "Passenger Rail": 15,
    "Freight Rail": 0.25,
    "Highway": 6
}

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

# ── Tutorial text ────────────────────────────────────────────────────────────
# Edit the lines below to customise the tutorial shown on the title screen.
# Use "\n" to start a new paragraph. Each entry in the list becomes a section.
TUTORIAL_SECTIONS: list[tuple[str, str]] = [
    (
        "Welcome to Mini Transit!",
        "Build a transit network connecting your city's districts together.\n"
        "Your goal is to keep the city funded by satisfying demand "
        "if you go bankrupt then your game is over!"
    ),
    (
        "Making Connections",
        "Select a node, then click another to draw a connection between them.\n"
        "Use the panel on the right to choose the connection type and upgrade level.\n"
        "there are three connection types highways, passenger rail, and freight rail.\n"
        "base highways can transport 3 people and 2 goods per day, base passenger rail can transport 25 people per day, base freight rail can transport 20 goods per day.\n"
        "you can level up your connections by hovering over it and pressing x, each level up increase the load of the connection, by one base level of goods."
    ),
    (
        "Node Types",
        "Center — the city hub (teal).\n"
        "Residential — where people live (green).\n"
        "Commercial / Market — where people shop (blue).\n"
        "Industrial — freight and goods (amber).\n"
        "Out of City — external connections (grey)."
    ),
    (
        "Playback Controls",
        "Use the Pause/Play button to start and stop time.\n"
        "The Speed button cycles through 1×, 2×, 3× and 4× simulation speed.\n"
        "Watch your budget in the top bar — build efficiently!"
    ),
]


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
        self._tutorial_btn_rect: pygame.Rect | None = None
        self._show_tutorial = False
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
            # Close tutorial overlay if open
            if self._show_tutorial:
                self._show_tutorial = False
                return True
            if self._btn_rect and self._btn_rect.collidepoint(event.pos):
                self.started = True
                return True
            if self._tutorial_btn_rect and self._tutorial_btn_rect.collidepoint(event.pos):
                self._show_tutorial = True
                return True

        if event.type == pygame.KEYDOWN:
            if self._show_tutorial and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self._show_tutorial = False
                return True
            if not self._show_tutorial and event.key in (pygame.K_RETURN, pygame.K_SPACE):
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

        if self._show_tutorial:
            self._draw_tutorial_overlay()

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

        bw = _scale(160, self.surface, "w")
        bh = _scale(48, self.surface)
        btn_top = cy + _scale(80, self.surface)
        gap = _scale(14, self.surface, "w")

        # Two buttons centred together
        total_w = bw * 2 + gap
        start_rect = pygame.Rect(cx - total_w // 2, btn_top, bw, bh)
        tut_rect   = pygame.Rect(cx - total_w // 2 + bw + gap, btn_top, bw, bh)

        self._btn_rect          = start_rect
        self._tutorial_btn_rect = tut_rect

        # START button
        hovered_s = start_rect.collidepoint(mouse_pos)
        color_s   = C_START_BTN_HOVER if hovered_s else C_START_BTN
        pygame.draw.rect(self.surface, color_s, start_rect, border_radius=8)
        pygame.draw.rect(self.surface, C_TITLE_ACCENT2, start_rect, width=1, border_radius=8)
        label_s = font_btn.render("START", True, C_START_BTN_TEXT)
        self.surface.blit(label_s, label_s.get_rect(center=start_rect.center))

        # TUTORIAL button
        C_TUT_BTN       = (40, 60, 100)
        C_TUT_BTN_HOVER = (55, 85, 140)
        hovered_t = tut_rect.collidepoint(mouse_pos)
        color_t   = C_TUT_BTN_HOVER if hovered_t else C_TUT_BTN
        pygame.draw.rect(self.surface, color_t, tut_rect, border_radius=8)
        pygame.draw.rect(self.surface, C_TITLE_ACCENT2, tut_rect, width=1, border_radius=8)
        label_t = font_btn.render("TUTORIAL", True, C_START_BTN_TEXT)
        self.surface.blit(label_t, label_t.get_rect(center=tut_rect.center))

    def _draw_tutorial_overlay(self):
        """Draw a modal overlay with the tutorial text over the title screen."""
        sw, sh = self.surface.get_size()
        cx = sw // 2

        # Dark translucent backdrop
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.surface.blit(overlay, (0, 0))

        # Card dimensions
        card_w = min(_scale(640, self.surface, "w"), int(sw * 0.85))
        pad    = _scale(28, self.surface)

        # Pre-render all text so we can measure total card height
        font_heading  = _font(34, self.surface, bold=True)
        font_section  = _font(22, self.surface, bold=True)
        font_body     = _font(20, self.surface)
        font_hint     = _font(16, self.surface)

        line_gap   = _scale(6,  self.surface)
        sec_gap    = _scale(18, self.surface)
        inner_w    = card_w - pad * 2

        def wrap(text: str, font: pygame.font.Font, max_w: int) -> list[str]:
            """Wrap text to fit within max_w pixels."""
            lines: list[str] = []
            for paragraph in text.split("\n"):
                words = paragraph.split()
                if not words:
                    lines.append("")
                    continue
                current = ""
                for word in words:
                    test = (current + " " + word).strip()
                    if font.size(test)[0] <= max_w:
                        current = test
                    else:
                        if current:
                            lines.append(current)
                        current = word
                if current:
                    lines.append(current)
            return lines

        # Build rendered blocks: list of (surface, x_offset)
        blocks: list[pygame.Surface] = []

        heading_surf = font_heading.render("How to Play", True, C_TITLE_ACCENT)
        blocks.append(heading_surf)

        for title, body in TUTORIAL_SECTIONS:
            blocks.append(None)  # spacer sentinel
            sec_surf = font_section.render(title, True, (200, 215, 235))
            blocks.append(sec_surf)
            for line in wrap(body, font_body, inner_w):
                blocks.append(font_body.render(line if line else " ", True, (160, 175, 195)))

        hint_surf = font_hint.render("Click anywhere or press Esc to close", True, (80, 95, 115))

        total_h = pad
        for b in blocks:
            if b is None:
                total_h += sec_gap
            else:
                total_h += b.get_height() + line_gap
        total_h += sec_gap + hint_surf.get_height() + pad

        card_h = min(total_h, int(sh * 0.82))
        card_x = cx - card_w // 2
        card_y = (sh - card_h) // 2

        # Drop shadow
        shadow = pygame.Surface((card_w + 20, card_h + 20), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 90),
                         pygame.Rect(10, 10, card_w, card_h), border_radius=16)
        self.surface.blit(shadow, (card_x - 10, card_y - 10))

        # Card body
        card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
        pygame.draw.rect(self.surface, (18, 24, 38), card_rect, border_radius=16)
        pygame.draw.rect(self.surface, C_TITLE_ACCENT, card_rect, width=2, border_radius=16)

        # Accent bar
        accent = pygame.Rect(card_x, card_y, card_w, _scale(5, self.surface))
        pygame.draw.rect(self.surface, C_TITLE_ACCENT, accent, border_radius=16)

        # Clip content to card
        clip_rect = pygame.Rect(card_x + pad, card_y + pad,
                                inner_w, card_h - pad * 2)
        old_clip = self.surface.get_clip()
        self.surface.set_clip(clip_rect)

        y = card_y + pad
        for b in blocks:
            if b is None:
                y += sec_gap
            else:
                self.surface.blit(b, (card_x + pad, y))
                y += b.get_height() + line_gap

        self.surface.set_clip(old_clip)

        # Hint pinned to bottom of card
        self.surface.blit(hint_surf,
                          hint_surf.get_rect(centerx=cx, y=card_y + card_h - pad // 2 - hint_surf.get_height()))

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

        # Junction targeting: index into _cached_all_conns of a same-type
        # connection the player is hovering while a node is selected.
        self.hovered_junction_conn: int | None = None

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

    def _screen_to_world(self, screen_pos) -> tuple[float, float]:
        """Convert a screen-space position to world-space coordinates."""
        cx = self.canvas_rect().width / 2
        cy = self.surface.get_height() / 2
        s  = self._pos_scale()
        wx = (screen_pos[0] - cx) / s - self._pan_offset[0]
        wy = (screen_pos[1] - cy) / s - self._pan_offset[1]
        return (wx, wy)

    def _closest_point_on_conn(self, conn, screen_pos) -> tuple[float, float]:
        """
        Return the world-space position of the closest point on a connection's
        rendered line segment to the given screen position.
        Accounts for the lateral offset used when parallel connections exist.
        """
        # We need the sibling count to replicate the offset, but since this is
        # called after _gather_connection_pairs we can compute it on the fly.
        pair_map = self._gather_connection_pairs_cached()
        key = tuple(sorted([id(conn.nodes[0]), id(conn.nodes[1])]))
        siblings = pair_map.get(key, [conn])
        n = len(siblings)
        try:
            sibling_idx = next(i for i, s in enumerate(siblings) if id(s) == id(conn))
        except StopIteration:
            sibling_idx = 0
        offset = (sibling_idx - (n - 1) / 2) * CONNECTION_OFFSET * self.zoom

        p1 = self._to_screen(conn.nodes[0].position)
        p2 = self._to_screen(conn.nodes[1].position)
        op1, op2 = self._offset_line(p1, p2, offset)

        dx, dy = op2[0] - op1[0], op2[1] - op1[1]
        seg_len_sq = dx * dx + dy * dy
        if seg_len_sq == 0:
            closest_screen = op1
        else:
            t = max(0.0, min(1.0, (
                (screen_pos[0] - op1[0]) * dx +
                (screen_pos[1] - op1[1]) * dy
            ) / seg_len_sq))
            closest_screen = (op1[0] + t * dx, op1[1] + t * dy)

        return self._screen_to_world(closest_screen)

    # Cache for the pair_map so we don't rebuild it multiple times per frame.
    _pair_map_cache: dict | None = None
    _pair_map_nodes_id: int | None = None

    def _gather_connection_pairs_cached(self) -> dict:
        """Return the pair_map; rebuilt whenever _cached_all_conns changes."""
        return getattr(self, '_pair_map_last', {})

    def handle_event(self, event, nodes, on_connect, on_upgrade_connection, on_junction=None):
        """
        on_junction(world_pos: tuple[float, float], conn_type: str, from_node, level: int) -> bool
            Called when the player targets a connection instead of a node.
            world_pos   – world-space position of the snap point on the connection.
            conn_type   – name of the active connection type (e.g. "Highway").
            from_node   – the node object the player started the connection from.
            level       – the active connection level selected in the panel.
            Should create a junction node at world_pos and wire everything up.
            Return True on success, False on failure (e.g. insufficient funds).
        """
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
                clicked_node = self._node_at(nodes, pos)

                if clicked_node is None:
                    # ── Check for junction click (node selected + hovering same-type conn) ──
                    if (self.selected_node is not None
                            and on_junction is not None
                            and self.hovered_junction_conn is not None):
                        all_conns = getattr(self, '_cached_all_conns', [])
                        if self.hovered_junction_conn < len(all_conns):
                            target_conn = all_conns[self.hovered_junction_conn]
                            world_pos = self._closest_point_on_conn(target_conn, pos)
                            conn_type = CONNECTION_TYPES[self.active_type_idx]["name"]
                            from_node = nodes[self.selected_node]
                            success = on_junction(world_pos, conn_type, from_node, all_conns[self.hovered_junction_conn])
                            if not success:
                                self.show_flash("Insufficient funds for junction")
                            else:
                                self.selected_node = None
                            return True

                    self.selected_node = None

                elif self.selected_node is None:
                    self.selected_node = clicked_node
                elif clicked_node == self.selected_node:
                    self.selected_node = None
                else:
                    type_name = CONNECTION_TYPES[self.active_type_idx]["name"]
                    success = on_connect(nodes[self.selected_node], nodes[clicked_node], type_name, self.active_level)
                    if not success:
                        ct_name = CONNECTION_TYPES[self.active_type_idx]["name"]
                        dx = nodes[clicked_node].position[0] - nodes[self.selected_node].position[0]
                        dy = nodes[clicked_node].position[1] - nodes[self.selected_node].position[1]
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
                    res = on_upgrade_connection(all_conns[self.hovered_conn])
                    if res != "":
                        self.show_flash(res)
                return True
            if event.key == pygame.K_SPACE:
                self.paused = not self.paused

        elif event.type == pygame.MOUSEWHEEL:
            # Only zoom when the cursor is over the canvas
            mouse_pos = pygame.mouse.get_pos()
            if self.canvas_rect().collidepoint(mouse_pos):
                old_zoom = self.zoom
                new_zoom = max(ZOOM_MIN, min(ZOOM_MAX, self.zoom + event.y * ZOOM_STEP))

                canvas = self.canvas_rect()
                cx = canvas.width  / 2
                cy = self.surface.get_height() / 2

                dx = mouse_pos[0] - cx
                dy = mouse_pos[1] - cy

                self.zoom = new_zoom
                ps = self._pos_scale_base()
                self._pan_offset[0] += dx / ps * (1.0 / new_zoom - 1.0 / old_zoom)
                self._pan_offset[1] += dy / ps * (1.0 / new_zoom - 1.0 / old_zoom)
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self.canvas_rect().collidepoint(event.pos):
                self.hovered_node = self._node_at(nodes, event.pos)

                if self.hovered_node is None:
                    # Standard connection hover (for inspection tooltip / X-upgrade)
                    self.hovered_conn = self._connection_at(nodes, event.pos)
                else:
                    self.hovered_conn = None
                    self.hovered_junction_conn = None

                self._hovered_type_idx = None
            else:
                self.hovered_node = None
                self.hovered_conn = None
                self.hovered_junction_conn = None
                self._hovered_type_idx = None
                for i, rect in enumerate(self._type_btn_rects):
                    if rect.collidepoint(event.pos):
                        self._hovered_type_idx = i
                        break
        return False

    def update(self, nodes: list, money: float, moneyPerMonth: float):
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
        self._draw_panel(nodes, money, moneyPerMonth)
        self._draw_zoom_indicator()
        self._draw_connection_preview_tooltip(nodes)
        # Must come after _draw_connection_preview_tooltip so it draws on top
        self._draw_junction_preview_tooltip(nodes)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _draw_zoom_indicator(self):
        """Small zoom level label in the bottom-left of the canvas."""
        font = _font(16, self.surface)
        label = font.render(f"zoom: {self.zoom:.1f}x  (scroll to zoom)", True, C_HINT)
        self.surface.blit(label, (8, self.surface.get_height() - label.get_height() - 6))

    def _draw_node_tooltip(self, nodes: list):
        if self.hovered_node is None or self.hovered_node >= len(nodes):
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
        return (round(p1[0] + px), round(p1[1] + py)), (round(p2[0] + px), round(p2[1] + py))

    def _gather_connection_pairs(self, nodes):
        pair_map: dict[tuple, list] = {}
        seen = set()
        # Collect all connections in a stable order first
        all_conns = []
        for node in nodes:
            for conn in node.connections:
                if id(conn) in seen:
                    continue
                seen.add(id(conn))
                all_conns.append(conn)
        # Sort ALL connections globally by type name so grouping order is deterministic
        all_conns.sort(key=lambda c: c.type.name)
        for conn in all_conns:
            key = tuple(sorted([id(conn.nodes[0]), id(conn.nodes[1])]))
            pair_map.setdefault(key, []).append(conn)
        return pair_map

    def _draw_connections(self, nodes):
        pair_map = self._gather_connection_pairs(nodes)
        # Cache for junction detection later in the same frame
        self._pair_map_last = pair_map

        for key, connections in pair_map.items():
            n = len(connections)

            # In _draw_connections, before the inner loop:
            max_width = max(
                max(1, int((BASE_CONNECTION_WIDTH + c.level * CONNECTION_WIDTH_PER_LEVEL) * self.zoom))
                for c in connections
            )

            std_node_order = (self._to_screen(connections[0].nodes[0].position), self._to_screen(connections[0].nodes[1].position))

            for i, c in enumerate(connections):
                offset = (i - (n - 1) / 2) * (CONNECTION_OFFSET + max_width) * self.zoom
                op1, op2 = self._offset_line(std_node_order[0], std_node_order[1], offset)
                style = self._connection_style(c.type)
                base_color = style.get("color", (100, 100, 100))
                width = max(1, int((BASE_CONNECTION_WIDTH + c.level * CONNECTION_WIDTH_PER_LEVEL) * self.zoom))
                dash_len = max(4, int(10 * self.zoom))

                cap_people, cap_goods = c.capacity
                load_people, load_goods = c.load
                used_people = cap_people - load_people
                used_goods = cap_goods - load_goods
                p_ratio = (used_people / cap_people) if cap_people > 0 else 0.0
                g_ratio = (used_goods / cap_goods) if cap_goods > 0 else 0.0
                full_ratio = max(p_ratio, g_ratio)
                full_ratio = max(0.0, min(1.0, full_ratio))
                full_ratio = 0 if full_ratio < 0.5 else full_ratio

                red = (200, 80, 60)
                t = full_ratio
                color = tuple(int(base_color[j] * (1 - t) + red[j] * t) for j in range(3))

                # Highlight the junction-hovered connection
                all_conns = getattr(self, '_cached_all_conns', [])
                jconn_idx = self.hovered_junction_conn
                is_junction_target = (
                    jconn_idx is not None
                    and jconn_idx < len(all_conns)
                    and id(all_conns[jconn_idx]) == id(c)
                )
                if is_junction_target:
                    # Draw a bright highlight stroke behind the connection line
                    highlight_color = (255, 220, 60)
                    hw = width + max(3, int(4 * self.zoom))
                    pygame.draw.line(self.surface, highlight_color, op1, op2, hw)

                if style.get("dash"):
                    self._draw_dashed_line(color, op1, op2, width,
                                           style.get("dash") if isinstance(style.get("dash"), int) else dash_len)
                else:
                    pygame.draw.line(self.surface, color, op1, op2, width)

                # Draw a small diamond snap-point when junction-hovering
                if is_junction_target:
                    snap_sp = self._snap_screen_pos
                    if snap_sp:
                        sr = max(5, int(6 * self.zoom))
                        pts = [
                            (snap_sp[0],      snap_sp[1] - sr),
                            (snap_sp[0] + sr, snap_sp[1]),
                            (snap_sp[0],      snap_sp[1] + sr),
                            (snap_sp[0] - sr, snap_sp[1]),
                        ]
                        pygame.draw.polygon(self.surface, (255, 220, 60), pts)
                        pygame.draw.polygon(self.surface, (200, 140, 0), pts, 1)

    def _draw_preview(self, nodes):
        if self.selected_node is None:
            return
        p1 = self._to_screen(nodes[self.selected_node].position)

        if self.hovered_junction_conn is not None and self.hovered_node is None:
            # Snap preview line endpoint to the junction snap point on the connection
            p2 = self._snap_screen_pos if self._snap_screen_pos else pygame.mouse.get_pos()
        elif self.hovered_node is None:
            p2 = pygame.mouse.get_pos()
        else:
            p2 = self._to_screen(nodes[self.hovered_node].position)

        self._draw_dashed_line(C_PREVIEW, p1, p2, 1, 8)

    def _draw_nodes(self, nodes):
        self._last_node_positions = {}
        for i, node in enumerate(nodes):
            sp = self._to_screen(node.position)
            radius = self._node_radius(node)
            base_color = self._node_color(node.nodeType)

            met, total = node.ratioNeedsMet()
            if total > 0:
                unmet_ratio = 1.0 - (met / total)
            else:
                unmet_ratio = 0.0
            dark_factor = 1.0 - (unmet_ratio * 0.5)
            color = tuple(int(c * dark_factor) for c in base_color)

            if i == self.selected_node:
                pygame.draw.circle(self.surface, C_SELECT_RING, sp, radius + 6, 2)
            elif i == self.hovered_node and self.selected_node is not None:
                pygame.draw.circle(self.surface, (200, 200, 255), sp, radius + 5, 2)

            pygame.draw.circle(self.surface, color, sp, radius)
            self._last_node_positions[i] = sp

    # --- Panel --------------------------------------------------------

    def _draw_panel(self, nodes, money: float, moneyPerMonth: float):
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

        pause_rect = pygame.Rect(x, y, ctrl_btn_w, btn_h)
        self._pause_btn_rect = pause_rect
        pause_color = C_PAUSE_BTN_PAUSED if self.paused else C_PAUSE_BTN
        pygame.draw.rect(self.surface, pause_color, pause_rect, border_radius=6)
        pause_label = "> Play" if self.paused else "|| Pause"
        p_surf = font_md.render(pause_label, True, C_BTN_TEXT_A)
        self.surface.blit(p_surf, p_surf.get_rect(center=pause_rect.center))

        speed_rect = pygame.Rect(x + ctrl_btn_w + btn_gap, y, bw - ctrl_btn_w - btn_gap, btn_h)
        self._speed_btn_rect = speed_rect
        speed_color = C_SPEED_BTN_MAX if self.game_speed == SPEED_STEPS[-1] else C_SPEED_BTN
        pygame.draw.rect(self.surface, speed_color, speed_rect, border_radius=6)
        speed_label = f"x{self.game_speed}"
        s_surf = font_md.render(speed_label, True, C_BTN_TEXT_A)
        self.surface.blit(s_surf, s_surf.get_rect(center=speed_rect.center))

        y += btn_h + pad

        pygame.draw.line(self.surface, C_PANEL_EDGE, (x, y), (x + bw, y), 1)
        y += pad

        # ── Money display ──
        font_money_label = _font(16, self.surface)
        font_money_val = _font(30, self.surface, bold=True)

        money_label_surf = font_money_label.render("BALANCE", True, C_HINT)
        self.surface.blit(money_label_surf, money_label_surf.get_rect(centerx=px + pw // 2, y=y))
        y += money_label_surf.get_height() + 2

        money_color = (11, 133, 120) if money >= 0 else (200, 80, 60)
        money_str = f"${money if money < 1000 else money / 1000:,.2f}{'M' if money < 1000 else 'B'}"
        money_surf = font_money_val.render(money_str, True, money_color)

        font_money_day = _font(16, self.surface)
        day_color = (11, 133, 120) if moneyPerMonth >= 0 else (200, 80, 60)
        day_sign = "+" if moneyPerMonth >= 0 else ""
        day_str = f"{day_sign}${moneyPerMonth * 1000 if moneyPerMonth < 1 else moneyPerMonth:,.2f}{'k' if moneyPerMonth < 1 else 'M'} / month"
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

        if needs_pct >= 80:
            needs_color = (11, 133, 120)
        elif needs_pct >= 60:
            needs_color = (209, 151, 17)
        elif needs_pct >= 40:
            needs_color = (220, 100, 40)
        else:
            needs_color = (200, 80, 60)

        needs_pill_h = font_money_val.get_height() + 10
        needs_pill_rect = pygame.Rect(x, y, bw, needs_pill_h)
        pygame.draw.rect(self.surface, C_LEVEL_BG, needs_pill_rect, border_radius=8)

        pct_surf = font_money_val.render(f"{needs_pct}%", True, needs_color)
        self.surface.blit(pct_surf, pct_surf.get_rect(
            centerx=needs_pill_rect.centerx,
            y=needs_pill_rect.y + 4
        ))
        y += needs_pill_h + 4

        bar_h_needs = max(6, _scale(8, self.surface))
        bar_rect_needs = pygame.Rect(x, y, bw, bar_h_needs)
        pygame.draw.rect(self.surface, (200, 200, 200), bar_rect_needs, border_radius=4)
        fill_w_needs = int(bw * needs_pct / 100)
        if fill_w_needs > 0:
            pygame.draw.rect(self.surface, needs_color,
                             pygame.Rect(x, y, fill_w_needs, bar_h_needs), border_radius=4)
        y += bar_h_needs + pad

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

        # ── Status ──
        if self.selected_node is not None:
            status_color = C_STATUS_WAIT
            lines = ["node selected —", "click node or same-", "type line to connect"]
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

        pair_map: dict[tuple, list] = {}
        for conn in all_conns:
            key = tuple(sorted([id(conn.nodes[0]), id(conn.nodes[1])]))
            pair_map.setdefault(key, []).append(conn)
        for key in pair_map:
            pair_map[key].sort(key=lambda c: c.type.name)

        for i, conn in enumerate(all_conns):
            key = tuple(sorted([id(conn.nodes[0]), id(conn.nodes[1])]))
            siblings = pair_map[key]
            n = len(siblings)
            sibling_idx = siblings.index(conn)
            max_width = max(
                max(1, int((BASE_CONNECTION_WIDTH + s.level * CONNECTION_WIDTH_PER_LEVEL) * self.zoom))
                for s in siblings
            )
            offset = (sibling_idx - (n - 1) / 2) * (CONNECTION_OFFSET + max_width) * self.zoom

            # ── Use siblings[0]'s node order as the canonical orientation,
            #    matching _draw_connections. ──────────────────────────────
            p1 = self._to_screen(siblings[0].nodes[0].position)
            p2 = self._to_screen(siblings[0].nodes[1].position)
            op1, op2 = self._offset_line(p1, p2, offset)

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

    def _junction_conn_at(self, nodes: list, screen_pos) -> int | None:
        """
        Return the index (into _cached_all_conns) of the nearest connection
        that matches the currently active connection type AND is within hit
        radius.  Returns None if no such connection is near the cursor.

        Also stores the snapped world position in self._snap_world_pos and
        the snapped screen position in self._snap_screen_pos.
        """
        self._snap_world_pos = None
        self._snap_screen_pos = None

        all_conns = getattr(self, '_cached_all_conns', [])
        if not all_conns:
            return None

        active_type_name = CONNECTION_TYPES[self.active_type_idx]["name"]

        pair_map: dict[tuple, list] = {}
        for conn in all_conns:
            key = tuple(sorted([id(conn.nodes[0]), id(conn.nodes[1])]))
            pair_map.setdefault(key, []).append(conn)
        for key in pair_map:
            pair_map[key].sort(key=lambda c: c.type.name)

        best_idx = None
        best_dist = self._CONNECTION_HIT_RADIUS + 1
        best_closest_screen = None

        for i, conn in enumerate(all_conns):
            # Only match connections of the same type as active
            if conn.type.name != active_type_name:
                continue

            key = tuple(sorted([id(conn.nodes[0]), id(conn.nodes[1])]))
            siblings = pair_map[key]
            n = len(siblings)
            sibling_idx = siblings.index(conn)
            max_width = max(
                max(1, int((BASE_CONNECTION_WIDTH + s.level * CONNECTION_WIDTH_PER_LEVEL) * self.zoom))
                for s in siblings
            )
            offset = (sibling_idx - (n - 1) / 2) * (CONNECTION_OFFSET + max_width) * self.zoom

            p1 = self._to_screen(conn.nodes[0].position)
            p2 = self._to_screen(conn.nodes[1].position)
            op1, op2 = self._offset_line(p1, p2, offset)

            dx, dy = op2[0] - op1[0], op2[1] - op1[1]
            seg_len_sq = dx * dx + dy * dy
            if seg_len_sq == 0:
                closest = op1
                dist = math.hypot(screen_pos[0] - op1[0], screen_pos[1] - op1[1])
            else:
                t = max(0.0, min(1.0, (
                    (screen_pos[0] - op1[0]) * dx +
                    (screen_pos[1] - op1[1]) * dy
                ) / seg_len_sq))
                closest = (op1[0] + t * dx, op1[1] + t * dy)
                dist = math.hypot(screen_pos[0] - closest[0], screen_pos[1] - closest[1])

            if dist < best_dist:
                best_dist = dist
                best_idx = i
                best_closest_screen = closest

        if best_idx is not None:
            self._snap_screen_pos = (int(best_closest_screen[0]), int(best_closest_screen[1]))
            self._snap_world_pos = self._screen_to_world(best_closest_screen)

        return best_idx

    # ------------------------------------------------------------------
    # Junction preview tooltip
    # ------------------------------------------------------------------

    def _draw_junction_preview_tooltip(self, nodes: list):
        """
        Show build cost + upkeep tooltip when the player (with a node selected)
        hovers over a same-type connection to place a junction.
        """
        if self.selected_node is None:
            return
        if self.hovered_node is not None:
            return  # node tooltip takes priority
        if self.hovered_junction_conn is None:
            return

        all_conns = getattr(self, '_cached_all_conns', [])
        if self.hovered_junction_conn >= len(all_conns):
            return

        snap_world = getattr(self, '_snap_world_pos', None)
        if snap_world is None:
            return

        src_node = nodes[self.selected_node]

        # Distance from the selected node to the snap point on the connection
        dx = snap_world[0] - src_node.position[0]
        dy = snap_world[1] - src_node.position[1]
        distance = math.hypot(dx, dy) / 10  # same scale divisor as elsewhere

        ct_name = CONNECTION_TYPES[self.active_type_idx]["name"]
        level = self.active_level
        build_cost = self.CONNECTION_COSTS.get(ct_name, 0) * level * distance + JUNCTION_COSTS[ct_name] * all_conns[self.hovered_junction_conn].level
        monthly_upkeep = self.CONNECTION_UPKEEP_COSTS.get(ct_name, 0) * level * distance

        font_title = _font(22, self.surface, bold=True)
        font_body = _font(18, self.surface)
        pad = 10
        line_h = font_body.get_height()

        title_text = f"Junction on {ct_name}  (Lv.{level})"
        title_surf = font_title.render(title_text, True, (30, 30, 30))

        rows = [
            ("Build cost",     f"${build_cost:,.2f}M",               (200, 80, 60)),
            ("Monthly upkeep", f"-${monthly_upkeep * 1000:,.2f}k / month", (209, 151, 17)),
        ]

        # Divider row + note
        note_text = "Creates a junction node"
        note_surf = font_body.render(note_text, True, (100, 100, 100))

        max_row_w = max(
            font_body.render(lbl + "  " + val, True, (0, 0, 0)).get_width()
            for lbl, val, _ in rows
        )
        box_w = max(title_surf.get_width(), max_row_w, note_surf.get_width()) + pad * 2
        box_h = (pad
                 + font_title.get_height() + 4
                 + 1 + 6                         # divider
                 + len(rows) * (line_h + 4)
                 + 4 + 1 + 6                     # second divider + note
                 + line_h
                 + pad)

        # Anchor near the snap point on the connection
        snap_sp = getattr(self, '_snap_screen_pos', None)
        if snap_sp:
            tx = snap_sp[0] + 16
            ty = snap_sp[1] - box_h // 2
        else:
            mx, my = pygame.mouse.get_pos()
            tx = mx + 16
            ty = my - box_h // 2

        canvas_w = self.canvas_rect().width
        sh = self.surface.get_height()
        if tx + box_w > canvas_w - 4:
            tx = (snap_sp[0] if snap_sp else mx) - box_w - 16
        ty = max(4, min(ty, sh - box_h - 4))

        box = pygame.Rect(tx, ty, box_w, box_h)
        pygame.draw.rect(self.surface, (255, 255, 255), box, border_radius=8)
        # Amber border to distinguish from the node-to-node tooltip
        pygame.draw.rect(self.surface, (200, 150, 30), box, width=2, border_radius=8)

        y = ty + pad
        self.surface.blit(title_surf, (tx + pad, y))
        y += font_title.get_height() + 4

        pygame.draw.line(self.surface, (200, 200, 200),
                         (tx + pad, y), (tx + box_w - pad, y), 1)
        y += 6

        for lbl, val, color in rows:
            lbl_surf = font_body.render(lbl, True, (80, 80, 80))
            val_surf = font_body.render(val, True, color)
            self.surface.blit(lbl_surf, (tx + pad, y))
            self.surface.blit(val_surf, (tx + box_w - pad - val_surf.get_width(), y))
            y += line_h + 4

        y += 2
        pygame.draw.line(self.surface, (220, 220, 220),
                         (tx + pad, y), (tx + box_w - pad, y), 1)
        y += 6
        self.surface.blit(note_surf, note_surf.get_rect(centerx=tx + box_w // 2, y=y))

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

        ct_name = conn.type.name
        dx = conn.nodes[1].position[0] - conn.nodes[0].position[0]
        dy = conn.nodes[1].position[1] - conn.nodes[0].position[1]
        distance = math.hypot(dx, dy) / 10
        upgrade_cost   = self.CONNECTION_COSTS.get(ct_name, 0) * 1 * distance
        upgrade_upkeep = self.CONNECTION_UPKEEP_COSTS.get(ct_name, 0) * 1 * distance

        upgrade_rows = 2
        hint_rows = 1

        box_h = (font_title.get_height() + pad
                 + 6
                 + (line_h + 2)
                 + 2 * (line_h + 2 + bar_h + 6)
                 + 6
                 + upgrade_rows * (line_h + 2)
                 + 6
                 + hint_line_h + 4
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

        pygame.draw.line(self.surface, (200, 200, 200),
                         (tx + pad, y), (tx + box_w - pad, y), 1)
        y += 6

        upgrade_rows_data = [
            ("Upgrade Cost:",   f"${upgrade_cost:,.2f}M",              (200, 80, 60)),
            ("Upkeep:",   f"-${upgrade_upkeep * 1000:,.2f}k/month", (209, 151, 17)),
        ]
        for label, val, color in upgrade_rows_data:
            lbl_surf = font_body.render(label, True, (80, 80, 80))
            val_surf = font_body.render(val, True, color)
            self.surface.blit(lbl_surf, (tx + pad, y))
            self.surface.blit(val_surf, (tx + box_w - pad - val_surf.get_width(), y))
            y += line_h + 2

        y += 4
        hint_surf = font_hint.render("Press  X  to upgrade", True, (70, 130, 220))
        self.surface.blit(hint_surf, hint_surf.get_rect(centerx=tx + box_w // 2, y=y))

    CONNECTION_COSTS = {
        "Passenger Rail": 75,
        "Freight Rail": 15,
        "Highway": 10,
    }
    CONNECTION_UPKEEP_COSTS = {  # $million per mile per month per level
        "Passenger Rail": ((0.0000015) * 10 * 24 * 365) / 12,
        "Freight Rail": 0.05 / 12,
        "Highway": 0.035 / 12
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
            f"Upkeep: ${upkeep * self.active_level * 1000:.2f}k / mi / month",
        ]

        title_surf = font_title.render(name, True, (30, 30, 30))
        max_text_w = max(title_surf.get_width(),
                         max(font_body.render(r, True, (0, 0, 0)).get_width() for r in rows))
        box_w = max_text_w + pad * 2
        box_h = font_title.get_height() + 4 + 1 + 6 + len(rows) * (line_h + 2) + pad * 2

        tx = btn_rect.left - box_w - 6
        ty = btn_rect.top

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

        divider_row = 2
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
            ("Monthly upkeep", f"-${daily_upkeep * 1000:,.2f}k / month", (209, 151, 17)),
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
                 + 1 + 6
                 + len(rows) * (line_h + 4)
                 + pad)

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

    def show_lose_screen(
        self,
        transported: tuple[int, int],
        total_upkeep: float,
        total_earned: float,
        network_miles: list[float, float, float],
    ):
        """
        transported    : (total_people, total_goods) carried over the entire game.
        total_upkeep   : cumulative upkeep paid in $M.
        total_earned   : cumulative revenue earned in $M.
        network_miles  : (highway_miles, passenger_rail_miles, freight_rail_miles).
        Returns True to restart, False to quit.
        """
        total_people, total_goods               = transported
        hwy_miles, pr_miles, fr_miles           = network_miles

        # ── Helpers ────────────────────────────────────────────────────
        def fmt_money(m: float) -> str:
            """Format a $M value compactly: k suffix under $1 M, B suffix over $1 000 M."""
            if abs(m) < 1:
                return f"${m * 1000:,.0f}k"
            if abs(m) >= 1000:
                return f"${m / 1000:,.2f}B"
            return f"${m:,.2f}M"

        def fmt_miles(mi: float) -> str:
            return f"{mi:,.1f} mi"

        sw, sh = self.surface.get_size()
        cx, cy = sw // 2, sh // 2

        background_snapshot = self.surface.copy()

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((10, 14, 22, 190))

        # Card is wider and taller to fit the extra rows
        modal_w = min(_scale(560, self.surface, "w"), sw - _scale(40, self.surface, "w"))
        modal_h = _scale(580, self.surface)
        modal_x = cx - modal_w // 2
        modal_y = cy - modal_h // 2

        font_heading  = _font(72, self.surface, bold=True)
        font_sub      = _font(24, self.surface)
        font_stat_val = _font(34, self.surface, bold=True)
        font_stat_lbl = _font(15, self.surface)
        font_row_lbl  = _font(18, self.surface)
        font_row_val  = _font(18, self.surface, bold=True)
        font_sec      = _font(15, self.surface)
        font_btn      = _font(24, self.surface, bold=True)
        font_hint     = _font(14, self.surface)

        clock     = pygame.time.Clock()
        btn_rect  = pygame.Rect(0, 0, 0, 0)
        quit_rect = pygame.Rect(0, 0, 0, 0)

        while True:
            clock.tick(30)
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
                    if quit_rect.collidepoint(event.pos):
                        return False

            # ── Background ──────────────────────────────────────────────
            self.surface.blit(background_snapshot, (0, 0))
            self.surface.blit(overlay, (0, 0))

            pad = _scale(22, self.surface)
            gap = _scale(8,  self.surface)

            # Drop shadow
            shadow_surf = pygame.Surface((modal_w + 16, modal_h + 16), pygame.SRCALPHA)
            shadow_surf.fill((0, 0, 0, 0))
            pygame.draw.rect(shadow_surf, (0, 0, 0, 100),
                             pygame.Rect(8, 8, modal_w, modal_h), border_radius=14)
            self.surface.blit(shadow_surf, (modal_x - 8, modal_y - 8))

            # Card body
            card = pygame.Rect(modal_x, modal_y, modal_w, modal_h)
            pygame.draw.rect(self.surface, (22, 28, 40), card, border_radius=14)
            accent_bar = pygame.Rect(modal_x, modal_y, modal_w, _scale(5, self.surface))
            pygame.draw.rect(self.surface, (200, 80, 60), accent_bar, border_radius=14)
            pygame.draw.rect(self.surface, (55, 65, 85), card, width=1, border_radius=14)

            y = modal_y + _scale(26, self.surface)

            # ── Heading ─────────────────────────────────────────────────
            heading_surf = font_heading.render("GAME OVER", True, (220, 70, 55))
            self.surface.blit(heading_surf, heading_surf.get_rect(centerx=cx, y=y))
            y += heading_surf.get_height() + _scale(4, self.surface)

            pygame.draw.line(self.surface, (55, 65, 85),
                             (modal_x + pad, y), (modal_x + modal_w - pad, y), 1)
            y += _scale(10, self.surface)

            sub_surf = font_sub.render("Your city ran out of funds.", True, (120, 130, 150))
            self.surface.blit(sub_surf, sub_surf.get_rect(centerx=cx, y=y))
            y += sub_surf.get_height() + _scale(12, self.surface)

            # ── Section helper ───────────────────────────────────────────
            def section_label(text: str, yy: int) -> int:
                lbl = font_sec.render(text.upper(), True, (70, 85, 110))
                self.surface.blit(lbl, (modal_x + pad, yy))
                return yy + lbl.get_height() + _scale(4, self.surface)

            def draw_pill_row(pills, yy: int, pill_h: int) -> int:
                """Draw a horizontal row of stat pills. pills = list of (label, value, accent_color)."""
                n       = len(pills)
                total_gap = gap * (n - 1)
                pw      = (modal_w - pad * 2 - total_gap) // n
                for k, (lbl_text, val_text, accent) in enumerate(pills):
                    px_ = modal_x + pad + k * (pw + gap)
                    pr  = pygame.Rect(px_, yy, pw, pill_h)
                    pygame.draw.rect(self.surface, (30, 38, 55), pr, border_radius=10)
                    tb  = pygame.Rect(pr.x, pr.y, pr.width, _scale(3, self.surface))
                    pygame.draw.rect(self.surface, accent, tb, border_radius=10)
                    pygame.draw.rect(self.surface, (55, 65, 85), pr, width=1, border_radius=10)

                    ls  = font_stat_lbl.render(lbl_text, True, (90, 105, 130))
                    self.surface.blit(ls, ls.get_rect(
                        centerx=pr.centerx, y=pr.y + _scale(8, self.surface)))

                    vs  = font_stat_val.render(val_text, True, accent)
                    self.surface.blit(vs, vs.get_rect(
                        centerx=pr.centerx,
                        y=pr.y + ls.get_height() + _scale(10, self.surface)))
                return yy + pill_h + _scale(10, self.surface)

            def draw_kv_row(rows, yy: int) -> int:
                """Draw a list of (label, value, value_color) as plain key-value lines."""
                for lbl_text, val_text, val_color in rows:
                    ls = font_row_lbl.render(lbl_text, True, (110, 125, 150))
                    vs = font_row_val.render(val_text, True, val_color)
                    self.surface.blit(ls, (modal_x + pad, yy))
                    self.surface.blit(vs, vs.get_rect(right=modal_x + modal_w - pad, y=yy))
                    yy += ls.get_height() + _scale(3, self.surface)
                return yy

            def format_number(n: float) -> str:
                suffixes = [
                    (1_000_000_000_000, 'T'),
                    (1_000_000_000, 'B'),
                    (1_000_000, 'M'),
                    (1_000, 'k'),
                ]
                for threshold, suffix in suffixes:
                    if abs(n) >= threshold:
                        value = n / threshold
                        formatted = f"{value:.2f}".rstrip('0').rstrip('.')
                        return f"{formatted}{suffix}"
                return str(n)
            # ── 1. Transport stats (2 pills) ─────────────────────────────
            y = section_label("Transport", y)
            small_pill_h = _scale(68, self.surface)
            y = draw_pill_row([
                ("PASSENGERS SERVICED", format_number(total_people) + " Passengers", (11, 133, 120)),
                ("GOODS SHIPPED", format_number(total_goods) + " Tons",  (209, 151, 17)),
            ], y, small_pill_h)

            # ── 2. Finances ──────────────────────────────────────────────
            y = section_label("Finances", y)
            net = total_earned - total_upkeep
            net_color = (11, 133, 120) if net >= 0 else (200, 80, 60)
            y = draw_kv_row([
                ("Total revenue",  fmt_money(total_earned), (11, 133, 120)),
                ("Total upkeep",  f"-{fmt_money(total_upkeep)}", (200, 80, 60)),
                ("Net",            fmt_money(net),           net_color),
            ], y)
            y += _scale(10, self.surface)

            # ── 3. Network (3 pills) ─────────────────────────────────────
            y = section_label("Network built", y)
            y = draw_pill_row([
                ("HIGHWAY",        fmt_miles(hwy_miles), (80,  80,  80)),
                ("PASS. RAIL",     fmt_miles(pr_miles),  (173,  9, 232)),
                ("FREIGHT RAIL",   fmt_miles(fr_miles),  (122, 82,  13)),
            ], y, small_pill_h)

            # ── Divider ──────────────────────────────────────────────────
            pygame.draw.line(self.surface, (40, 50, 68),
                             (modal_x + pad, y), (modal_x + modal_w - pad, y), 1)
            y += _scale(10, self.surface)

            # ── Action buttons ───────────────────────────────────────────
            btn_gap = _scale(10, self.surface)
            btn_w   = (modal_w - pad * 2 - btn_gap) // 2
            btn_h_  = _scale(42, self.surface)

            btn_rect  = pygame.Rect(modal_x + pad, y, btn_w, btn_h_)
            quit_rect = pygame.Rect(modal_x + pad + btn_w + btn_gap, y, btn_w, btn_h_)

            restart_color = (14, 170, 153) if btn_rect.collidepoint(mouse_pos)  else (11, 133, 120)
            quit_color    = (75, 55, 55)   if quit_rect.collidepoint(mouse_pos) else (55, 40, 40)

            pygame.draw.rect(self.surface, restart_color, btn_rect,  border_radius=8)
            pygame.draw.rect(self.surface, (11, 133, 120), btn_rect, width=1, border_radius=8)
            self.surface.blit(
                font_btn.render("PLAY AGAIN", True, (255, 255, 255)),
                font_btn.render("PLAY AGAIN", True, (255, 255, 255)).get_rect(center=btn_rect.center))

            pygame.draw.rect(self.surface, quit_color,   quit_rect, border_radius=8)
            pygame.draw.rect(self.surface, (90, 60, 60), quit_rect, width=1, border_radius=8)
            self.surface.blit(
                font_btn.render("QUIT", True, (200, 160, 160)),
                font_btn.render("QUIT", True, (200, 160, 160)).get_rect(center=quit_rect.center))

            # Hint below the card
            hint_y    = modal_y + modal_h + _scale(8, self.surface)
            hint_surf = font_hint.render(
                "Enter / Space — restart   ·   Esc — quit", True, (70, 82, 100))
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
        warn_font = _font(20, self.surface)
        warn_surf = warn_font.render("!", True, (255, 215, 60))
        warn_bg = pygame.Surface((warn_surf.get_width() + 6, warn_surf.get_height() + 2),
                                 pygame.SRCALPHA)
        warn_bg.blit(warn_surf, (3, 1))
        pill_surf.blit(warn_bg, (h_pad - warn_bg.get_width(), v_pad))
        pill_surf.blit(text_surf, (h_pad, v_pad))
        self.surface.blit(pill_surf, (pill_x, pill_y))

        if self._flash_shake_node is not None:
            elapsed = now - self._flash_shake_start
            shake_dur = 0.5
            if elapsed < shake_dur:
                t = elapsed / shake_dur
                ring_r = int(6 + 4 * math.sin(t * math.pi * 6) * (1 - t))
                ring_a = int(255 * (1 - t) * alpha_frac)
                ring_color = (220, 80, 60, ring_a)

                node_sp = getattr(self, '_last_node_positions', {}).get(self._flash_shake_node)
                if node_sp:
                    ring_surf = pygame.Surface(
                        (ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(ring_surf, ring_color,
                                       (ring_r + 2, ring_r + 2), ring_r, 2)
                    self.surface.blit(ring_surf,
                                      (node_sp[0] - ring_r - 2,
                                       node_sp[1] - ring_r - 2))