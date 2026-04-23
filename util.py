

class Demand:
    def __init__(self, amount: int, type: str, destination: str):
        self.amount = amount
        self.type = type
        self.destination = destination

class NodeType:
    def __init__(self, name: str, demands: list[Demand]):
        self.name = name
        self.demands = demands

nodeTypes = {
    "center": NodeType("City Center", []),
    "residential": NodeType("Residential", [Demand(1, "goods", "City Center")]),
    "commercial": NodeType("Commercial", [Demand(1, "people", "Residential")]),
} # TODO: Fill out properly with good values & stuff. Temp value for testing rn.
    # Demand is in amount/tick, 100 ticks/s

class ConnectionType:
    def __init__(self, name: str, capacity: int):
        self.name = name
        self.capacity = capacity

class Capacity:
    def __init__(self, people: int, goods: int):
        self.people = people
        self.goods = goods