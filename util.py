class NodeType:
    def __init__(self, name, demands):
        self.name = name
        self.demands = demands

class Demand:
    def __init__(self, amount, type, destination):
        self.amount = amount
        self.type = type
        self.destination = destination

nodeTypes = {
    "center": NodeType("City Center", []),
    "residential": NodeType("Residential", [Demand(1, "goods", "City Center")]),
    "commercial": NodeType("Commercial", [Demand(1, "people", "residential")]),
} # TODO: Fill out properly with good values & stuff. Temp value for testing rn.
    # Demand is in amount/tick, 100 ticks/s

class ConnectionType:
    def __init__(self, name, capacity):
        self.name = name
        self.capacity = capacity

class Capacity:
    def __init__(self, people, goods):
        self.people = people
        self.goods = goods