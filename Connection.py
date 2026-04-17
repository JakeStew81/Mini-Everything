class Connection:
    def __init__(self, nodes, type, level):
        self.nodes = nodes
        self.type = type
        self.level = level
        # Have travel time? Ppl/t is going to be pretty low, and it adds a new element of gameplay without being
        # much work. Punishes longer routes, and we could do it with basic math & an extra variable or two

    def upgrade(self):
        self.level += 1