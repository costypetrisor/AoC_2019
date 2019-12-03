
import collections
import datetime
import functools
import itertools
import json
import math
from pprint import pformat, pprint
import re
import os
import sys
import time

from more_itertools import windowed


def read(filepath):
    elements = []
    if os.path.isfile(filepath):
        with open(filepath) as f:
            content = f.read()
    else:
        content = filepath
    for line in content.splitlines():
        line = line.strip()
        if not line: continue
        directions = [e.strip() for e in line.split(',')]
        elements.append(directions)
    assert len(elements) == 2
    return (elements, )


def distance(A, B):
    return abs(A[0] - B[0]) + abs(A[1] - B[1])


def solve(wire_directions):
    central_hub = (0, 0)
    wires = []
    for wire_direction in wire_directions:
        wire = [central_hub, ]
        for element in wire_direction:
            direction, length = element[0], element[1:]
            direction = direction.upper()
            length = int(length)
            last_point = wire[-1]
            if direction == 'U':
                wire.extend((last_point[0], last_point[1] + i) for i in range(-1, -length - 1, -1))
            elif direction == 'R':
                wire.extend((last_point[0] + i, last_point[1]) for i in range(1, length + 1))
            elif direction == 'D':
                wire.extend((last_point[0], last_point[1] + i) for i in range(1, length + 1))
            elif direction == 'L':
                wire.extend((last_point[0] + i, last_point[1]) for i in range(-1, -length - 1, -1))
            # print(wire)
        wires.append(wire)
    for i, wire in enumerate(wires):
        print(f'wire[{i}]=  {wire_directions[i]}')
        print(f'wire[{i}]=  {wire}')

    intersections = set(wires[0]).intersection(set(wires[1]))
    print(f'intersections={intersections}')
    intersections.remove(central_hub)
    smallest_dist = sys.maxsize
    for point in intersections:
        d = distance(central_hub, point)
        print(f'distance central_hub to point={point} is {d}')
        if d < smallest_dist:
            smallest_dist = d
    print(f'Smallest dist to central point = {smallest_dist}')
    return smallest_dist




def main():
    tests = [
        ('R8,U5,L5,D3\nU7,R6,D4,L4', 3, ),
        ('R75,D30,R83,U83,L12,D49,R71,U7,L72\nU62,R66,U55,R34,D71,R55,D58,R83', 159),
        ('R98,U47,R26,D63,R33,U87,L62,D20,R33,U53,R51\nU98,R91,D20,R16,D67,R40,U7,R15,U6,R7', 135),
        ('pb00_input00.txt', 17, ),
    ]
    for test, expected in tests:
        _input = read(test)
        res = solve(*_input)
        print(test, expected, res)

    # test = 'pb00_input01.txt'
    # _input = read(test)
    # result = solve(*_input)
    # print(result)


__name__ == '__main__' and main()
