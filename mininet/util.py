
import math

def distance( x, y ):
    """input x and y shall be list/tuple"""
    return math.sqrt(math.pow(x[0] - y[0], 2) + math.pow(x[1] - y[1], 2))
