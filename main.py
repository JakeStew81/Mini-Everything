import util
from Node import Node
from Connection import Connection
from util import *
import random, pygame, GUI
from NodeManagment import *
import numpy as np
import copy, math

GAME_TICK = pygame.event.custom_type()
MONEY_SCALAR = 0.18

NODE_ADVANCEMENT_ODDS = 0.00075
NODE_ADVANCEMENT_COOLDOWN_STEP = 25
NEW_NODE_ODDS = 0.3
LEVEL_UP_ODDS = 1 - NEW_NODE_ODDS

CONNECTION_COSTS = { # $million per mile per level
    "Passenger Rail": 75,
    "Freight Rail": 15,
    "Highway": 10
}

JUNCTION_COSTS = { # $million per level
    "Passenger Rail": 15,
    "Freight Rail": 0.25,
    "Highway": 6
}

CONNECTION_UPKEEP_COSTS = { # $million per mile per month per level
    "Passenger Rail": ((0.000003) * 10 * 24 * 365) / 12, # operating cost - ticket revenue
    "Freight Rail": 0.05 / 12,
    "Highway": 0.035 / 12
}

CONNECTION_UPGRADE_LIMITS = {
    "Highway": 4,
    "Passenger Rail": 3,
    "Freight Rail": 3,
}

PIXELS_PER_MILE = 10

class Game:
    def __init__(self):
        pygame.init()
        self.nodes = [
            Node(util.nodeTypes["center"], (0, 0)),
            Node(util.nodeTypes["residential"], (-80, 0)),
            Node(util.nodeTypes["market"], (80, 0)),
            Node(util.nodeTypes["industry"], (0, 80)),
            Node(util.nodeTypes["out"], (450, 0)),
            Node(util.nodeTypes["out"], (-450, 0)),
            Node(util.nodeTypes["out"], (0, 450)),
            Node(util.nodeTypes["out"], (0, -450)),
        ]
        out_conn = Connection([self.nodes[0], self.nodes[7]], util.connectionTypes["Highway"], 4)
        self.nodes[0].connections.append(out_conn)
        self.nodes[7].connections.append(out_conn)
        self.money = math.inf # 750
        self.moneyPerTick = 0
        self.newNodeTimer = 0
        self.levelUpTimer = 0
        self.surface = pygame.display.set_mode((1200, 900), pygame.RESIZABLE | pygame.SCALED)
        self.title = GUI.TitleScreen(self.surface)
        self.mut_nodes = self.nodes
        self.gui = None
        self.tick_skip_count = 0
        self.gameOver = False
        self.loseScreen = False
        self.months = 0
        self.node_advancement_cooldown = 300
        self.node_advancement_timer = 0

    def loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if not self.title.started:
                self.title.handle_event(event)
            else:
                self.gui.handle_event(event, self.nodes, self._add_connection, self._upgrade_connection, self._add_junction)

            if self.gui is None and self.title.started:
                self.gui = GUI.GUI(self.surface)

            if event.type == GAME_TICK and not self.loseScreen:
                if self.title.started and not self.gui.paused:
                    if self.gui.speed_changed:
                        self.tick_skip_count = 0
                        self.gui.speed_changed = False
                    if self.tick_skip_count >= 5 - self.gui.game_speed:
                        self.gameTick()
                        self.tick_skip_count = 0
                    else:
                        self.tick_skip_count += 1

        if not self.title.started:
            self.title.update()
        else:
            if self.gui is not None and self.gui.paused:
                for real, mut in zip(self.nodes, self.mut_nodes):
                    mut.level = real.level
                    mut.nodeType = real.nodeType
                    mut_conn_pairs = {
                        (c.nodes[0].position, c.nodes[1].position) for c in mut.connections
                    }
                    for conn in real.connections:
                        pair = (conn.nodes[0].position, conn.nodes[1].position)
                        pair_rev = (conn.nodes[1].position, conn.nodes[0].position)
                        if pair not in mut_conn_pairs and pair_rev not in mut_conn_pairs:
                            mut.connections.append(conn)

            self.gui.update(self.mut_nodes, self.money, self.moneyPerTick)

        pygame.display.flip()

    def calculate_connection_length(self, conn):
        return math.dist(conn.nodes[0].position, conn.nodes[1].position) / PIXELS_PER_MILE

    def gameTick(self):
        satisfied_demand = []
        mut_nodes = copy.deepcopy(self.nodes)
        for node in mut_nodes:
            node.tick()
            satisfied_demand.append(node.ratioNeedsMet())

        self.mut_nodes = mut_nodes

        metDemands, totalDemands = zip(*satisfied_demand)

        demand_mult = ((sum(metDemands) / sum(totalDemands)) - 0.45)
        totalDemand = np.sum(totalDemands) + 40
        totalDemand = totalDemand ** (3/4)

        connections = []
        for node in self.nodes:
            for connection in node.connections:
                if connection not in connections:
                    connections.append(connection)

        operatingCost = 0.02
        for connection in connections:
            operatingCost += (CONNECTION_UPKEEP_COSTS[connection.type.name] * connection.level
                            * self.calculate_connection_length(connection))

        self.moneyPerTick = (totalDemand * demand_mult * MONEY_SCALAR) - (operatingCost * (sum(metDemands) / sum(totalDemands)))
        self.money += self.moneyPerTick

        for node in self.nodes:
            if node.nodeType.name == "out" or node.nodeType.name == "junction":
                continue

            if random.random() <= NODE_ADVANCEMENT_ODDS and self.node_advancement_timer <= 0:
                self.node_advancement_cooldown -= NODE_ADVANCEMENT_COOLDOWN_STEP if self.node_advancement_cooldown > 150 else 150
                self.node_advancement_timer = self.node_advancement_cooldown
                if random.random() <= NEW_NODE_ODDS:
                    addNode(self.nodes)
                    break
                else:
                    levelUpNode(self.nodes)
                    break

        self.node_advancement_timer -= 1

        if self.money <= 0:
            self.loseScreen = True
            res = self.gui.show_lose_screen(self.months)
            if res:
                self.gameOver = True
            else:
                pygame.quit()

        self.months += 1

    def _add_connection(self, node_a, node_b, type_name, level):
        conn = Connection([node_a, node_b], util.connectionTypes[type_name], level)
        cost = self.calculate_connection_length(conn) * CONNECTION_COSTS[type_name] * level
        if cost <= self.money:
            self.money -= cost
            node_a.connections.append(conn)
            node_b.connections.append(conn)
            for mut in self.mut_nodes:
                if mut.position == node_a.position:
                    mut.connections.append(conn)
                elif mut.position == node_b.position:
                    mut.connections.append(conn)
            print("conn added")
            return True
        else:
            return False

    def _upgrade_connection(self, conn):
        cost = self.calculate_connection_length(conn) * CONNECTION_COSTS[conn.type.name]
        if cost <= self.money and conn.level < CONNECTION_UPGRADE_LIMITS[conn.type.name]:
            self.money -= cost
            conn.upgrade()
            return ""
        elif cost > self.money:
            return "Insufficient Funds"
        else:
            return "Max Level Reached"

    def _add_junction(self, pos: tuple[int, int], conn_type: str, from_node: Node, hovered_conn: Connection):
        junction = Node(util.nodeTypes["junction"], pos)
        conn = Connection([from_node, junction], util.connectionTypes[conn_type], 1)
        cost = self.calculate_connection_length(conn) * CONNECTION_COSTS[conn_type] + JUNCTION_COSTS[conn.type.name] * hovered_conn.level
        print("ON JUNCTION")
        if cost <= self.money:
            self.money -= cost
            from_node.connections.append(conn)
            junction.connections.append(conn)
            self.nodes.append(junction)

            hovered_conn.nodes[0].connections.remove(hovered_conn)
            hovered_conn.nodes[1].connections.remove(hovered_conn)

            firstLeg = Connection([hovered_conn.nodes[0], junction], hovered_conn.type, hovered_conn.level)
            secondLeg = Connection([junction, hovered_conn.nodes[1]], hovered_conn.type, hovered_conn.level)

            hovered_conn.nodes[0].connections.append(firstLeg)
            hovered_conn.nodes[1].connections.append(secondLeg)
            junction.connections.append(firstLeg)
            junction.connections.append(secondLeg)

            print("Called junction!!")

            return True
        else:
            print(cost)
            return False

if __name__ == "__main__":
    game = Game()

    gameTickEvent = pygame.event.Event(GAME_TICK)
    pygame.time.set_timer(gameTickEvent, 10)
    while True:
        game.loop()
        if game.gameOver:
            del game
            game = Game()