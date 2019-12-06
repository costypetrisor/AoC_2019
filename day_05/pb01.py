
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
    # print(len(content.splitlines()))
    for line in content.splitlines():
        line = line.strip()
        assert '(' not in line
        a, b = line.split(')', 1)
        elements.append((a, b))
    # print(len(elements))
    return (elements, )


def compute_orbit_map(orbits_who, subject_obj):
    orbit_map = []
    obj_around = orbits_who.get(subject_obj)
    while obj_around:
        orbit_map.append(obj_around)
        subject_obj = obj_around
        obj_around = orbits_who.get(subject_obj)
    return orbit_map


def solve(orbits):
    all_objects = set(itertools.chain.from_iterable(orbits))
    # print(all_objects)
    # orbits_orbited_by = dict(orbits)
    # pprint(orbits_orbited_by)
    # print(len(orbits_orbited_by))
    # orbits_who = {v: k for k, v in orbits_orbited_by.items()}
    # pprint(orbits_who)
    # print(len(orbits_who))
    orbits_who = {}
    for a, b in orbits:
        orbits_who[b] = a
    # pprint(orbits_who)
    # print(len(orbits_who))

    orbit_map_you = compute_orbit_map(orbits_who, 'YOU')
    # print(f'orbit_map_you={orbit_map_you}')
    orbit_map_san = compute_orbit_map(orbits_who, 'SAN')
    # print(f'orbit_map_san={orbit_map_san}')

    common_points = set(orbit_map_san).intersection(orbit_map_you)
    print(common_points)

    # distances_to_common_points = {}
    min_dist = sys.maxsize
    min_dist_common_point = None
    for common_point in common_points:
        dist_you_cp = orbit_map_you.index(common_point)
        dist_you_san = orbit_map_san.index(common_point)
        if dist_you_cp + dist_you_san < min_dist:
            min_dist = dist_you_cp + dist_you_san
            min_dist_common_point = common_point
    print(f'min_dist={min_dist}    min_dist_common_point={min_dist_common_point}')




def main():
    tests = [
        # ('pb00_input02.txt', 42, ),
        ('pb00_input01.txt', 42, ),
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
