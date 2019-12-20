
import collections
import copy
import datetime
import functools
import itertools
import json
import logging
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
        elements.append(list(line))
    return (elements, )


movement_offsets = ((0, -1), (1, 0), (0, 1), (-1, 0), )


def print_grid(grid):
    # print('------------------------------------------------------------------------')
    for line in grid:
        print(''.join(line))
    # print('------------------------------------------------------------------------')


class Maze:

    def __init__(self, grid):
        self.grid_size = (len(grid[0]), len(grid))
        self.grid = grid

        self.portals = collections.defaultdict(dict)

        self.parse()

    def parse(self):
        portal_positions = collections.defaultdict(list)
        print_grid(self.grid)
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if cell.isalpha():
                    portal0_letter0_pos = (x, y)
                    portal0_letter1_pos = (x + 1, y)
                    if portal0_letter1_pos[0] < self.grid_size[0] and portal0_letter1_pos[1] < self.grid_size[1]:
                        portal0_letter1_cell = self.grid[portal0_letter1_pos[1]][portal0_letter1_pos[0]]
                        if portal0_letter1_cell.isalpha():
                            portal = ''.join((cell, portal0_letter1_cell))
                            portal_pos = (x + 2, y)
                            if 0 <= portal_pos[0] < self.grid_size[0] and 0 <= portal_pos[1] < self.grid_size[1]:
                                portal_cell = self.grid[portal_pos[1]][portal_pos[0]]
                                if portal_cell == '.':
                                    portal_positions[portal].append(portal_pos)
                            portal_pos = (x - 1, y)
                            if 0 <= portal_pos[0] < self.grid_size[0] and 0 <= portal_pos[1] < self.grid_size[1]:
                                portal_cell = self.grid[portal_pos[1]][portal_pos[0]]
                                if portal_cell == '.':
                                    portal_positions[portal].append(portal_pos)
                    portal0_letter1_pos = (x, y + 1)
                    if portal0_letter1_pos[0] < self.grid_size[0] and portal0_letter1_pos[1] < self.grid_size[1]:
                        portal0_letter1_cell = self.grid[portal0_letter1_pos[1]][portal0_letter1_pos[0]]
                        if portal0_letter1_cell.isalpha():
                            portal = ''.join((cell, portal0_letter1_cell))
                            portal_pos = (x, y + 2)
                            if 0 <= portal_pos[0] < self.grid_size[0] and 0 <= portal_pos[1] < self.grid_size[1]:
                                portal_cell = self.grid[portal_pos[1]][portal_pos[0]]
                                if portal_cell == '.':
                                    portal_positions[portal].append(portal_pos)
                            portal_pos = (x, y - 1)
                            if 0 <= portal_pos[0] < self.grid_size[0] and 0 <= portal_pos[1] < self.grid_size[1]:
                                portal_cell = self.grid[portal_pos[1]][portal_pos[0]]
                                if portal_cell == '.':
                                    portal_positions[portal].append(portal_pos)
        self.portal_positions = dict(portal_positions)
        print(f'portal_positions: {pformat(self.portal_positions)}')

        self.portals = {}
        for portal_key, doors in self.portal_positions.items():
            if len(doors) < 2: continue
            assert len(doors) == 2
            self.portals[doors[0]] = doors[1]
            self.portals[doors[1]] = doors[0]
        print(f'portals={pformat(self.portals)}')

        self.starting_pos, self.finishing_pos = self.portal_positions['AA'][0], self.portal_positions['ZZ'][0]
        print(f'Starting from AA {self.starting_pos} and finishing at ZZ {self.finishing_pos}')

    def find_shortest_path_with_queue(self):
        Robot = collections.namedtuple('Robot', 'pos, walked_distance, path_taken')

        seen = dict()
        frontier = collections.deque()
        frontier.append(Robot(self.starting_pos, 0, tuple()))
        found_solution = False
        cycle = 0

        while frontier and not found_solution:
            cycle += 1

            robot = frontier.popleft()

            # if cycle % 10000 == 0:
            # print(f'cycle={cycle}  robot={robot}')

            # make sure we don't walk back to where we came from
            seen_key = (robot.pos, )
            if seen_key in seen and robot.walked_distance >= seen[seen_key]:
                # print(f'discarding {robot} because seen key  dist seen[key]={seen[seen_key]}')
                continue
            seen[seen_key] = robot.walked_distance

            print(f'cycle={cycle}  robot_pos={robot.pos}  pos_in_portals={robot.pos in self.portals}  robot={robot}')
            if robot.pos in self.portals:
                other_pos = self.portals[robot.pos]
                print(f'Robot taking portal from {robot.pos} to {other_pos}')
                if other_pos == self.finishing_pos:
                    print(f'Found solution: {robot.walked_distance + 1}')
                    return robot.walked_distance + 1
                frontier.append(Robot(other_pos, robot.walked_distance + 1, robot.path_taken + (other_pos, )))

            for offset in movement_offsets:
                new_pos = (robot.pos[0] + offset[0], robot.pos[1] + offset[1])
                if new_pos[0] < 0 or new_pos[0] >= self.grid_size[0] or new_pos[1] < 0 or new_pos[1] >= self.grid_size[1]:
                    print(f'discarding {robot} because out of bonds')
                    continue
                new_tile = self.grid[new_pos[1]][new_pos[0]]
                if new_tile != '.':
                    continue

                if new_pos == self.finishing_pos:
                    print(f'Found solution: {robot.walked_distance + 1}')
                    return robot.walked_distance + 1
                # if new_tile.isalpha():
                #     if new_tile.isupper():
                #         if new_tile.lower() not in obtained_keys:
                #             # print(f"Not going to tile {new_pos} {new_tile}  because we don't have the key")
                #             continue
                #     elif new_tile.islower():
                #         # if new_tile in obtained_keys:  # commented because we can walk back
                #         #     continue
                #         if new_tile not in obtained_keys:
                #             obtained_keys = set(obtained_keys) | {new_tile, }
                #             obtained_keys_order = obtained_keys_order + (new_tile, )

                #         if set(obtained_keys) == all_keys:
                #             found_solution = obtained_keys_order, robot.walked_distance + 1
                #             break

                frontier.append(Robot(new_pos, robot.walked_distance + 1, robot.path_taken + (new_pos, )))

        print(f'found_solution={found_solution}')






def solve(grid):
    maze = Maze(grid)

    shortest_path = maze.find_shortest_path_with_queue()
    print(f'Shortest path: {shortest_path}')


def main():
    tests = [
        # ('pb00_input00.txt', 23, ),
        # ('pb00_input01.txt', 58, ),
        ('pb00_input02.txt', 17, ),
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
