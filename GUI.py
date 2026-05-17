import pygame
import math


NODE_TYPE_COLORS: dict[str, tuple[int, int, int]] = {
    "center": (11, 133, 120),
    "residential": (8, 196, 24),
    "market": (12, 96, 166),
    "industrial": (209, 151, 17),
    "out": (0, 0, 0),
    "junction": (100, 100, 100)
}

# Registry of available connection types for the UI.
# Add new types here; the panel will pick them up automatically.
CONNECTION_TYPES: list[dict] = [
    {"name": "Highway", "color": (0, 0, 0),    "dash": True},
    {"name": "Subway",  "color": (173, 9, 232),  "dash": False},
    {"name": "Freight Rail",    "color": (122, 82, 13), "dash": True},
]

CONNECTION_TYPE_STYLES: dict[str, dict] = {t["name"]: t for t in CONNECTION_TYPES}

BASE_NODE_RADIUS      = 10
NODE_RADIUS_PER_LEVEL = 3
BASE_CONNECTION_WIDTH      = 2
CONNECTION_WIDTH_PER_LEVEL = 1
CONNECTION_OFFSET = 6

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

# Title screen colors
C_TITLE_BG        = (15, 20, 30)
C_TITLE_ACCENT     = (11, 133, 120)
C_TITLE_ACCENT2    = (70, 130, 220)
C_TITLE_TEXT       = (220, 225, 235)
C_TITLE_SUBTEXT    = (140, 150, 165)
C_START_BTN        = (11, 133, 120)
C_START_BTN_HOVER  = (14, 170, 153)
C_START_BTN_TEXT   = (255, 255, 255)


# ---------------------------------------------------------------------------
# Responsive helpers
# ---------------------------------------------------------------------------

def _scale(reference: float, surface: pygame.Surface, axis: str = "h") -> int:
    """
    Return an integer pixel value scaled relative to a 900-px tall (or 1200-px
    wide) reference resolution, so layout proportions stay consistent at any
    window size.
    """
    if axis == "h":
        factor = surface.get_height() / 900
    else:
        factor = surface.get_width() / 1200
    return max(1, int(reference * factor))


def _font(size_ref: int, surface: pygame.Surface, bold: bool = False) -> pygame.font.Font:
    size = _scale(size_ref - 6, surface)
    # Use the bundled font directly — crisp at any size
    return pygame.font.Font(pygame.font.get_default_font(), size)


class TitleScreen:
    """
    Standalone title screen drawn on the given surface.
    Call update() each frame; it returns True once the player
    has clicked Start (the `started` flag is also set to True).

    All layout values are derived from the surface dimensions on every
    frame, so the screen responds correctly when the window is resized.
    """

    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.started = False
        self._btn_rect: pygame.Rect | None = None
        self._tick = 0

        # Decorative node positions expressed as fractions of the reference
        # radius (150 px at 900 px tall).  Scaled each frame.
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

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

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

        # Position the network above centre and the text below it.
        net_cy  = cy - _scale(80, self.surface)
        text_cy = cy + _scale(40, self.surface)

        self._draw_decorative_network(cx, net_cy)
        self._draw_title(cx, text_cy)
        self._draw_start_button(cx, text_cy)
        self._draw_hint(cx, sh)

        return False

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _to_screen(self, offset, radius, cx, cy):
        return (int(offset[0] * radius + cx), int(offset[1] * radius + cy))

    def _draw_decorative_network(self, cx, cy):
        # Scale the orbit radius with the window so nodes spread out on large
        # screens and stay visible on small ones.
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
    # Maps single-letter need keys to human-readable display names.
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
        self.hovered_conn = None
        self._type_btn_rects: list[pygame.Rect] = []

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

    def handle_event(self, event, nodes, on_connect):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            for i, rect in enumerate(self._type_btn_rects):
                if rect.collidepoint(pos):
                    self.active_type_idx = i
                    return True

            if self.canvas_rect().collidepoint(pos):
                if event.button == 1:
                    clicked = self._node_at(nodes, pos)
                    if clicked is None:
                        self.selected_node = None
                    elif self.selected_node is None:
                        self.selected_node = clicked
                    elif clicked is self.selected_node:
                        self.selected_node = None
                    else:
                        type_name = CONNECTION_TYPES[self.active_type_idx]["name"]
                        on_connect(self.selected_node, clicked, type_name, self.active_level)
                        self.selected_node = None
                    return True
                elif event.button == 3:
                    self.selected_node = None
                    return True

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.selected_node = None
                return True

        elif event.type == pygame.MOUSEWHEEL:
            self.active_level = max(1, min(10, self.active_level + event.y))
            return True


        elif event.type == pygame.MOUSEMOTION:
            if self.canvas_rect().collidepoint(event.pos):
                self.hovered_node = self._node_at(nodes, event.pos)
                self.hovered_conn = self._connection_at(nodes, event.pos)
            else:
                self.hovered_node = None
                self.hovered_conn = None

        return False

    def update(self, nodes: list):
        self.surface.fill(C_TITLE_BG)
        canvas = self.canvas_rect()

        old_clip = self.surface.get_clip()
        self.surface.set_clip(canvas)

        self._draw_connections(nodes)
        self._draw_preview(nodes)
        self._draw_nodes(nodes)

        self.surface.set_clip(old_clip)
        self._draw_node_tooltip(nodes)
        self._draw_connection_tooltip()
        self._draw_panel()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _draw_node_tooltip(self, nodes: list):
        node = self.hovered_node
        if node is None:
            return

        font_title = _font(25, self.surface, bold=True)
        font_body = _font(20, self.surface)
        pad = 10
        line_h = font_body.get_height()

        title_text = f"{node.nodeType.displayName}  (Lv. {node.level})"

        # Each need value is (people, goods); emit a sub-line for each non-zero component.
        # need_lines entries: (display_name, sub_label, amount)
        need_lines = []
        for need_key, (people, goods) in node.needs.items():
            display_name = self.NEED_DISPLAY_NAMES.get(need_key, need_key)
            if people > 0:
                need_lines.append((display_name, "People", people))
            if goods > 0:
                need_lines.append((display_name, "Goods", goods))

        # Overall needs-met summary from the single tuple.
        met, total = node._needsMet

        # One overall progress bar row (bar_h + gap).
        bar_h = max(4, _scale(5, self.surface))
        bar_row_h = bar_h + 8  # bar + breathing room below it

        n_text_lines = len(need_lines) + 1
        box_h = (font_title.get_height() + pad  # title
                 + n_text_lines * (line_h + 2)  # text rows
                 + (line_h + 2)  # "Need Fulfilled" header
                 + pad * 2 - (0 if need_lines else 18))
        box_w = max(160, _scale(200, self.surface))

        mx, my = pygame.mouse.get_pos()
        tx = mx + 14
        ty = my - box_h // 2
        canvas_w = self.canvas_rect().width
        if tx + box_w > canvas_w:
            tx = mx - box_w - 10
        ty = max(4, min(ty, self.surface.get_height() - box_h - 4))

        # Background
        box = pygame.Rect(tx, ty, box_w, box_h)
        pygame.draw.rect(self.surface, (255, 255, 255), box, border_radius=8)
        pygame.draw.rect(self.surface, (180, 180, 180), box, width=1, border_radius=8)

        # Title
        y = ty + pad
        title_surf = font_title.render(title_text, True, (30, 30, 30))
        self.surface.blit(title_surf, (tx + pad, y))
        y += font_title.get_height() + 4

        # Divider
        pygame.draw.line(self.surface, (200, 200, 200),
                         (tx + pad, y), (tx + box_w - pad, y), 1)
        y += 6

        if need_lines:
            needs_title = font_body.render("Needs:", True, (0, 0, 0))
            self.surface.blit(needs_title, (tx + pad, y))
            y += line_h + 2

            # Each entry: (display_name, sub_label, amount)
            for display_name, sub_label, amount in need_lines:
                label = font_body.render(f"{display_name} — {sub_label}: {amount}", True, (60, 60, 60))
                self.surface.blit(label, (tx + pad, y))
                y += line_h + 2

            # One overall progress bar.
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

    def _pos_scale(self) -> float:
        """
        Uniform scale factor that maps world-space node positions (designed for
        a 1200x900 canvas) to the current canvas size. Using the smaller axis
        keeps nodes on-screen when the window is narrow or short.
        """
        canvas = self.canvas_rect()
        return min(canvas.width / 1200, self.surface.get_height() / 900)

    def _to_screen(self, pos):
        cx = self.canvas_rect().width  / 2
        cy = self.surface.get_height() / 2
        s  = self._pos_scale()
        return (int(pos[0] * s + cx), int(pos[1] * s + cy))

    def _node_radius(self, node) -> int:
        """Return the scaled pixel radius for a node."""
        base = _scale(BASE_NODE_RADIUS, self.surface)
        per_level = _scale(NODE_RADIUS_PER_LEVEL, self.surface)
        return base + node.level * per_level

    def _node_at(self, nodes, screen_pos):
        for node in nodes:
            sp = self._to_screen(node.position)
            radius = self._node_radius(node)
            if math.hypot(screen_pos[0] - sp[0], screen_pos[1] - sp[1]) <= radius + 4:
                return node
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
        pair_map   = self._gather_connection_pairs(nodes)
        drawn_keys = set()
        for node in nodes:
            for conn in node.connections:
                key = frozenset([id(conn.nodes[0]), id(conn.nodes[1])])
                if key in drawn_keys:
                    continue
                drawn_keys.add(key)
                connections = pair_map[key]
                n = len(connections)
                for i, c in enumerate(connections):
                    offset = (i - (n - 1) / 2) * CONNECTION_OFFSET
                    p1 = self._to_screen(c.nodes[0].position)
                    p2 = self._to_screen(c.nodes[1].position)
                    op1, op2 = self._offset_line(p1, p2, offset)
                    style = self._connection_style(c.type)
                    color = style.get("color", (100, 100, 100))
                    width = max(1, BASE_CONNECTION_WIDTH + c.level * CONNECTION_WIDTH_PER_LEVEL)
                    if style.get("dash"):
                        self._draw_dashed_line(color, op1, op2, width,
                                               style.get("dash") if isinstance(style.get("dash"), int) else 10)
                    else:
                        pygame.draw.line(self.surface, color, op1, op2, width)

    def _draw_preview(self, nodes):
        if self.selected_node is None:
            return
        p1 = self._to_screen(self.selected_node.position)
        mx, my = pygame.mouse.get_pos()
        p2 = (mx, my) if self.hovered_node is None else self._to_screen(self.hovered_node.position)
        self._draw_dashed_line(C_PREVIEW, p1, p2, 1, 8)

    def _draw_nodes(self, nodes):
        for node in nodes:
            sp     = self._to_screen(node.position)
            radius = self._node_radius(node)
            color  = self._node_color(node.nodeType)

            if node is self.selected_node:
                pygame.draw.circle(self.surface, C_SELECT_RING, sp, radius + 6, 2)
            elif node is self.hovered_node and self.selected_node is not None:
                pygame.draw.circle(self.surface, (200, 200, 255), sp, radius + 5, 2)

            pygame.draw.circle(self.surface, color, sp, radius)

    # --- Panel --------------------------------------------------------

    def _draw_panel(self):
        sw = self.surface.get_width()
        sh = self.surface.get_height()

        pw      = self._panel_width()
        pad     = self._panel_padding()
        btn_h   = self._btn_height()
        btn_gap = self._btn_gap()
        lvl_h   = self._level_box_h()

        # Rebuild fonts each frame so they stay sharp after resize.
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

        # ── Title ──
        lbl = font_md.render("new connection", True, C_BTN_TEXT)
        self.surface.blit(lbl, (x, y))
        y += lbl.get_height() + pad // 2

        # ── Type buttons ──
        lbl = font_sm.render("type", True, C_HINT)
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

        # ── Level ──
        lbl = font_sm.render("level  (scroll to adjust)", True, C_HINT)
        self.surface.blit(lbl, (x, y))
        y += lbl.get_height() + 4

        lvl_rect = pygame.Rect(x, y, bw, lvl_h)
        pygame.draw.rect(self.surface, C_LEVEL_BG, lvl_rect, border_radius=6)

        minus = font_lg.render("−", True, C_HINT)
        self.surface.blit(minus, minus.get_rect(midleft=(x + pad, lvl_rect.centery)))

        num = font_lg.render(str(self.active_level), True, C_LEVEL_TEXT)
        self.surface.blit(num, num.get_rect(center=lvl_rect.center))

        plus = font_lg.render("+", True, C_HINT)
        self.surface.blit(plus, plus.get_rect(midright=(x + bw - pad, lvl_rect.centery)))
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

    _CONNECTION_HIT_RADIUS = 8  # px from midpoint to trigger hover

    def _connection_at(self, nodes: list, screen_pos):
        """Return the connection whose screen-space midpoint is closest to
        screen_pos (within _CONNECTION_HIT_RADIUS), or None."""
        best_conn = None
        best_dist = self._CONNECTION_HIT_RADIUS + 1
        seen = set()
        for node in nodes:
            for conn in node.connections:
                if id(conn) in seen:
                    continue
                seen.add(id(conn))
                p1 = self._to_screen(conn.nodes[0].position)
                p2 = self._to_screen(conn.nodes[1].position)
                mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
                dist = math.hypot(screen_pos[0] - mid[0], screen_pos[1] - mid[1])
                if dist < best_dist:
                    best_dist = dist
                    best_conn = conn
        return best_conn

    def _draw_connection_tooltip(self):
        """Draw a tooltip for self.hovered_conn near the mouse cursor."""
        conn = self.hovered_conn
        if conn is None:
            return

        font_title = _font(25, self.surface, bold=True)
        font_body = _font(20, self.surface)
        pad = 10
        bar_h = max(4, _scale(5, self.surface))
        line_h = font_body.get_height()

        cap_people, cap_goods = conn.capacity
        load_people, load_goods = conn.load

        load_people = cap_people - load_people
        load_goods = cap_goods - load_goods

        title_text = conn.type.name.capitalize()

        # 1 title + 1 level line + 2×(label + bar) rows
        box_h = (font_title.get_height() + pad
                 + 6
                 + (line_h + 2)  # "Level: x"
                 + 2 * (line_h + 2 + bar_h + 6)  # "People:" + bar, "Goods:" + bar
                 + pad)
        box_w = max(180, _scale(210, self.surface))

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

        # Title
        title_surf = font_title.render(title_text, True, (30, 30, 30))
        self.surface.blit(title_surf, (tx + pad, y))
        y += font_title.get_height() + 4

        # Divider
        pygame.draw.line(self.surface, (200, 200, 200),
                         (tx + pad, y), (tx + box_w - pad, y), 1)
        y += 6

        # Level
        level_surf = font_body.render(f"Level: {conn.level}", True, (60, 60, 60))
        self.surface.blit(level_surf, (tx + pad, y))
        y += line_h + 2

        # Resource rows: label then bar
        bar_total_w = box_w - pad * 2
        for label, load, cap in [("People", load_people, cap_people),
                                 ("Goods", load_goods, cap_goods)]:
            lbl_surf = font_body.render(f"{label}:", True, (60, 60, 60))
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