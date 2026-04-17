class Connection:
    def __init__(self, nodes, type, level):
        self.nodes = nodes
        self.type = type
        self.level = level

    def upgrade(self):
        self.level += 1