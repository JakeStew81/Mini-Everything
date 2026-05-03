from asyncio.windows_events import NULL

from util import NodeType

class Node:
    def __init__(self, nodeType: NodeType, position, UID):
        self.UID = UID
        self.transit = False
        self.satisfied = True
        self.nodeType = nodeType
        self.connections = [] # connections to transit options
        self.position = position
        self.level = 1
        self.needs = nodeType.needs
        self.supply = nodeType.max_supply

    def tick(self):
        for destination in self.needs:
            amount = self.needs[destination]
            if amount[0] == 0 and amount[1] == 0:
                continue

            people_satisfied = False
            goods_satisfied = False
            queue = [self]
            visited = [self.UID]

            while queue:
                node = queue.pop(0)
                for connection in node.connections:
                    if connection.UID not in visited:
                        visited.append(connection.UID)
                        queue.append(connection)
                if node.transit:
                    continue
                    # TODO: wait for jake to make a good connection class before attempting to do anything with transit
                else:
                    if node.nodeType == destination:
                        if node.supply[0] > amount[0] and not people_satisfied:
                            node.supply[0] -= amount[0]
                            people_satisfied = True
                        if node.supply[1] > amount[1] and not goods_satisfied:
                            node.supply[1] -= amount[1]
                            goods_satisfied = True
            if (not people_satisfied or not goods_satisfied):
                self.satisfied = False

        print(self.UID, self.satisfied)

            # TODO: Search alg for amount of needs met (needs to include indirect travel & interchanges)
    '''
    you have to fix this shit -.- i don't think it should be that hard but you did it the first time so just want to make sure that it is how you like it.

    def levelUp(self, amount):
        self.level += amount
        self.needs = {key: (x * self.level for x in val) for key, val in self.nodeType.needs.items()}
        self.maxPeople = self.maxPeople * self.level

    def needsMet(self):
        return (1, 1) # temp, return tuple with (met needs, total needs)

    def capacityUsed(self):
        return 1.0 # temp, return % of max people used (ex: 4/5 should return 0.8)
    '''