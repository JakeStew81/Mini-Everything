# if there is a system for creating a new node you need to increment and pass the UID var idk if there is one I searched and found nothing

from Node import Node
from Connection import Connection
from util import *
import util, pygame, GUI
import numpy as np
import copy


GAME_TICK = pygame.event.custom_type()
MONEY_SCALAR = 0.01



class Game:
    UID = 2
    def __init__(self):
        pygame.init()
        self.nodes = [Node(util.nodeTypes["center"], (0, 0), 0), Node(util.nodeTypes["residential"], (-100, 0), 1), Node(util.nodeTypes["market"], (-50, 50), 2)]
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
        mut_nodes = copy.deepcopy(self.nodes)
        for node in mut_nodes:
            node.tick()
            satisfied_demand.append(node.needsMet())


        metDemands, totalDemands = zip(*satisfied_demand)

        demand_mult = (np.sum(metDemands) / np.sum(totalDemands)) ** 3
        totalDemand = np.sum(totalDemands)

        self.money += totalDemand * demand_mult * MONEY_SCALAR

        self.gui.update(self.nodes)
        pygame.display.flip()

    def _add_connection(self, node_a, node_b, type_name, level):
        game.UID += 1
        conn_type = ConnectionType(type_name, None)
        conn = Connection([node_a, node_b], conn_type, level, game.UID)
        node_a.connections.append(conn)
        node_b.connections.append(conn)

if __name__ == "__main__":
    game = Game()

    gameTickEvent = pygame.event.Event(GAME_TICK)
    pygame.time.set_timer(gameTickEvent, 10)
    while True:
        game.loop()
