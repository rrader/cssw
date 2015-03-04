from math import sqrt


def length(s, e):
    return sqrt((e[0] - s[0])**2 + (e[1] - s[1])**2)
