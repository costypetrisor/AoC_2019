# cython: language_level=3, boundscheck=False

import collections
import copy
# import dataclasses
import datetime
import enum
import functools
import itertools
import json
import logging
import math
import operator
from pprint import pformat, pprint
import re
import os
import sys
from typing import *
import time

# from more_itertools import windowed



class Move:
    North = 1
    South = 2
    West = 3
    East = 4

Move_directions = (Move.North, Move.South, Move.West, Move.East, )

Move_opposite = {
    Move.North: Move.South,
    Move.South: Move.North,
    Move.West: Move.East,
    Move.East: Move.West,
}


movement_offsets = ((0, -1), (1, 0), (0, 1), (-1, 0), )


def move_xy(x, y, direction):
    if direction == Move.North:
        y -= 1
    elif direction == Move.South:
        y += 1
    elif direction == Move.West:
        x -= 1
    elif direction == Move.East:
        x += 1
    return (x, y)


def min_max_grid_coords(elements):
    min_x, max_x, min_y, max_y = sys.maxsize, 0, sys.maxsize, 0
    for elem in elements:
        if min_x > elem[0]:
            min_x = elem[0]
        if max_x < elem[0]:
            max_x = elem[0]
        if min_y > elem[1]:
            min_y = elem[1]
        if max_y < elem[1]:
            max_y = elem[1]
    return min_x, max_x, min_y, max_y


def make_grid(elements, min_x, max_x, min_y, max_y):
    grid = [[' ' for _ in range(min_x, max_x + 1)] for _ in range(min_y, max_y + 1)]
    possible_grid_elements = [tv.value for tv in tuple(Tile)]
    for elem in elements:
        if elem[2] in possible_grid_elements:
            grid[elem[1]][elem[0]] = Tile_print[elem[2]]
    return grid


def print_grid(grid):
    # print('------------------------------------------------------------------------')
    for line in grid:
        print(''.join(line))
    # print('------------------------------------------------------------------------')


def diff_points_to_direction(A, B):
    # print(f'diff_points_to_direction  A={A} B={B}')
    d = (A[0] - B[0], A[1] - B[1])
    if d[0] == 0 and d[1] == -1:
        return Move.South
    elif d[0] == 0 and d[1] == 1:
        return Move.North
    elif d[0] == -1 and d[1] == 0:
        return Move.East
    elif d[0] == 1 and d[1] == 0:
        return Move.West


def manhattan_distance(A, B):
    return abs(A[0] - B[0]) + abs(A[1] - B[1])

def sq_distance(A, B):
    return (A[0] - B[0]) * (A[0] - B[0]) + (A[1] - B[1]) * (A[1] - B[1])

def distance(A, B):
    return math.sqrt((A[0] - B[0]) * (A[0] - B[0]) + (A[1] - B[1]) * (A[1] - B[1]))





def read(filepath):
    elements = []
    if os.path.isfile(filepath):
        with open(filepath) as f:
            content = f.read()
    else:
        content = filepath
    for line in content.splitlines():
        line = line.strip()
        elements.append(list(line))
    return (elements, )


def count_bugs(grid):
    bug_count = 0
    for row, line in enumerate(grid):
        for col, cell in enumerate(line):
            if grid[row][col] == '#':
                bug_count += 1
    return bug_count


def solve(grid):
    original_grid = copy.deepcopy(grid)
    grid_size = (len(grid[0]), len(grid))

    # A bug dies (becoming an empty space) unless there is exactly one bug adjacent to it.
    # An empty space becomes infested with a bug if exactly one or two bugs are adjacent to it.

    grid[2][2] = '?'

    GRIDS = {0: grid}
    GRID_COUNTS = {}

    cycle = -1
    while True:
        cycle += 1
        if cycle == 200:
            break
        print(f'cycle={cycle}')

        NEW_GRIDS = {}
        bug_count = 0


        def compute_for_grid(level, grid_to_compute_for):
            new_grid = copy.deepcopy(grid_to_compute_for)

            lower_grid = GRIDS.get(level + 1)
            higher_grid = GRIDS.get(level - 1)

            for row, line in enumerate(grid_to_compute_for):
                for col, cell in enumerate(line):
                    if row == 2 and col == 2:
                        continue
                    current_pos = (row, col)

                    others_count = 0
                    for offset_x, offset_y in movement_offsets:
                        pos = (row + offset_x, col + offset_y)
                        if 0 <= pos[0] < grid_size[0] and 0 <= pos[1] < grid_size[1] and pos != (2, 2):
                            if grid_to_compute_for[pos[0]][pos[1]] == '#':
                                others_count += 1

                    if higher_grid:
                        if row in (0, grid_size[0] - 1):
                            if col == 2 and False:
                                if row == 0:
                                    for i in range(grid_size[0]):
                                        pos = (grid_size[0] - 1, i)
                                        if higher_grid[pos[0]][pos[1]] == '#':
                                            others_count += 1
                                elif row == grid_size[0] - 1:
                                    for i in range(grid_size[0]):
                                        pos = (0, i)
                                        if higher_grid[pos[0]][pos[1]] == '#':
                                            others_count += 1
                            else:
                                if row == 0:
                                    pos = (1, 2)
                                    if higher_grid[pos[0]][pos[1]] == '#':
                                        others_count += 1
                                elif row == grid_size[0] - 1:
                                    pos = (3, 2)
                                    if higher_grid[pos[0]][pos[1]] == '#':
                                        others_count += 1
                        if col in (0, grid_size[1] - 1):
                            if row == 2 and False:
                                if col == 0:
                                    for i in range(grid_size[1]):
                                        pos = (i, grid_size[0] - 1)
                                        if higher_grid[pos[0]][pos[1]] == '#':
                                            others_count += 1
                                elif col == grid_size[1] - 1:
                                    for i in range(grid_size[1]):
                                        pos = (i, 0)
                                        if higher_grid[pos[0]][pos[1]] == '#':
                                            others_count += 1
                            else:
                                if col == 0:
                                    pos = (2, 1)
                                    if higher_grid[pos[0]][pos[1]] == '#':
                                        others_count += 1
                                elif col == grid_size[0] - 1:
                                    pos = (2, 3)
                                    if higher_grid[pos[0]][pos[1]] == '#':
                                        others_count += 1

                    if lower_grid:
                        if row == 2:
                            if col == 1:
                                for i in range(grid_size[0]):
                                    pos = (i, 0)
                                    if lower_grid[pos[0]][pos[1]] == '#':
                                        others_count += 1
                            elif col == 3:
                                for i in range(grid_size[0]):
                                    pos = (i, 4)  # pos = (i, grid_size[1] - 1)
                                    if lower_grid[pos[0]][pos[1]] == '#':
                                        others_count += 1
                        elif col == 2:
                            if row == 1:
                                for i in range(grid_size[1]):
                                    pos = (0, i)
                                    if lower_grid[pos[0]][pos[1]] == '#':
                                        others_count += 1
                            elif row == 3:
                                for i in range(grid_size[1]):
                                    pos = (4, i)  # pos = (grid_size[0] - 1, i)
                                    if lower_grid[pos[0]][pos[1]] == '#':
                                        others_count += 1

                    if cell == '#' and others_count != 1:
                        new_grid[row][col] = '.'
                    elif cell == '.' and others_count in (1, 2):
                        new_grid[row][col] = '#'

            NEW_GRIDS[level] = new_grid

        for level, grid_to_compute_for in GRIDS.items():
            compute_for_grid(level, grid_to_compute_for)

        min_grid = min(GRIDS.keys())
        max_grid = max(GRIDS.keys())
        ng = [['.' for _ in range(grid_size[1])] for _ in range(grid_size[0])]
        ng[2][2] = '?'
        # ng = copy.deepcopy(original_grid)
        compute_for_grid(min_grid - 1, ng)
        ng = [['.' for _ in range(grid_size[1])] for _ in range(grid_size[0])]
        ng[2][2] = '?'
        # ng = copy.deepcopy(original_grid)
        compute_for_grid(max_grid + 1, ng)

        if count_bugs(NEW_GRIDS[min_grid - 1]) == 0:
            del NEW_GRIDS[min_grid - 1]
        if count_bugs(NEW_GRIDS[max_grid + 1]) == 0:
            del NEW_GRIDS[max_grid + 1]

        bug_count = 0
        for level, grid in sorted(NEW_GRIDS.items(), key=lambda e: e[0]):
            print(f'Grid at level: {level}')
            bug_count += count_bugs(grid)
            print_grid(grid)
        print(f'Total bug count at cycle {cycle}: {bug_count}')

        GRIDS = NEW_GRIDS

        print('')



def main():
    tests = [
        # ('pb00_input00.txt', 17, ),
        ('pb00_input01.txt', 17, ),
        # ('pb00_input02.txt', 17, ),
    ]
    for test, expected in tests:
        _input = read(test)
        res = solve(*_input)
        print(f'test={test}  expected={expected}  res={res}')

    # test = 'pb00_input01.txt'
    # _input = read(test)
    # result = solve(*_input)
    # print(result)


__name__ == '__main__' and main()
