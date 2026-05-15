from util import NodeType

class Node:
    def __init__(self, nodeType: NodeType, position): #
        self.transit = False
        self.satisfied = True
        self.nodeType = nodeType
        self.connections = [] # connections to transit options
        self.position = position
        self.level = 1
        self.needs = nodeType.needs
        self.supply = nodeType.max_supply
        self.name = nodeType.name[0]

    def tick(self):
        self.satisfied = True
        for destination in self.needs:
            amount = self.needs[destination]
            if amount[0] == 0 and amount[1] == 0:
                continue

            people_satisfied = False
            goods_satisfied = False
            queue = [(self, [self])]
            visited = set()

            while queue:
                node, path = queue.pop(0)
                if node != self and node.name[0] == destination:
                    path_connections = []
                    for i in range(len(path) - 1):
                        a, b = path[i], path[i + 1]
                        for connection in a.connections:
                            if (connection.nodes[0] == a and connection.nodes[1] == b) or (connection.nodes[0] == b and connection.nodes[1] == a):
                                path_connections.append(connection)
                                break

                    if all(c.load[0] >= amount[0] for c in path_connections):
                        for c in path_connections:
                            temp = list(c.load)
                            temp[0] -= amount[0]
                            c.load = tuple(temp)
                        people_satisfied = True
                    if all(c.load[1] >= amount[1] for c in path_connections):
                        for c in path_connections:
                            temp = list(c.load)
                            temp[1] -= amount[1]
                            c.load = tuple(temp)
                        goods_satisfied = True
                    break

                for connection in node.connections:
                    if connection.load[0] < amount[0] or connection.load[1] < amount[1]:
                        continue
                    if connection not in visited:
                        neighbor = connection.nodes[1] if connection.nodes[0] == node else connection.nodes[0]
                        if neighbor not in visited:
                            queue.append((neighbor, path + [neighbor]))
                            visited.add(neighbor)

            if not people_satisfied or not goods_satisfied:
                self.satisfied = False

            # TODO: Search alg for amount of needs met (needs to include indirect travel & interchanges)

    def levelUp(self, amount):
        self.level += amount
        self.needs = {key: [x * self.level for x in val] for key, val in self.nodeType.needs.items()}
        self.supply = self.supply * self.level

    def needsMet(self):
        return (1, 1) # temp, return tuple with (met needs, total needs)