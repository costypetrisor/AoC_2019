
import collections
import copy
import dataclasses
import datetime
import enum
import functools
import itertools
import json
import logging
import math
from pprint import pformat, pprint
import re
import os
import sys
from typing import *
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
        elements.append(line)
    return (elements, )


movement_offsets = ((0, -1), (1, 0), (0, 1), (-1, 0), )



def solve(grid):
    original_grid = copy.deepcopy(grid)
    grid_size = (len(grid[0]), len(grid))

    starting_pos = (-1, -1)
    all_keys, all_doors = set(), set()
    for line_idx, line in enumerate(grid):
        if '@' in line:
            starting_pos = (line.index('@'), line_idx)
        line = line.replace('.', '').replace('#', '').replace('@', '')
        all_keys.update(k for k in line if k.islower())
        all_doors.update(d for d in line if d.isupper())
    print(f'starting at {starting_pos}  all_keys={all_keys}  all_doors={all_doors}')

    grid = [list(line) for line in original_grid]

    Robot = collections.namedtuple('Robot', 'pos, obtained_keys, obtained_keys_order, walked_distance')

    seen = set()
    frontier = collections.deque()
    frontier.append(Robot(starting_pos, set(), tuple(), 0))
    found_solution = False
    cycle = 0

    while frontier and not found_solution:
        cycle += 1

        robot = frontier.popleft()

        if cycle % 10000 == 0:
            print(f'cycle={cycle}  robot={robot}')

        # make sure we don't walk back to where we came from
        seen_key = (robot.pos, tuple(sorted(robot.obtained_keys)), )
        if seen_key in seen:
            continue
        seen.add(seen_key)

        # current_tile = grid[robot.pos[1]][robot.pos[0]]
        # if current_tile.isalpha():
        #     if current_tile.isupper():
        #         if current_tile.lower() not in robot.obtained_keys:
        #             continue
            # elif current_tile.islower():
            #     if current_tile in robot.obtained_keys:
            #         continue

        for offset in movement_offsets:
            new_pos = (robot.pos[0] + offset[0], robot.pos[1] + offset[1])
            if new_pos[0] < 0 or new_pos[0] >= grid_size[0] or new_pos[1] < 0 or new_pos[1] >= grid_size[1]:
                continue
            new_tile = grid[new_pos[1]][new_pos[0]]
            if new_tile == '#':
                continue
            obtained_keys, obtained_keys_order = robot.obtained_keys, robot.obtained_keys_order
            if new_tile.isalpha():
                if new_tile.isupper():
                    if new_tile.lower() not in obtained_keys:
                        # print(f"Not going to tile {new_pos} {new_tile}  because we don't have the key")
                        continue
                elif new_tile.islower():
                    # if new_tile in obtained_keys:  # commented because we can walk back
                    #     continue
                    if new_tile not in obtained_keys:
                        obtained_keys = set(obtained_keys) | {new_tile, }
                        obtained_keys_order = obtained_keys_order + (new_tile, )

                    if set(obtained_keys) == all_keys:
                        found_solution = obtained_keys_order, robot.walked_distance + 1
                        break

            frontier.append(Robot(new_pos, obtained_keys, obtained_keys_order, robot.walked_distance + 1))

    print(f'found_solution={found_solution}')



def main():
    tests = [
        # ('pb00_input00.txt', 8, ),  # ab
        # ('pb00_input01.txt', 86, ),  # abcdef
        # ('pb00_input02.txt', 132, ),  # b, a, c, d, f, e, g
        # ('pb00_input04.txt', 81, ),  # a, c, f, i, d, g, b, e, h
        # ('pb00_input03.txt', 136, ),  # a, f, b, j, g, n, h, d, l, o, e, p, c, i, k, m
        ('pb00_input07.txt', 17, ),
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
