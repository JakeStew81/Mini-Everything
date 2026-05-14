class NodeType:
    def __init__(self, name: str, displayName: str, needs: dict[str, tuple[int, int]], max_supply: tuple[int, int]):
        # For tuples, format is (people, goods)
        self.name = name
        self.displayName = displayName
        self.needs = needs
        self.max_supply = max_supply

class ConnectionType:
    def __init__(self, name: str, capacity: tuple[int, int]):
        self.name = name
        self.capacity = capacity

nodeTypes = {
    "center": NodeType("center", "City Center",
                       {"c": (0, 0), "r": (0, 0), "m": (0, 0), "i": (0, 0), "o": (0, 0)},
                       (9999, 9999)),
    "residential": NodeType("residential", "Residential",
                            {"c": (1, 0), "r": (0, 0), "m": (2, 0), "i": (0, 0), "o": (0, 0)}, # changed out people to zero for the sake of testing
                            (2, 9999)),
    "market": NodeType("market", "Commercial",
                       {"c": (0, 0), "r": (0, 0), "m": (0, 0), "i": (0, 2), "o": (0, 2)},
                       (10, 9999)),
    "industry": NodeType("industrial", "Industrial",
                         {"c": (0, 0), "r": (2, 0), "m": (0, 0), "i": (0, 0), "o": (0, 2)},
                         (2,9999)),
    "junction": NodeType("junction", "Junction",
                         {"c": (0, 0), "r": (0, 0), "m": (0, 0), "i": (0, 0), "o": (0, 0)},
                         (9999,9999)),
    "out": NodeType("Outside of City", "OUT",
                    {"c": (0, 0), "r": (0, 0), "m": (0, 0), "i": (0, 0), "o": (0, 0)},
                    (9999, 9999)),
}  # TODO: Fill out properly with good values & stuff. Temp values for testing rn.
    # I switched out max people for max supply so that we can track both goods and people for that in which it is required
    # The values are 9999 because idk what they should be, and it seems like you want to do the balance so like -.- you know?

connectionTypes = {
    "road": ConnectionType("Highway", (2, 2)),
    "train": ConnectionType("Freight Rail", (0, 4)),
    "metro": ConnectionType("Subway", (4, 0))
} # TODO: Fill out properly with good values & stuff. Temp values for testing rn.
# Needs & capacity is in amount/tick, 100 ticks/s