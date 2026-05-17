class Connection:
    def __init__(self, nodes, type, level):
        self.transit = True
        self.nodes = nodes # [node_a, node_b]
        self.type = type
        self.level = level
        self.capacity = self.type.capacity
        self.load = type.capacity


    def upgrade(self):
        self.level += 1
        self.capacity += self.type.capacity