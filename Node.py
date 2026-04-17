class Node:
    def __init__(self, type, position):
        self.type = type
        self.connections = []
        self.level = 1

    def tick(self):
        for demand in self.type.demands:
            pass
            # TODO: Search alg for amount of demand met (needs to include indirect travel & interchanges)

    def demandMet(self):
        return (1, 1) # temp, return tuple with (met demand, total demand)