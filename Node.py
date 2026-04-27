from util import NodeType

class Node:
    def __init__(self, nodeType: NodeType, position):
        self.nodeType = nodeType
        self.connections = []
        self.position = position
        self.level = 1
        self.needs = nodeType.needs
        self.maxPeople = nodeType.maxPeople

    def tick(self):
        for destination in self.needs:
            amount = self.needs[destination]
            pass
            # TODO: Search alg for amount of needs met (needs to include indirect travel & interchanges)

    def levelUp(self, amount):
        self.level += amount
        self.needs = {key: (x * self.level for x in val) for key, val in self.nodeType.needs.items()}
        self.maxPeople = self.maxPeople * self.level

    def needsMet(self):
        return (1, 1) # temp, return tuple with (met needs, total needs)

    def capacityUsed(self):
        return 1.0 # temp, return % of max people used (ex: 4/5 should return 0.8)
