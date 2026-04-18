from Node import Node
from Connection import Connection
from util import *
import util, pygame, GUI
import numpy as np

GAME_TICK = pygame.event.custom_type()
MONEY_SCALAR = 0.01

class Game:
    def __init__(self):
        pygame.init()
        self.nodes = [Node(util.nodeTypes["center"], (0, 0)), Node(util.nodeTypes["residential"], (-100, 0))]
        self.money = 1000
        self.newNodeTimer = 0
        self.gui = GUI.GUI(pygame.display.set_mode((480, 480), pygame.RESIZABLE))

    def loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if self.gui.handle_event(event, self.nodes, self._add_connection):
                continue

            if event.type == GAME_TICK:
                self.gameTick()

    def gameTick(self):
        satisfied_demand = []
        for node in self.nodes:
            node.tick()
            satisfied_demand.append(node.demandMet())

        metDemands, totalDemands = zip(*satisfied_demand)

        demand_mult = (np.sum(metDemands) / np.sum(totalDemands)) ** 3
        totalDemand = np.sum(totalDemands)

        self.money += totalDemand * demand_mult * MONEY_SCALAR

        self.gui.update(self.nodes)
        pygame.display.flip()

    def _add_connection(self, node_a, node_b, type_name, level):
        conn_type = ConnectionType(type_name, None)
        conn = Connection([node_a, node_b], conn_type, level)
        node_a.connections.append(conn)
        node_b.connections.append(conn)

if __name__ == "__main__":
    game = Game()

    gameTickEvent = pygame.event.Event(GAME_TICK)
    pygame.time.set_timer(gameTickEvent, 10)
    while True:
        game.loop()
