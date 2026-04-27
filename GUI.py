import pygame
import math


NODE_TYPE_COLORS: dict[str, tuple[int, int, int]] = {
    "City Center": (0, 0, 255),
    "Residential": (0, 255, 0),
    "Commercial": (255, 0, 0),
}

# Registry of available connection types for the UI.
# Add new types here; the panel will pick them up automatically.
CONNECTION_TYPES: list[dict] = [
    {"name": "highway", "color": (0, 0, 0),    "dash": True},
    {"name": "subway",  "color": (80, 80, 80),  "dash": False},
    {"name": "rail",    "color": (120, 60, 180), "dash": True},
]

CONNECTION_TYPE_STYLES: dict[str, dict] = {t["name"]: t for t in CONNECTION_TYPES}

BASE_NODE_RADIUS      = 10
NODE_RADIUS_PER_LEVEL = 5
BASE_CONNECTION_WIDTH      = 2
CONNECTION_WIDTH_PER_LEVEL = 1
CONNECTION_OFFSET = 6

PANEL_WIDTH   = 200
PANEL_PADDING = 14
BTN_HEIGHT    = 36
BTN_GAP       = 8
LEVEL_BOX_H   = 48

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


class GUI:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.font_md = pygame.font.SysFont(pygame.font.get_default_font(), 20)
        self.font_sm = pygame.font.SysFont(pygame.font.get_default_font(), 16)
        self.font_lg = pygame.font.SysFont(pygame.font.get_default_font(), 28)

        # Interaction state
        self.selected_node   = None   # first node clicked when building a connection
        self.active_type_idx = 0      # index into CONNECTION_TYPES
        self.active_level    = 1      # current level for new connections
        self.hovered_node    = None   # node under the mouse cursor

        # Button rects (built in _draw_panel, used for hit-testing)
        self._type_btn_rects: list[pygame.Rect] = []

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def canvas_rect(self) -> pygame.Rect:
        """Area of the surface reserved for the game world."""
        w = self.surface.get_width()
        h = self.surface.get_height()
        return pygame.Rect(0, 0, w - PANEL_WIDTH, h)

    def handle_event(self, event, nodes, on_connect):
        """
        Process a pygame event and call on_connect(node_a, node_b, type_name, level)
        when the user completes a connection gesture.

        Returns True if the event was consumed.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            # --- Panel type buttons ---
            for i, rect in enumerate(self._type_btn_rects):
                if rect.collidepoint(pos):
                    self.active_type_idx = i
                    return True

            # --- Canvas click ---
            if self.canvas_rect().collidepoint(pos):
                if event.button == 1:
                    clicked = self._node_at(nodes, pos)
                    if clicked is None:
                        self.selected_node = None
                    elif self.selected_node is None:
                        self.selected_node = clicked
                    elif clicked is self.selected_node:
                        self.selected_node = None          # deselect
                    else:
                        type_name = CONNECTION_TYPES[self.active_type_idx]["name"]
                        on_connect(self.selected_node, clicked, type_name, self.active_level)
                        self.selected_node = None
                    return True
                elif event.button == 3:                    # right-click cancels
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
            else:
                self.hovered_node = None

        return False

    def update(self, nodes: list):
        self.surface.fill(C_BG)
        canvas = self.canvas_rect()

        # Clip drawing to the canvas region
        old_clip = self.surface.get_clip()
        self.surface.set_clip(canvas)

        self._draw_connections(nodes)
        self._draw_preview(nodes)
        self._draw_nodes(nodes)

        self.surface.set_clip(old_clip)
        self._draw_panel()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _to_screen(self, pos):
        cx = self.canvas_rect().width  / 2
        cy = self.surface.get_height() / 2
        return (int(pos[0] + cx), int(pos[1] + cy))

    def _node_at(self, nodes, screen_pos):
        for node in nodes:
            sp = self._to_screen(node.position)
            radius = BASE_NODE_RADIUS + node.level * NODE_RADIUS_PER_LEVEL
            if math.hypot(screen_pos[0] - sp[0], screen_pos[1] - sp[1]) <= radius + 4:
                return node
        return None

    # --- Connection drawing helpers (unchanged from original) ----------

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
            s = (start[0] + dx * i / steps,           start[1] + dy * i / steps)
            e = (start[0] + dx * min(i+1, steps) / steps, start[1] + dy * min(i+1, steps) / steps)
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
                        self._draw_dashed_line(color, op1, op2, width, style.get("dash") if isinstance(style.get("dash"), int) else 10)
                    else:
                        pygame.draw.line(self.surface, color, op1, op2, width)

    def _draw_preview(self, nodes):
        """Dotted preview line from selected node to mouse / hovered node."""
        if self.selected_node is None:
            return
        p1 = self._to_screen(self.selected_node.position)
        mx, my = pygame.mouse.get_pos()
        p2 = (mx, my) if self.hovered_node is None else self._to_screen(self.hovered_node.position)
        self._draw_dashed_line(C_PREVIEW, p1, p2, 1, 8)

    def _draw_nodes(self, nodes):
        for node in nodes:
            sp     = self._to_screen(node.position)
            radius = BASE_NODE_RADIUS + node.level * NODE_RADIUS_PER_LEVEL
            color  = self._node_color(node.nodeType)

            # Selection ring
            if node is self.selected_node:
                pygame.draw.circle(self.surface, C_SELECT_RING, sp, radius + 6, 2)

            # Hover ring
            elif node is self.hovered_node and self.selected_node is not None:
                pygame.draw.circle(self.surface, (200, 200, 255), sp, radius + 5, 2)

            pygame.draw.circle(self.surface, color, sp, radius)

    # --- Panel --------------------------------------------------------

    def _draw_panel(self):
        sw = self.surface.get_width()
        sh = self.surface.get_height()
        px = sw - PANEL_WIDTH
        panel_rect = pygame.Rect(px, 0, PANEL_WIDTH, sh)

        pygame.draw.rect(self.surface, C_PANEL_BG,  panel_rect)
        pygame.draw.line(self.surface, C_PANEL_EDGE, (px, 0), (px, sh), 1)

        x  = px + PANEL_PADDING
        bw = PANEL_WIDTH - PANEL_PADDING * 2
        y  = 14

        # ── Title ──
        lbl = self.font_md.render("new connection", True, C_BTN_TEXT)
        self.surface.blit(lbl, (x, y))
        y += 28

        # ── Type buttons ──
        lbl = self.font_sm.render("type", True, C_HINT)
        self.surface.blit(lbl, (x, y))
        y += 16

        self._type_btn_rects = []
        for i, ct in enumerate(CONNECTION_TYPES):
            rect = pygame.Rect(x, y, bw, BTN_HEIGHT)
            self._type_btn_rects.append(rect)
            active = (i == self.active_type_idx)
            pygame.draw.rect(self.surface, C_BTN_ACTIVE if active else C_BTN, rect, border_radius=6)
            tc = C_BTN_TEXT_A if active else C_BTN_TEXT
            t  = self.font_md.render(ct["name"], True, tc)
            self.surface.blit(t, t.get_rect(center=rect.center))
            y += BTN_HEIGHT + BTN_GAP

        y += 4

        # ── Level ──
        lbl = self.font_sm.render("level  (scroll to adjust)", True, C_HINT)
        self.surface.blit(lbl, (x, y))
        y += 16

        lvl_rect = pygame.Rect(x, y, bw, LEVEL_BOX_H)
        pygame.draw.rect(self.surface, C_LEVEL_BG, lvl_rect, border_radius=6)

        minus = self.font_lg.render("−", True, C_HINT)
        self.surface.blit(minus, minus.get_rect(midleft=(x + 10, lvl_rect.centery)))

        num = self.font_lg.render(str(self.active_level), True, C_LEVEL_TEXT)
        self.surface.blit(num, num.get_rect(center=lvl_rect.center))

        plus = self.font_lg.render("+", True, C_HINT)
        self.surface.blit(plus, plus.get_rect(midright=(x + bw - 10, lvl_rect.centery)))
        y += LEVEL_BOX_H + 12

        # ── Status ──
        if self.selected_node is not None:
            status_color = C_STATUS_WAIT
            lines = ["node selected —", "click another to connect"]
        else:
            status_color = C_STATUS_OK
            lines = ["click a node to", "start a connection"]

        status_h = 52
        srect = pygame.Rect(x, y, bw, status_h)
        pygame.draw.rect(self.surface, status_color, srect, border_radius=6)
        for j, line in enumerate(lines):
            t = self.font_sm.render(line, True, C_STATUS_TEXT)
            self.surface.blit(t, t.get_rect(centerx=srect.centerx, y=srect.y + 10 + j * 18))
        y += status_h + 10

        # ── Hint ──
        hint = self.font_sm.render("esc / right-click: cancel", True, C_HINT)
        self.surface.blit(hint, hint.get_rect(centerx=px + PANEL_WIDTH // 2, y=y))