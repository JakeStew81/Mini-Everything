import util
from Node import Node
from Connection import Connection
from util import *
import random, pygame, GUI
from NodeManagment import *
import numpy as np
import copy, math

GAME_TICK = pygame.event.custom_type()
MONEY_SCALAR = 0.08

NEW_NODE_COOLDOWN_MIN = 300
NEW_NODE_COOLDOWN_STEP = 25
NEW_NODE_ODDS_MAX = 0.75
NEW_NODE_ODDS_STEP = 0.05

LEVEL_UP_COOLDOWN_MIN = 200
LEVEL_UP_COOLDOWN_STEP = 25
LEVEL_UP_ODDS_MAX = 0.75
LEVEL_UP_ODDS_STEP = 0.1

CONNECTION_COSTS = { # $million per mile per level
    "Passenger Rail": 75,
    "Freight Rail": 15,
    "Highway": 10
}

CONNECTION_UPKEEP_COSTS = { # $million per mile per day per level
    "Passenger Rail": 0.0125,
    "Freight Rail": 0.05 / 365.0,
    "Highway": 0.035 / 365.0
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
        out_conn = Connection([self.nodes[0], self.nodes[7]], util.connectionTypes["Highway"], 6)
        self.nodes[0].connections.append(out_conn)
        self.nodes[7].connections.append(out_conn)
        self.money = 650
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
        self.days = 0
        self.new_node_cooldown = 700
        self.new_node_odds = 0.1
        self.level_up_cooldown = 600
        self.level_up_odds = 0.15

    def loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if not self.title.started:
                self.title.handle_event(event)
            else:
                self.gui.handle_event(event, self.nodes, self._add_connection, self._upgrade_connection)

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

        demand_mult = (((sum(metDemands) / sum(totalDemands)) ** 1.25) - 0.5)
        print(demand_mult)
        totalDemand = np.sum(totalDemands) + 10

        connections = []
        for node in self.nodes:
            for connection in node.connections:
                if connection not in connections:
                    connections.append(connection)

        operatingCost = 0.02
        for connection in connections:
            operatingCost += (CONNECTION_UPKEEP_COSTS[connection.type.name] * connection.level
                            * self.calculate_connection_length(connection))

        self.moneyPerTick = (totalDemand * demand_mult * MONEY_SCALAR) - operatingCost
        self.money += self.moneyPerTick

        self.newNodeTimer += 1
        if self.newNodeTimer > self.new_node_cooldown and random.random() <= self.new_node_odds:
            addNode(self.nodes)
            self.newNodeTimer = 0
            if self.new_node_cooldown > NEW_NODE_COOLDOWN_MIN:
                self.new_node_cooldown -= NEW_NODE_COOLDOWN_STEP
            if self.new_node_odds > NEW_NODE_ODDS_MAX:
                self.new_node_odds += NEW_NODE_ODDS_STEP

        self.levelUpTimer += 1
        if self.levelUpTimer > self.level_up_cooldown and random.random() <= self.level_up_odds:
            levelUpNode(self.nodes)
            self.levelUpTimer = 0
            if self.level_up_cooldown > LEVEL_UP_COOLDOWN_MIN:
                self.level_up_cooldown -= LEVEL_UP_COOLDOWN_STEP
            if self.level_up_odds > LEVEL_UP_ODDS_MAX:
                self.level_up_odds += LEVEL_UP_ODDS_STEP

        if self.money <= 0:
            self.loseScreen = True
            res = self.gui.show_lose_screen(self.days)
            if res:
                self.gameOver = True
            else:
                pygame.quit()

        self.days += 1

    def _add_connection(self, node_a, node_b, type_name, level):
        conn = Connection([node_a, node_b], util.connectionTypes[type_name], level)
        cost = self.calculate_connection_length(conn) * CONNECTION_COSTS[type_name] * level
        if cost <= self.money:
            self.money -= cost
            node_a.connections.append(conn)
            node_b.connections.append(conn)
            return True
        else:
            return False

    def _upgrade_connection(self, conn):
        cost = self.calculate_connection_length(conn) * CONNECTION_COSTS[conn.type.name]
        if cost <= self.money:
            self.money -= cost
            conn.upgrade()
            return True
        else:
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