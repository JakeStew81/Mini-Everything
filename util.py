class NodeType:
    def __init__(self, name: str, displayName: str, needs: dict[str, tuple[int, int]], maxPeople: int):
        # For tuples, format is (people, goods)
        self.name = name
        self.displayName = displayName
        self.needs = needs
        self.maxPeople = maxPeople

class ConnectionType:
    def __init__(self, name: str, capacity: tuple[int, int]):
        self.name = name
        self.capacity = capacity

nodeTypes = {
    "center": NodeType("center", "City Center",
                       {"c": (0, 0), "r": (0, 0), "m": (0, 0), "i": (0, 0), "o": (0, 0)},
                       9999),
    "residential": NodeType("residential", "Residential",
                            {"c": (1, 0), "r": (0, 0), "m": (2, 0), "i": (0, 0), "o": (1, 0)},
                            4),
    "market": NodeType("market", "Commercial",
                       {"c": (0, 0), "r": (0, 0), "m": (0, 0), "i": (0, 1), "o": (0, 1)},
                       10),
    "industry": NodeType("industry", "Industrial",
                         {"c": (1, 0), "r": (2, 0), "m": (0, 0), "i": (0, 0), "o": (0, 2)},
                         0),
    "junction": NodeType("junction", "Junction",
                         {"c": (0, 0), "r": (0, 0), "m": (0, 0), "i": (0, 0), "o": (0, 0)},
                         9999),
    "out": NodeType("out", "Outside of City",
                    {"c": (0, 0), "r": (0, 0), "m": (0, 0), "i": (0, 0), "o": (0, 0)},
                    9999),
}  # TODO: Fill out properly with good values & stuff. Temp values for testing rn.

connectionTypes = {
    "road": ConnectionType("Highway", (2, 2)),
    "train": ConnectionType("Freight Rail", (0, 4)),
    "metro": ConnectionType("Subway", (4, 0))
} # TODO: Fill out properly with good values & stuff. Temp values for testing rn.
# Needs & capacity is in amount/tick, 100 ticks/s