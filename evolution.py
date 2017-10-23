# TODO: Test against MATLAB implementation
from math import sqrt, acos, pi, inf
import numpy as np
'''
Implementation of Discrete Contour Evolution algorithm (Longin Jan Latecki, Rolf Lakämper, Convexity
Rule for Shape Decomposition Based on Discrete Contour Evolution, In Computer Vision and Image
Understanding, Volume 73, Issue 3, 1999, Pages 441-454, ISSN 1077-3142,
https://doi.org/10.1006/cviu.1998.0738.).
Almost a direct port of the existing implementation in MATLAB.
For the most part, naming choices and comments are replicated.
'''

def evolution(slist, number, max_value=None, keep_endpoints=False, process_until_convex=False, display=False):
    # EVOLUTION(slist, number,<maxvalue>,<keepEndpoints>,<processUntilConvex><display>)
    #  discrete curve evolution of slist to n points
    # input: slist, number of vertices in resulting list
    #        optional: maxvalue: stop criterion,if >0.0 value overrides number
    #        optional: keepEndpoints. if set to 1, endpoints are NOT deleted
    #        optional: processUntilConvex. if set to 1, evolution continues until
    #                  shape is convex
    #        optional: display: displayflag
    # output: s=simplificated list
    #         value= vector containing values of remaining vertices in point-order
    #         delval= vector containing values of deleted vertices in order of deletion


    # this function is not speed-optimized, it is near a simple brute force
    # implementation !

    # blocking of vertices is taken into account.

    if max_value is not None and max_value > 0:
        number = 3
    else:
        max_value = inf

    if process_until_convex:
        number = 3
        max_value = inf

    del_val = np.array([])
    s = slist
    # initialize value vector (containing the information value of each vertex)
    value = np.zeros((1, len(s)))

    if number < 3 or len(slist) <= 3:
        print("WARNING (evolution): less than 3 vertices")
        return (s, value, del_val)

    peri = poly_perimeter(np.append(slist, [slist[0]], axis=0))

    for i in range(len(s)):
        value[i] = relevance(s, i, peri, keep_endpoints)

    m = -1

    while True:
        if display:
            print("Value of deleted vertex: {}".format(m))

        if process_until_convex and is_convex(s):
            break

        if number >= len(s):
            break

        i = np.argmin(value)
        m = value[i][0]
        if m > max_value:
            break

        # test blocking
        if m > 0:
            bf = blocked(s, i)

            # if vertex is blocked, find first non-blocked vertex
            # this procedure is separated from the 'usual min-case'
            # for speed-reasons (sort is needed instead of min)
            if bf:
                ind = np.argsort(value)
                rel = value[ind]
                j = 2
                m = 1e16
                while j < len(s):
                    i = ind[j]
                    bf = blocked(s, i)
                    if not bf:
                        m = rel[j]
                        break
                    j += 1

                if m > max_value:
                    break

        # delete vertex
        px = s[i, 0]
        py = s[i, 1]
        np.delete(s, i, axis=0)
        np.delete(value, i, axis=0)

        np.append(del_val, [m], axis=0)

        # neighboring vertices
        i0 = i - 1
        i1 = i
        if i0 == 0:
            i0 = len(s)
        elif i1 > len(s):
            i1 = 1

        value[i0] = relevance(s, i0, peri, keep_endpoints)
        value[i1] = relevance(s, i1, peri, keep_endpoints)

def relevance(s, index, peri, keep_endpoints):
    if keep_endpoints:
        if index == 0 or index == len(s[:, 0]) - 1:
            return inf
    # vertices
    i0 = index - 1
    i1 = index
    i2 = index + 1
    if i0 < 0:
        i0 = len(s) - 1
    elif i2 >= len(s):
        i2 = 0

    # segments
    seg1x = s[i1, 0] - s[i0, 0]
    seg1y = s[i1, 1] - s[i0, 1]
    seg2x = s[i1, 0] - s[i2, 0]
    seg2y = s[i1, 1] - s[i2, 1]

    l1 = sqrt(seg1x * seg1x + seg1y * seg1y)
    l2 = sqrt(seg2x * seg2x + seg2y * seg2y)

    # turning angle (0-180)
    a = 180 - acos((seg1x * seg2x + seg1y * seg2y) / l1 / l2) * 180 / pi

    # relevance measure
    v = a * l1 * l2 / (l1 + l2)

    v = v / peri # normalize
    return v

def seglength(p1x, p1y, p2x, p2y):
    dx = p2x - p1x
    dy = p2y - p1y
    l = sqrt(dx * dx + dy * dy)
    return l

def blocked(s, i):
    # find neighbouring vertices
    i0 = i - 1
    i1 = i + 1
    if i0 < 0:
        i0 = len(s) - 1
    elif i1 >= len(s):
        i1 = 0

    # bounding box
    minx = min([s[i0, 0], s[i, 0], s[i1, 0]])
    miny = min([s[i0, 1], s[i, 1], s[i1, 1]])
    maxx = max([s[i0, 0], s[i, 0], s[i1, 0]])
    maxy = max([s[i0, 1], s[i, 1], s[i1, 1]])

    # check if any boundary-vertex is inside bounding box
    # first create index-set v=s\(i0,i,i1)

    if i0 < i1:
        k = [i1, i, i0]
    elif i0 > i:
        k = [i0, i1, i]
    elif i1 < i:
        k = [i, i0, i1]

    v = np.arange(len(s))
    np.delete(v, k[0], axis=0)
    np.delete(v, k[1], axis=0)
    np.delete(v, k[2], axis=0)

    for k in range(len(v)):
        px = s[v[k], 0]
        py = s[v[k], 1]

        # vertex px, py inside boundary-box?
        b = False
        if not (px < minx or py < miny or px > maxx or py > maxy):
            # inside, now test triangle
            a = s[i, :] - s[i0, :] # a = i0 to i
            b = s[i1, :] - s[i, :] # b = i to i1
            c = s[i0, :] - s[i1, :] # c = i1 to i0

            e0 = s[i0, :] - np.array([px, py])
            e1 = s[i, :] - np.array([px, py])
            e2 = s[i1, :] - np.array([px, py])

            d0 = np.linalg.det(np.append(a, e0, axis=0))
            d1 = np.linalg.det(np.append(b, e1, axis=0))
            d2 = np.linalg.det(np.append(c, e2, axis=0))

            # INSIDE?
            b = (d0 > 0 and d1 > 0 and d2 > 0) or (d0 < 0 and d1 < 0 and d2 < 0)

        if b:
            break
    return b

# check if shape is convex (or concave)
def is_convex(s):
    con = True
    if len(s[:, 0]) < 4:
        return con
    # get direction of first curve
    for i in range(1, len(s[:, 0]) - 1):
        curv = curvature_direction(s, i)
        if curv != 0:
            break

    # check if there's a curve oppositely directed
    for j in range(i+1, len(s[:, 0] - 1)):
        curv1 = curvature_direction(s, j)
        if curv1 != 0 and curv1 != curv:
            con = False
            break
    return con

def curvature_direction(s, i):
    a = s[i-1, :]
    b = s[i, :]
    c = s[i+1, :]

    d1 = b - a
    d2 = c - b

    d = np.sign(np.linalg.det(np.append(d1, d2, axis=0)))
    return d

def poly_perimeter(s):
    return np.sum(np.sqrt(np.diff(s[:, 0]) ** 2 + np.diff(s[:, 1]) ** 2))