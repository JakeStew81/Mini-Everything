from logging import exception

from Node import Node
import random, util, math

BOUNDS = (-400, 400)

def tryTypesLevel(types: list[util.NodeType], level: int, capacityVNeeds):
    for typeToTry in types:
        tempCvN = capacityVNeeds.copy()

        for need in typeToTry.needs.values():
            if need in tempCvN:
                tempCvN[need][1] += need[0] * level

        tempCvN[typeToTry.name[0]][0] += typeToTry.max_supply[0] * level

        for nodeType in tempCvN:
            if tempCvN[nodeType][0] < tempCvN[nodeType][1]:
                print(f"TempCvN: {tempCvN}")
                break
        else:
            return typeToTry
    return None

def calculate_balance(nodes: list[Node]):
    capacityVNeeds = {
        "m": [0, 0],
        "i": [0, 0],
        "r": [0, 0]
    }

    levels = []

    for node in nodes:
        if node.nodeType.name[0] in capacityVNeeds:
            capacityVNeeds[node.nodeType.name[0]][0] += node.supply[0]
            levels.append(node.level)

        for need in node.needs:
            if need in capacityVNeeds:
                capacityVNeeds[need][1] += node.needs[need][0]

    return capacityVNeeds, levels


def point_to_segment_distance(px, py, ax, ay, bx, by):
    """Calculate minimum distance from point (px,py) to line segment (ax,ay)-(bx,by)."""
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)

    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    closest_x = ax + t * dx
    closest_y = ay + t * dy
    return math.hypot(px - closest_x, py - closest_y)


def generate_node_position(nodes, min_distance=80, search_radius=100):
    if not nodes:
        return random.uniform(*BOUNDS), random.uniform(*BOUNDS)

    # Gather all unique connections from nodes
    all_connections = {id(c): c for n in nodes for c in n.connections}.values()

    for _ in range(1000):
        anchor = random.choice(nodes)
        while anchor.nodeType.name == "out" or anchor.nodeType.name == "junction":
            anchor = random.choice(nodes)
        ax, ay = anchor.position

        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(min_distance, search_radius)
        x = ax + math.cos(angle) * distance
        y = ay + math.sin(angle) * distance

        if not (BOUNDS[0] <= x <= BOUNDS[1] and BOUNDS[0] <= y <= BOUNDS[1]):
            continue

        if not all(math.hypot(x - n.position[0], y - n.position[1]) >= min_distance for n in nodes):
            continue

        if all(
            point_to_segment_distance(
                x, y,
                c.nodes[0].position[0], c.nodes[0].position[1],
                c.nodes[1].position[0], c.nodes[1].position[1]
            ) >= min_distance
            for c in all_connections
        ):
            return (x, y)

    return None

def get_type_weights(typesToTry: list[util.NodeType], capacityVNeeds, nodes: list[Node]) -> list[float]:
    counts = {"market": 0, "industry": 0, "residential": 0}
    for node in nodes:
        if node.nodeType.name in counts:
            counts[node.nodeType.name] += 1

    goods_consumers = counts["market"] + counts["residential"]
    target_industry = goods_consumers / 2  # 1 industry per 2 others, tunable
    deficit = max(target_industry - counts["industry"], 0)

    weights = []
    for nodeType in typesToTry:
        if nodeType.name == "industry":
            weights.append(deficit / max(target_industry, 1) if deficit > 0 else 0.01)
        else:
            key = nodeType.name[0]
            capacity, need = capacityVNeeds.get(key, [0, 0])
            if need == 0 and capacity == 0:
                weights.append(1.0)
            elif need == 0:
                weights.append(0.1)
            else:
                weights.append(need / capacity if capacity > 0 else 0.1)

    return weights

def addNode(nodes: list[Node]):
    capacityVNeeds, levels = calculate_balance(nodes)

    averageLevel = sum(levels) / len(levels)

    levelToTry = round(random.random() * averageLevel * 1.49)

    typesToTry = [util.nodeTypes["market"], util.nodeTypes["industry"], util.nodeTypes["residential"]]

    weights = get_type_weights(typesToTry, capacityVNeeds, nodes)

    typesToTry = sorted(typesToTry, key=lambda t: -random.random() ** (1 / weights[typesToTry.index(t)]))

    typeToMake = None

    while typeToMake is None:
        typeToMake = tryTypesLevel(typesToTry, levelToTry, capacityVNeeds)

        if typeToMake is not None:
            break

        if levelToTry > 1:
            levelToTry -= 1
        else:
            raise exception("Error! Cannot generate new node without unbalancing need and capacity!")
    pos = generate_node_position(nodes)
    if pos is None:
        print("Cannot generate any new nodes!")
        return
    nodes.append(Node(typeToMake, pos))


def levelUpNode(nodes: list[Node]):
    capacityVNeeds, levels = calculate_balance(nodes)

    levels = [math.cbrt(1/(x-0.6)) for x in levels]

    nodesCopy = [x for x in nodes if x.nodeType.name[0] in capacityVNeeds]

    while len(nodesCopy) > 0:
        nodeToTry = random.choices(nodesCopy, levels, k=1)[0]

        out = tryTypesLevel([nodeToTry.nodeType], 1, capacityVNeeds) # trying new at level one is the same as +1 level

        out = None if nodeToTry.level == 5 else out

        if out is not None:
            nodeToTry.levelUp(1)
            break
        else:
            index = nodesCopy.index(nodeToTry)
            nodesCopy.pop(index)
            levels.pop(index)