import util
from Node import Node
from Connection import Connection
from util import *
import random, pygame, GUI
from NodeManagment import *
import numpy as np
import copy


GAME_TICK = pygame.event.custom_type()
MONEY_SCALAR = 0.01

NEW_NODE_COOLDOWN = 500000
NEW_NODE_ODDS = 0.1

LEVEL_UP_COOLDOWN = 500000
LEVEL_UP_ODDS = 0.15

class Game:
    def __init__(self):
        pygame.init()
        self.nodes = [Node(util.nodeTypes["center"], (0, 0)), Node(util.nodeTypes["residential"], (-100, 0)), Node(util.nodeTypes["market"], (-50, 50)), Node(util.nodeTypes["industry"], (50, 50))]
        self.money = 1000
        self.newNodeTimer = 0
        self.levelUpTimer = 0
        self.surface = pygame.display.set_mode((1200, 900), pygame.RESIZABLE | pygame.SCALED)
        self.title = GUI.TitleScreen(self.surface)
        self.gui = None
        self.sketchystoringmutnodes = self.nodes

    def loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if not self.title.started:
                self.title.handle_event(event)
            else:
                self.gui.handle_event(event, self.nodes, self._add_connection)

            if event.type == GAME_TICK:
                if self.title.started:
                    self.gameTick()

        if self.gui is None and self.title.started:
            self.gui = GUI.GUI(self.surface)

        if not self.title.started:
            self.title.update()
        else:
            self.gui.update(self.nodes)

        pygame.display.flip()

    def gameTick(self):
        satisfied_demand = []
        mut_nodes = copy.deepcopy(self.nodes)
        for node in mut_nodes:
            node.tick()
            satisfied_demand.append(node.ratioNeedsMet())

        metDemands, totalDemands = zip(*satisfied_demand)

        print(sum(metDemands), sum(totalDemands))

        demand_mult = (np.sum(metDemands) / np.sum(totalDemands)) ** 3
        totalDemand = np.sum(totalDemands)

        self.money += totalDemand * demand_mult * MONEY_SCALAR

        self.newNodeTimer += 1
        if self.newNodeTimer > NEW_NODE_COOLDOWN and random.random() <= NEW_NODE_ODDS:
            addNode(self.nodes)
            self.newNodeTimer = 0

        self.levelUpTimer += 1
        if self.levelUpTimer > LEVEL_UP_COOLDOWN and random.random() <= LEVEL_UP_ODDS:
            levelUpNode(self.nodes)
            self.levelUpTimer = 0

    def _add_connection(self, node_a, node_b, type_name, level):
        print("Add connection")
        conn = Connection([node_a, node_b], util.connectionTypes[type_name], level)
        node_a.connections.append(conn)
        node_b.connections.append(conn)

if __name__ == "__main__":
    game = Game()

    gameTickEvent = pygame.event.Event(GAME_TICK)
    pygame.time.set_timer(gameTickEvent, 10)
    while True:
        game.loop()