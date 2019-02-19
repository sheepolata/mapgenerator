import time
import utils
import parameters


#_start and _goal here are Coordinates
def heuristic_cost_estimate(_current, _goal):
    res = utils.distance2p(_current.getPose(), _goal.getPose())
    # res = _goal.getCost()
    return res

#start and goal are tiles
def astar(_start, _goal, maptiles=parameters.getInstance().MAP_TILES, forbidden=[], diagonal_neighbourhood=True):
    # The set of nodes already evaluated
    closedSet = []

    # The set of currently discovered nodes that are not evaluated yet.
    # Initially, only the start node is known.
    openSet = [_start]

    # For each node, which node it can most efficiently be reached from.
    # If a node can be reached from many nodes, cameFrom will eventually contain the
    # most efficient previous step.
    came_from = {}

    # For each node, the cost of getting from the start node to that node.
    g_score = {}
    for i in maptiles:
        g_score[i] = float("inf")
    
    # The cost of going from start to start is zero.
    g_score[_start] = 0.0

    # For each node, the total cost of getting from the start node to the goal
    # by passing by that node. That value is partly known, partly heuristic.
    f_score = {}
    for i in maptiles:
        f_score[i] = float("inf")
    f_score[_start] = heuristic_cost_estimate(_start, _goal)

    while openSet:

        #current = Node in openSet with the lowest f_score
        mini = float("inf")
        current = None
        for elt in openSet:
            if mini >= f_score[elt]:
                mini = f_score[elt]
                current = elt

        if current == None:
            print("Error : current == None")
            return []

        if current == _goal:
            return reconstructPath(came_from, current)

        openSet.remove(current)
        closedSet.append(current)

        #For each neighbours of current
        for _neighbour in utils.getNeighboursFrom1D(current.index, maptiles, parameters.getInstance().CANVAS_WIDTH, parameters.getInstance().CANVAS_HEIGHT, eight_neigh=diagonal_neighbourhood):
            if _neighbour in closedSet:
                continue

            if _neighbour not in openSet:
                openSet.append(_neighbour)

            #The distance from start to a neighbor
            #the "dist_between" function may vary as per the solution requirements.
            #May add utils.distance2p(current.getPose(), _neighbour.getPose()) to cost BUT decrease perf quite a lot
            tentative_gScore = (g_score[current] 
                                + _neighbour.getCost() 
                                + (1*((_neighbour.h+_neighbour.w)/2) 
                                    if (not utils.isDiagonalNeighbour(current.getPose(), _neighbour.getPose()))
                                    else sqrt(2)*((_neighbour.h+_neighbour.w)/2)
                                  )
                                )
            if tentative_gScore >= g_score[_neighbour] or _neighbour.getType() in forbidden:
                continue

            came_from[_neighbour] = current
            g_score[_neighbour] = tentative_gScore
            f_score[_neighbour] = g_score[_neighbour] + heuristic_cost_estimate(_neighbour, _goal)

    return None


def reconstructPath(came_from, current):
    total_path = [current]
    while current in came_from.keys():
        current = came_from[current]
        total_path.append(current)

    return list(reversed(total_path)) #+ [total_path[-1]]

def computePathLength(path):
    if not path:
        return -1
    if len(path) == 1:
        return 0
    res = path[0].getCost()
    for i in range(1, len(path)):
        res = res + path[i].getCost()
    return res

def getPathLength(tile1, tile2, maptiles=parameters.getInstance().MAP_TILES, forbidden=[], approx=False):
    if approx:
        res = utils.distance2p(tile1.getPose(), tile2.getPose())
    #OLD
    else:
        path = astar(tile1, tile2, maptiles, forbidden)
        res = computePathLength(path)
    
    return res
    

# def checkStraightPath(env, p1, p2, precision, check_obs=True, check_river=True):
#     #if line from entity.pos to target is OK, do not compute astar
#         #y = a*x + b => a==0 : parallele; a==inf : perpendicular; a == (-)1 : (-)45deg
#     a, b = geo.computeLineEquation(p1, p2)
#     astar_needed = False
#     if a == None or b == None:
#         astar_needed = True
#     elif abs(p1[0] - p2[0]) > abs(p1[1] - p2[1]):
#         mini = min(p1[0], p2[0])
#         maxi = max(p1[0], p2[0])

#         for step_x in range(int(mini), int(maxi), int(precision)):
#             y = a*step_x + b
#             if env.collideOneObstacle_Point((step_x, y), check_obs=check_obs, check_river=check_river):
#                 astar_needed = True
#     else:
#         mini = min(p1[1], p2[1])
#         maxi = max(p1[1], p2[1])

#         for step_y in range(int(mini), int(maxi), int(precision)):
#             # y = a*step_x + b
#             x = (step_y - b)/a
#             if env.collideOneObstacle_Point((x, step_y), check_obs=check_obs, check_river=check_river):
#                 astar_needed = True

#     return astar_needed