from asyncio.windows_events import NULL

from util import NodeType

class Node:
    def __init__(self, nodeType: NodeType, position): #
        self.nodeType = nodeType
        self.connections = [] # connections to transit options
        self.position = position
        self.level = 1
        self.needs = nodeType.needs
        self.supply = nodeType.max_supply
        self.name = nodeType.name[0]
        self._needsMet = (0,0)

    def tick(self):
        needs_met = (0,0)
        for destination in self.needs:
            original_need = list(self.needs[destination]) # for print
            amount_prev = list(self.needs[destination])
            temp1 = list(needs_met)
            temp1[1] += amount_prev[0] + amount_prev[1]

            while amount_prev[0] > 0 or amount_prev[1] > 0:
                amount_now = list(amount_prev)
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

                        if all(c.load[0] >= 1 for c in path_connections):
                            for c in path_connections:
                                temp = list(c.load)
                                temp[0] -= 1
                                c.load = tuple(temp)
                            amount_now[0] -= 1
                        if all(c.load[1] >= 1 for c in path_connections):
                            for c in path_connections:
                                temp = list(c.load)
                                temp[1] -= 1
                                c.load = tuple(temp)
                            amount_now[1] -= 1
                        break

                    for connection in node.connections:
                        if connection.load[0] < 1 or connection.load[1] < 1:
                            continue
                        if connection not in visited:
                            neighbor = connection.nodes[1] if connection.nodes[0] == node else connection.nodes[0]
                            if neighbor not in visited:
                                queue.append((neighbor, path + [neighbor]))
                                visited.add(neighbor)

                if amount_prev[0] == amount_now[0] and amount_prev[1] == amount_now[1]:
                    break
                amount_prev = (amount_now[0], amount_now[1])

            temp1[0] += (original_need[0] - amount_prev[0] + original_need[1] - amount_prev[1]) // 2
            needs_met = tuple(temp1)
            self._needsMet = needs_met

    def levelUp(self, amount):
        self.level += amount
        self.needs = {key: [x * self.level for x in val] for key, val in self.nodeType.needs.items()}
        self.supply = self.supply * self.level

    def ratioNeedsMet(self):
        return self._needsMet # temp, return tuple with (met needs, total needs)