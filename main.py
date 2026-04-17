from Node import Node
import util, pygame, GUI
import numpy as np

GAME_TICK = pygame.event.custom_type()
MONEY_SCALAR = 0.01

class Game:
    def __init__(self):
        self.nodes = [Node(util.nodeTypes["center"], (0, 0))]
        self.money = 1000
        self.newNodeTimer = 0
        self.gui = GUI.GUI()

        pygame.init()

    def loop(self):
        # If you need to touch this, read up on pygame events first so ya don't break stuff
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

            if event.type == GAME_TICK:
                self.gameTick()
        pass

    def gameTick(self):
        satisfied_demand = []
        for node in self.nodes:
            node.tick()
            satisfied_demand.append(node.demandMet())

        metDemands, totalDemands = zip(*satisfied_demand)

        demand_mult = (np.sum(metDemands) / np.sum(totalDemands)) ** 3
        totalDemand = np.sum(totalDemands)

        self.money += totalDemand * demand_mult * MONEY_SCALAR

        self.gui.update(self.money, self.nodes)

if __name__ == "__main__":
    game = Game()

    gameTickEvent = pygame.event.Event(GAME_TICK)
    pygame.time.set_timer(gameTickEvent, 10)
    while True:
        game.loop()
