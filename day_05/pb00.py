
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


def solve(orbits):
    all_objects = set(itertools.chain.from_iterable(orbits))
    print(all_objects)
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

    orbit_count = 0
    # counted_orbits = set()
    for subject_obj in all_objects:
        # if obj == 'COM':
        #     continue

        # orbit_stack = collections.deque([subject_obj])
        # while orbit_stack:
        #     obj = orbit_stack.popleft()
        #     obj_around = orbits_who.get(obj)
        #     if not obj_around:
        #         continue
        #     orbit_stack.append(obj_around)
        #     orbit_count += 1

        obj_around = orbits_who.get(subject_obj)
        while obj_around:
            orbit_count += 1
            # print(f'{subject_obj} orbits {obj_around}')
            subject_obj = obj_around
            obj_around = orbits_who.get(subject_obj)
        # print('')
    return orbit_count




def main():
    tests = [
        # ('pb00_input00.txt', 42, ),
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
