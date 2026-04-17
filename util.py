class NodeType:
    def __init__(self, name, demands, revenue):
        self.name = name
        self.demands = demands

class Demand:
    def __init__(self, amount, destination):
        self.amount = amount
        self.destination = destination

class ConnectionType:
    def __init__(self, name, capacity):
        self.name = name
        self.capacity = capacity

class Capacity:
    def __init__(self, people, goods):
        self.people = people
        self.goods = goods