
import bisect
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

        self.distances_portal_to_portal = {}

        self.parse()

    def parse(self):
        portal_positions = collections.defaultdict(list)
        self.positions_to_portal_names = {}
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
                                    self.positions_to_portal_names[portal_pos] = portal
                            portal_pos = (x - 1, y)
                            if 0 <= portal_pos[0] < self.grid_size[0] and 0 <= portal_pos[1] < self.grid_size[1]:
                                portal_cell = self.grid[portal_pos[1]][portal_pos[0]]
                                if portal_cell == '.':
                                    portal_positions[portal].append(portal_pos)
                                    self.positions_to_portal_names[portal_pos] = portal
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
                                    self.positions_to_portal_names[portal_pos] = portal
                            portal_pos = (x, y - 1)
                            if 0 <= portal_pos[0] < self.grid_size[0] and 0 <= portal_pos[1] < self.grid_size[1]:
                                portal_cell = self.grid[portal_pos[1]][portal_pos[0]]
                                if portal_cell == '.':
                                    portal_positions[portal].append(portal_pos)
                                    self.positions_to_portal_names[portal_pos] = portal
        self.portal_positions = dict(portal_positions)
        print(f'positions_to_portal_names={pformat(self.positions_to_portal_names)}')
        print(f'portal_positions: {pformat(self.portal_positions)}')

        print(f'grid_size={self.grid_size}')
        self.portals_going_down = {}
        self.portals_going_up = {}
        for portal_key, doors in self.portal_positions.items():
            if len(doors) < 2: continue
            assert len(doors) == 2
            door_outer, door_inner = doors
            if door_inner[0] in (2, self.grid_size[0] - 3) or door_inner[1] in (2, self.grid_size[1] - 3):
                door_outer, door_inner = door_inner, door_outer
                print(f'Flipped outer={door_outer} with inner={door_inner}')
            else:
                print(f'NOT FLIPPED outer={door_outer} with inner={door_inner}')
            self.portals_going_down[door_inner] = door_outer
            self.portals_going_up[door_outer] = door_inner
        print(f'portals_going_down={pformat(self.portals_going_down)}')
        print(f'portals_going_up={pformat(self.portals_going_up)}')
        portals_going_down_names = set(self.positions_to_portal_names[e] for e in self.portals_going_down)
        assert len(portals_going_down_names) == len(self.portals_going_down)
        portals_going_up_names = set(self.positions_to_portal_names[e] for e in self.portals_going_up)
        assert len(portals_going_up_names) == len(self.portals_going_up)
        if portals_going_down_names != portals_going_up_names:
            print(f'pgdn extra: {portals_going_down_names - portals_going_up_names} pgun: {portals_going_up_names - portals_going_down_names}')
        assert portals_going_down_names == portals_going_up_names

        self.starting_pos, self.finishing_pos = self.portal_positions['AA'][0], self.portal_positions['ZZ'][0]
        print(f'Starting from AA {self.starting_pos} and finishing at ZZ {self.finishing_pos}')

    def compute_walk_distances(self):
        for point in (self.starting_pos, self.finishing_pos):
            distances = self._walk_from_point_to_all_other_points(point)
            # print(f'Distances from {point} {self.positions_to_portal_names[point]}: {pformat(distances)}')
            self.distances_portal_to_portal[point] = distances
        for point in itertools.chain(self.portals_going_down, self.portals_going_up, ):
            distances = self._walk_from_point_to_all_other_points(point)
            # print(f'Distances from {point} {self.positions_to_portal_names[point]}: {pformat(distances)}')
            self.distances_portal_to_portal[point] = distances

        print(f'distances_portal_to_portal={pformat(self.distances_portal_to_portal)}')

    def _walk_from_point_to_all_other_points(self, from_point):
        Robot = collections.namedtuple('Robot', [
            'pos',
            # 'level',
            'walked_distance',
            # 'path_taken',
        ])

        seen = dict()
        frontier = collections.deque()
        frontier.append(Robot(
            from_point,
            walked_distance=0,
            # path_taken=(),
        ))
        cycle = 0

        distances = {}

        while frontier:
            cycle += 1

            robot = frontier.popleft()

            if cycle % 10000 == 0:
                print(f'cycle={cycle}  robot={robot}')

            # make sure we don't walk back to where we came from
            seen_key = (robot.pos, )
            if seen_key in seen and robot.walked_distance >= seen[seen_key]:
                # print(f'discarding {robot} because seen key  dist seen[key]={seen[seen_key]}')
                continue
            seen[seen_key] = robot.walked_distance

            for offset in movement_offsets:
                new_pos = (robot.pos[0] + offset[0], robot.pos[1] + offset[1])
                if new_pos[0] < 0 or new_pos[0] >= self.grid_size[0] or new_pos[1] < 0 or new_pos[1] >= self.grid_size[1]:
                    print(f'discarding {robot} because out of bonds')
                    continue
                new_tile = self.grid[new_pos[1]][new_pos[0]]
                if new_tile != '.':
                    continue

                frontier.append(Robot(
                    new_pos, robot.walked_distance + 1,
                    # robot.path_taken + (new_pos, ),
                ))

            if robot.pos != from_point and (robot.pos in self.portals_going_up or robot.pos in self.portals_going_down or robot.pos == self.starting_pos or robot.pos == self.finishing_pos):
                distances[robot.pos] = robot.walked_distance
                # continue

        return distances

    def find_shortest_path_with_queue(self):
        Robot = collections.namedtuple('Robot', 'pos, walked_distance, path_taken')

        seen = dict()
        frontier = collections.deque()
        frontier.append(Robot(self.starting_pos, 0, tuple()))
        found_solution = False
        cycle = 0
        min_solution = sys.maxsize
        solutions = []

        while frontier and not found_solution:
            cycle += 1

            robot = frontier.popleft()

            # if cycle % 10000 == 0:
            # print(f'cycle={cycle}  robot={robot}')

            # make sure we don't walk back to where we came from
            seen_key = (robot.pos, )
            if seen_key in seen and robot.walked_distance >= seen[seen_key] or robot.walked_distance > min_solution:
                # print(f'discarding {robot} because seen key  dist seen[key]={seen[seen_key]}')
                continue
            seen[seen_key] = robot.walked_distance

            pos_in_going_down = self.portals_going_down.get(robot.pos)
            pos_in_going_up = self.portals_going_up.get(robot.pos)
            print(f'cycle={cycle}  robot_pos={robot.pos}  pos_in_portals={pos_in_going_down, pos_in_going_up}  robot={robot}')
            if pos_in_going_down:
                print(f'Robot taking portal from {robot.pos} to {pos_in_going_down}')
                if pos_in_going_down == self.finishing_pos:
                    print(f'Found solution: {robot.walked_distance + 1}')
                    solutions.append(robot.walked_distance + 1)
                    solutions = sorted(solutions)
                    if solutions[0] < min_solution:
                        min_solution = solutions[0]
                frontier.append(Robot(pos_in_going_down, robot.walked_distance + 1, robot.path_taken + (pos_in_going_down, )))
            if pos_in_going_up:
                print(f'Robot taking portal from {robot.pos} to {pos_in_going_up}')
                if pos_in_going_up == self.finishing_pos:
                    print(f'Found solution: {robot.walked_distance + 1}')
                    solutions.append(robot.walked_distance + 1)
                    solutions = sorted(solutions)
                    if solutions[0] < min_solution:
                        min_solution = solutions[0]
                frontier.append(Robot(pos_in_going_up, robot.walked_distance + 1, robot.path_taken + (pos_in_going_up, )))

            possible_movements = sorted(self.distances_portal_to_portal[robot.pos].items(), key=lambda m: m[1])
            for new_pos, adding_distance in possible_movements:
                if new_pos == self.finishing_pos:
                    print(f'Found solution: {robot.walked_distance + adding_distance}')
                    solutions.append(robot.walked_distance + adding_distance)
                    solutions = sorted(solutions)
                    if solutions[0] < min_solution:
                        min_solution = solutions[0]
                    # return robot.walked_distance + adding_distance

                frontier.append(Robot(new_pos, robot.walked_distance + adding_distance, robot.path_taken + (new_pos, )))

        print(f'BEST found_solution={min_solution}')


    def find_shortest_path_with_queue_in_levels(self):
        class Robot(collections.namedtuple('_Robot', [
            'pos',
            'level',
            'walked_distance',
            'level_offset',
            'path_taken',
        ])):
            pass
            # def __repr__(self):
            #     return f'Robot(pos={self.pos}, level={self.level}, walked_distance={self.walked_distance})'

            # def path_taken(self, ):

        seen = dict()
        frontier = collections.deque()
        frontier.append(Robot(
            self.starting_pos,
            level=0,
            walked_distance=0,
            level_offset=0,
            path_taken=(),
        ))
        found_solution = False
        cycle = 0
        min_solution = sys.maxsize
        solutions = []

        while frontier and not found_solution:
            cycle += 1

            robot = frontier.popleft()

            # if cycle % 10000 == 0:
            #     print(f'cycle={cycle}  robot={robot}')

            # make sure we don't walk back to where we came from
            seen_key = (robot.pos, robot.level, robot.level_offset, )
            if seen_key in seen and robot.walked_distance >= seen[seen_key] or robot.walked_distance > min_solution:
                continue
            seen[seen_key] = robot.walked_distance

            pos_in_going_down = self.portals_going_down.get(robot.pos)
            pos_in_going_up = self.portals_going_up.get(robot.pos)

            if cycle % 10000 == 0:
                print(f'cycle={cycle}  min_solution={min_solution}  pos_in_going down={1 if pos_in_going_down else 0} up={1 if pos_in_going_up else 0}   robot={robot}')

            if pos_in_going_down and robot.level_offset != -1 and robot.level < 100:
                # print(f'Robot taking portal from {robot.pos} to {pos_in_going_down}')
                # if pos_in_going_down == self.finishing_pos and robot.level == 0:
                #     print(f'Found solution: {robot.walked_distance + 1}')
                #     solutions.append(robot.walked_distance + 1)
                #     solutions = sorted(solutions)
                #     if solutions[0] < min_solution:
                #         min_solution = solutions[0]
                new_portal_name = self.positions_to_portal_names[pos_in_going_down]
                frontier.append(Robot(
                    pos_in_going_down,
                    robot.level + 1,
                    robot.walked_distance + 1,
                    level_offset=+1,
                    # path_taken=robot.path_taken + (pos_in_going_down, ),
                    path_taken=robot.path_taken + ((new_portal_name, 1), ),
                ))

            if robot.level > 0 and pos_in_going_up and robot.level_offset != +1:
                # print(f'Robot taking portal from {robot.pos} to {pos_in_going_up}')
                # if pos_in_going_up == self.finishing_pos and robot.level == 0:
                #     print(f'Found solution: {robot.walked_distance + 1}')
                #     solutions.append(robot.walked_distance + 1)
                #     solutions = sorted(solutions)
                #     if solutions[0] < min_solution:
                #         min_solution = solutions[0]
                new_portal_name = self.positions_to_portal_names[pos_in_going_up]
                frontier.append(Robot(
                    pos_in_going_up,
                    robot.level - 1,
                    robot.walked_distance + 1,
                    level_offset=-1,
                    # path_taken=robot.path_taken + (pos_in_going_up, ),
                    path_taken=robot.path_taken + ((new_portal_name, 1), ),
                ))

            # for offset in movement_offsets:
            possible_movements = sorted(self.distances_portal_to_portal[robot.pos].items(), key=lambda m: m[1])
            current_in_going_up = robot.pos in self.portals_going_up
            current_in_going_down = robot.pos in self.portals_going_down
            for new_pos, adding_distance in possible_movements:
                new_in_going_up = robot.pos in self.portals_going_up
                new_in_going_down = robot.pos in self.portals_going_down

                if new_pos == self.starting_pos:
                    continue

                if robot.level == 0:
                    if new_pos in self.portals_going_up:
                        continue

                # if (current_in_going_up and new_in_going_up) or (current_in_going_down and new_in_going_down):
                #     continue

                # level_offset = 0
                # pos_in_going_down = self.portals_going_down.get(new_pos)
                # if pos_in_going_down:
                #     level_offset += 1
                # pos_in_going_up = self.portals_going_up.get(new_pos)
                # if pos_in_going_up:
                #     level_offset -= 1
                # if new_pos not in (self.starting_pos, self.finishing_pos):
                #     assert level_offset != 0
                # new_level = robot.level + level_offset
                # if new_level < 0:
                #     continue

                new_level = robot.level

                if new_pos == self.finishing_pos and robot.level == 0:
                    print(f'Found solution: {robot.walked_distance + adding_distance}    {robot}')
                    solutions.append(robot.walked_distance + adding_distance)
                    solutions = sorted(solutions)
                    if solutions[0] < min_solution:
                        min_solution = solutions[0]

                new_pos_name = self.positions_to_portal_names[new_pos]

                frontier.append(Robot(
                    new_pos, new_level, robot.walked_distance + adding_distance,
                    level_offset=0,
                    path_taken=robot.path_taken + ((new_pos_name, adding_distance), ),
                ))

        print(f'BEST found_solution={min_solution}')






def solve(grid):
    maze = Maze(grid)

    maze.compute_walk_distances()
    # return

    shortest_path = maze.find_shortest_path_with_queue()
    print(f'Part1 : Shortest path: {shortest_path}')
    shortest_path = maze.find_shortest_path_with_queue_in_levels()
    print(f'Part2 : Shortest path: {shortest_path}')


def main():
    tests = [
        # ('pb00_input00.txt', 23, ),
        # ('pb00_input01.txt', 58, ),
        # ('pb01_input00.txt', 396, ),
        ('pb00_input02.txt', 7492, ),
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
