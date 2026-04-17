class Node:
    def __init__(self, type):
        self.type = type
        self.connections = []
        self.level = 1

    def loop(self):
        pass

    def satisfied_demand(self):
        pass # return % of demand satisfied