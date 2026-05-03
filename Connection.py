# not my problem to fix this up to you to make a proper connection class idk how you imagein this version working.

class Connection:
    def __init__(self, nodes, type, level, UID):
        self.UID = UID
        self.transit = True
        self.nodes = nodes # [node_a, node_b]
        self.type = type
        self.level = level


    def upgrade(self):
        self.level += 1