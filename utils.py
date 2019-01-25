import math
import threading
import parameters
import random
import numpy as np

class Pose(object):
    """docstring for Pose"""
    def __init__(self, nx, ny):
        self.x = nx
        self.y = ny

    def setPose(self, nx, ny):
        self.x = nx
        self.y = ny

    def getPose(self):
        return (self.x, self.y)
        
def getSign(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0

def normalise(a, mini, maxi):
    return (float(a) - float(mini)) / (float(maxi) - float(mini))

def closeEnough(a, b, _thresh=10):
    return abs(a-b) <= _thresh

def signof(a):
    if a >= 0:
        return 1
    else:
        return -1

def near(a, target, _thresh=10):
    return (a[0] > (target[0] - _thresh) and a[0] < (target[0] + _thresh)) and (a[1] > (target[1] - _thresh) and a[1] <(target[1] + _thresh))

def distance2p(a,b):
    a0 = float(a[0])
    a1 = float(a[1])
    b0 = float(b[0])
    b1 = float(b[1])
    return math.sqrt((a0-b0)**2+(a1-b1)**2)

class perpetualTimer():
    def __init__(self,t,hFunction):
        self.t=t
        self.hFunction = hFunction
        self.thread = threading.Timer(self.t, self.handle_function)

    def handle_function(self):
        self.hFunction()
        self.thread = threading.Timer(self.t, self.handle_function)
        self.thread.start()

    def start(self):
        self.thread.start()

    def cancel(self):
        self.thread.cancel()

# GCD and LCM are not in math module.  They are in gmpy, but these are simple enough:
def gcd(a,b):
    """Compute the greatest common divisor of a and b"""
    while b > 0:
        a, b = b, a % b
    return a
    
def lcm(a, b):
    """Compute the lowest common multiple of a and b"""
    return a * b / gcd(a, b)

def clamp(x, a, b):
    return max(a, min(x, b))

def getNeighboursFrom1D(elem_i, list=parameters.MAP_TILES, grid_w=parameters.CANVAS_WIDTH, grid_h=parameters.CANVAS_HEIGHT, eight_neigh=parameters.EIGHT_NEIGHBOURS):
    neighbours = []

    #k = i * width + j. Thus i = k / width, j = k % width

    #(i, j)
    coord2d = (elem_i / grid_w, elem_i % grid_w)

    #(i - 1, j)
    if coord2d[0] - 1 >= 0:
        kn1 = (coord2d[0] - 1) * grid_w + coord2d[1]
    else:
        kn1 = None

    #(i + 1, j)
    if coord2d[0] + 1 < grid_w:
        kn2 = (coord2d[0] + 1) * grid_w + coord2d[1]
    else:
        kn2 = None

    #(i, j - 1)
    if coord2d[1] - 1 >= 0:
        kn3 = (coord2d[0]) * grid_w + (coord2d[1] - 1)
    else:
        kn3 = None

    #(i, j + 1)
    if coord2d[1] + 1 < grid_h:
        kn4 = (coord2d[0]) * grid_w + (coord2d[1] + 1)
    else:
        kn4 = None

    if eight_neigh:
        if coord2d[0] - 1 >= 0 and coord2d[1] - 1 >= 0:
            kn5 = (coord2d[0] - 1) * grid_w + (coord2d[1] - 1)
        else:
            kn5 = None

        if coord2d[0] + 1 < grid_w and coord2d[1] + 1 < grid_h:
            kn6 = (coord2d[0] + 1) * grid_w + (coord2d[1] + 1)
        else:
            kn6 = None

        if coord2d[0] + 1 < grid_w and coord2d[1] - 1 >= 0:
            kn7 = (coord2d[0] + 1) * grid_w + (coord2d[1] - 1)
        else:
            kn7 = None

        if coord2d[0] - 1 >= 0 and coord2d[1] + 1 < grid_h:
            kn8 = (coord2d[0] - 1) * grid_w + (coord2d[1] + 1)
        else:
            kn8 = None

    res = []
    res.append(kn1)
    res.append(kn2)
    res.append(kn3)
    res.append(kn4)
    if eight_neigh:
        res.append(kn5)
        res.append(kn6)
        res.append(kn7)
        res.append(kn8)

    for x in res:
        if x != None:
            neighbours.append(list[x])

    return neighbours

#a and b are coordinates
#return if b is diagonal neighbour to a
def isDiagonalNeighbour(a, b):
    return ((b[0] == a[0] - 1 or b[0] == a[0] + 1)
            and (b[1] == a[1] - 1 or b[1] == a[1] + 1))

def trianglePointsFromCenter(centre, size):

    x1 = centre[0] + (size * math.cos(math.pi/3))
    y1 = centre[1] + (size * math.sin(math.pi/3))

    x2 = centre[0] + (size * math.cos((2*math.pi)/3))
    y2 = centre[1] + (size * math.sin((2*math.pi)/3))

    x3 = centre[0] + (size * math.cos(-math.pi/2))
    y3 = centre[1] + (size * math.sin(-math.pi/2))

    return [(x1, y1), (x2, y2), (x3, y3)]

def roughSemicirclePointsFromCenter(centre, size):

    res = []

    resolution = 8

    for i in range(0,resolution+1):
        x = centre[0] + (size * math.cos(-(i*math.pi)/resolution))
        y = centre[1] + (size * math.sin(-(i*math.pi)/resolution))
        res.append((x, y))

    return res
    
def getEdgeTile(_list=parameters.MAP_TILES, grid_w=parameters.CANVAS_WIDTH, grid_h=parameters.CANVAS_HEIGHT, forbidden=[]):
    #k = i * width + j. Thus i = k / width, j = k % width

    _x, _y = 0, 0

    if random.random() < 0.5:
        _x = random.randint(0, grid_w-1)
        _y = random.choice([0, grid_h-1])
    else:
        _x = random.choice([0, grid_w-1])
        _y = random.randint(0, grid_h-1)

    tile = _list[_x * grid_w + _y]

    while tile.getType() in forbidden:
        if random.random() < 0.5:
            _x = random.randint(0, grid_w-1)
            _y = random.choice([0, grid_h-1])
        else:
            _x = random.choice([0, grid_w-1])
            _y = random.randint(0, grid_h-1)

        tile = _list[_x * grid_w + _y]

    return tile

def weighted_choice(weight_map):
    values = weight_map.keys()
    p = weight_map.values()

    c = np.random.choice(range(0, len(values)), p=p)
    # print c, " ", values[c]
    return values[c]

def getRandomTile(tilemap=parameters.MAP_TILES, p=None, forbidden=[]):
    if p == None:
        res = random.choice(tilemap)
        while res.getType() in forbidden:
            res = random.choice(tilemap)
        return res
    else:
        res = random.choice(tilemap)
        while res.getType() in forbidden:
            res = random.choice(tilemap)
        return res

def getTilesInRadius(tile, radius, include_self=True):
    res = []
    if include_self:
        res = [tile]
    neigh = getNeighboursFrom1D(elem_i=tile.index, eight_neigh=False)
    res += neigh

    to_do = neigh
    for n in to_do:
        neigh = getNeighboursFrom1D(elem_i=n.index, eight_neigh=False)
        for n2 in neigh:
            if distance2p(tile.get2DCoord(), n2.get2DCoord()) > radius:
                continue
            if n2 not in res:
                res.append(n2)
            if n2 not in to_do:
                to_do.append(n2)

    return res

def countFreq(_list):
    d = {}
    for e in _list:
        if e not in d.keys():
            d[e] = 1
        else:
            d[e] += 1
    for k in d.keys():
        d[k] = float(d[k])/float(len(_list))
    return d