import math
import threading
import parameters

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
    return math.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2)

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