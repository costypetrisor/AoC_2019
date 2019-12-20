# cython: language_level=3, boundscheck=False

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
import operator
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


cpdef void print_grid(list grid):
    cdef list line
    # print('------------------------------------------------------------------------')
    for line in grid:
        print(''.join(line))
    # print('------------------------------------------------------------------------')



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


cdef tuple move_xy(int x, int y, int direction):
    if direction == Move.North:
        y -= 1
    elif direction == Move.South:
        y += 1
    elif direction == Move.West:
        x -= 1
    elif direction == Move.East:
        x += 1
    return (x, y)



# @dataclasses.dataclass
cdef class SAPNode:
    # __slots__ = ('position', 'possibilities', 'possib_idx', )
    cdef public tuple position
    cdef public list possibilities
    cdef public int possib_idx

    def __init__(self, position: Tuple, possibilities: List, possib_idx: int):
        self.position = position
        self.possibilities = possibilities
        self.possib_idx = possib_idx


SAP_Path = collections.namedtuple('SAP_Path', 'distance, end_pos')


cdef dict SAP_CACHE = {}


cpdef list scan_all_paths(list grid, tuple starting_pos, looking_for=None):
    cdef:
        list all_paths, all_paths_just_end, stack, path_l
        bint backtracking_running, increment_was_done, visited_point_before
        tuple current_pos, point, path
        str current_tile
        list possibilities
        int direction
    global SAP_CACHE
    if not looking_for:
        if starting_pos in SAP_CACHE:
            return SAP_CACHE[starting_pos]
    # print(f'scan_all_paths {starting_pos} {grid[starting_pos[1]][starting_pos[0]]}')
    all_paths = []

    stack = []
    backtracking_running = True
    current_pos = starting_pos
    stack.append(SAPNode(position=starting_pos, possibilities=[], possib_idx=0))

    # pprint(starting_pos)
    while backtracking_running:
        # pprint(stack)

        current_pos = stack[-1].position if stack else starting_pos
        current_tile = grid[current_pos[1]][current_pos[0]]

        if current_tile in ('.', '@') or current_pos == starting_pos:
            possibilities = []
            for direction in Move_directions:
                point = move_xy(current_pos[0], current_pos[1], direction)
                if grid[point[1]][point[0]] != '#':
                    visited_point_before = False
                    for node in stack:
                        if node.position == point:
                            visited_point_before = True
                            break
                    # if not any(node.position == point for node in stack):
                    if not visited_point_before:
                        possibilities.append(point)
            # print(f'    scan_all_paths: for {current_pos} {current_tile}    possibilities={possibilities}')

            if possibilities:
                node = SAPNode(position=possibilities[0], possibilities=possibilities, possib_idx=0)
                stack.append(node)
                continue

        # path = tuple(node.position for node in stack)
        path_l = []
        for node in stack:
            path_l.append(node.position)
        path = tuple(path_l)

        all_paths.append(path)
        if looking_for == current_tile:
            all_paths.reverse()
            return all_paths

        increment_was_done = False
        while stack:
            top_node = stack[-1]
            if top_node.possib_idx < len(top_node.possibilities) - 1:
                top_node.possib_idx += 1
                top_node.position = top_node.possibilities[top_node.possib_idx]
                increment_was_done = True
                break
            else:
                del stack[-1]
        if not stack or not increment_was_done:
            backtracking_running = False

    assert len(set(all_paths)) == len(all_paths)

    # SAP_CACHE[starting_pos] = all_paths
    # return all_paths
    all_paths_just_end = []
    for path in all_paths:
        all_paths_just_end.append(SAP_Path(distance=len(path) - 1, end_pos=path[-1]))
    SAP_CACHE[starting_pos] = all_paths_just_end
    return all_paths_just_end


SAP2_Robot = collections.namedtuple('Robot', 'pos, walked_distance')


cdef dict SAP2_CACHE = {}


cpdef list scan_all_paths2(list grid, tuple starting_pos, looking_for=None, only_directs=True):
    cdef:
        list app_paths
        tuple grid_size
        set seen
        int cycle
        bint found_solution
    global SAP_CACHE
    if not looking_for:
        if starting_pos in SAP_CACHE:
            return SAP_CACHE[starting_pos]

    all_paths = []

    grid_size = (len(grid[0]), len(grid))
    seen = set()
    frontier = collections.deque()
    frontier.append(SAP2_Robot(starting_pos, 0))
    found_solution = False
    cycle = 0

    while frontier and not found_solution:
        cycle += 1

        robot = frontier.popleft()

        if cycle % 10000 == 0:
            print(f'SAP2 cycle={cycle}  robot={robot}')

        # make sure we don't walk back to where we came from
        seen_key = (robot.pos, )  # tuple(sorted(robot.obtained_keys))
        if seen_key in seen:
            continue
        seen.add(seen_key)

        tile = grid[robot.pos[1]][robot.pos[0]]
        if robot.walked_distance > 0 and (tile.isalpha() or tile == '@'):
            all_paths.append(SAP_Path(distance=robot.walked_distance, end_pos=robot.pos))
            if only_directs:
                continue

        for offset in movement_offsets:
            new_pos = (robot.pos[0] + offset[0], robot.pos[1] + offset[1])
            if new_pos[0] < 0 or new_pos[0] >= grid_size[0] or new_pos[1] < 0 or new_pos[1] >= grid_size[1]:
                continue
            new_tile = grid[new_pos[1]][new_pos[0]]
            if new_tile == '#':
                continue

            frontier.append(SAP2_Robot(new_pos, robot.walked_distance + 1))

    all_paths = sorted(all_paths, key=operator.attrgetter('distance'))
    SAP_CACHE[starting_pos] = all_paths
    return all_paths




# @dataclasses.dataclass
cdef class Connection:
    cdef public tuple pos
    cdef public str tile
    cdef public int steps_to_take

    def __init__(self, pos, tile, steps_to_take):
        self.pos = pos
        self.tile = tile
        self.steps_to_take = steps_to_take

    def __repr__(self):
        return f'Connection(pos={self.pos}, tile={self.tile}, steps_to_take={self.steps_to_take})'




cpdef compute_connections(list grid, tuple starting_pos):
    cdef:
        set tiles_mapped
        tuple current_pos, tile_pos
        str current_tile, tile
        list paths
        int distance
    tile_to_points = collections.defaultdict(dict)
    tiles_mapped = set()
    points_to_search_paths_for = collections.deque([starting_pos, ])
    print(f'compute_connections  starting_pos={starting_pos} {grid[starting_pos[1]][starting_pos[0]]}')

    while points_to_search_paths_for:
        current_pos = points_to_search_paths_for.popleft()
        current_tile = grid[current_pos[1]][current_pos[0]]
        assert current_tile.isalpha() or current_tile == '@'
        tiles_mapped.add(current_tile)
        paths = scan_all_paths2(grid, current_pos)
        print(f'  computing connections for {current_pos} {current_tile}:')
        for path in paths:
            # tile_pos = path[-1]  # SAP1
            tile_pos = path.end_pos  # SAP2
            if tile_pos == current_pos:
                continue

            tile = grid[tile_pos[1]][tile_pos[0]]
            print(f'    possible {tile_pos} {tile}  {path}')
            if tile in tiles_mapped:
                continue
            # distance = len(path) - 1  # SAP1
            distance = path.distance  # SAP2
            if tile.isalpha() or tile == '@':
                points_to_search_paths_for.append(tile_pos)

                conn = Connection(pos=tile_pos, tile=tile, steps_to_take=distance)
                tile_to_points[current_tile][tile] = conn
                conn_back = Connection(pos=current_pos, tile=current_tile, steps_to_take=distance)
                tile_to_points[tile][current_tile] = conn_back

                print(f'    For tile {current_pos} {current_tile}  found tile {conn.pos} {conn.tile} at distance {conn.steps_to_take}')
        # print(f'points_to_search_paths_for={points_to_search_paths_for}')

    # pprint(tile_to_points)
    return tile_to_points




cdef int compute_seen_key(tuple positions, frozenset obtained_keys):
    cdef:
        list seen_key_l
        tuple seen_key
    seen_key_l = []
    for pos in positions:
        seen_key_l.extend(pos)
    seen_key_l.extend(tuple(sorted(obtained_keys)))
    seen_key = tuple(seen_key_l)
    return hash(seen_key)



cpdef void solve(list grid):
    cdef:
        list seen_key_l
        int seen_key
    original_grid = copy.deepcopy(grid)
    grid_size = (len(grid[0]), len(grid))

    starting_pos = (-1, -1)
    all_keys, all_doors = set(), set()
    for line_idx, line in enumerate(grid):
        if '@' in line:
            starting_pos = (line.index('@'), line_idx)
        line = line.replace('.', '').replace('#', '').replace('@', '')
        for k in line:
            if k.islower():
                all_keys.add(k)
            elif k.isupper():
                all_doors.add(k)
    print(f'starting at {starting_pos}  all_keys={all_keys}  all_doors={all_doors}')

    grid = [list(line) for line in original_grid]

    for c_idx, c in enumerate('@#@'):
        grid[starting_pos[1] - 1][starting_pos[0] - 1 + c_idx] = c
    for c_idx, c in enumerate('###'):
        grid[starting_pos[1]][starting_pos[0] - 1 + c_idx] = c
    for c_idx, c in enumerate('@#@'):
        grid[starting_pos[1] + 1][starting_pos[0] - 1 + c_idx] = c
    # grid[starting_pos[1] - 1][starting_pos[0] - 1: starting_pos[0] + 2][:] = '@#@'.split()
    # grid[starting_pos[1]][starting_pos[0] - 1: starting_pos[0] + 2][:] = '###'.split()
    # grid[starting_pos[1] + 1][starting_pos[0] - 1: starting_pos[0] + 2][:] = '@#@'.split()
    starting_positions = []
    for ox, oy in itertools.product((-1, 1), (-1, 1)):
        starting_positions.append((starting_pos[0] + ox, starting_pos[1] + oy))
    starting_positions = tuple(starting_positions)

    print_grid(grid)
    print(f'starting_positions={starting_positions}')

    tile_to_points = []
    for sp_idx, starting_pos in enumerate(starting_positions):
        ttp = compute_connections(grid, starting_pos)
        tile_to_points.append(ttp)
        print(f'For starting_pos[{sp_idx}]={starting_pos}  tile_to_points={pformat(ttp)}')
    # return


    Robots = collections.namedtuple(
        'Robots', [
            'robot_positions',
            'obtained_keys',
            # 'obtained_keys_order',
            'walked_distance',
        ])

    cdef dict seen = {}
    frontier = collections.deque()
    frontier.append(Robots(
        starting_positions,
        frozenset(),
        # tuple(), # obtained_keys_order
        0))
    found_solution = False
    cdef long cycle = 0
    cdef long min_solution = sys.maxsize
    cdef list solutions = []

    cdef tuple robot_pos, new_pos, new_robot_positions
    cdef str robot_tile, new_tile
    cdef list connections
    cdef int new_distance

    while frontier and not found_solution:
        cycle += 1

        robots = frontier.popleft()

        if cycle % 10000 == 0:
            print(f'cycle={cycle}  len(frontier)={len(frontier)}  robots={robots}')

        # make sure we don't walk back to where we came from
        seen_key = compute_seen_key(robots.robot_positions, robots.obtained_keys)
        # seen_key = (robots.robot_positions, tuple(sorted(robots.obtained_keys)), )
        if seen_key in seen and robots.walked_distance >= seen[seen_key]:
            continue
        seen[seen_key] = robots.walked_distance

        # current_tile = grid[robot.pos[1]][robot.pos[0]]
        # if current_tile.isalpha():
        #     if current_tile.isupper():
        #         if current_tile.lower() not in robot.obtained_keys:
        #             continue
            # elif current_tile.islower():
            #     if current_tile in robot.obtained_keys:
            #         continue

        for robot_idx in range(len(robots.robot_positions)):
            robot_pos = robots.robot_positions[robot_idx]
            robot_tile = grid[robot_pos[1]][robot_pos[0]]

            # for offset in movement_offsets:
            #     new_pos = (robot_pos[0] + offset[0], robot_pos[1] + offset[1])

            # paths = scan_all_paths2(grid, starting_pos=robot_pos)
            # for path in paths:
            #     new_pos = path.end_pos  # new_pos = path[-1]
            #     new_distance = path.distance

            connections = sorted(tile_to_points[robot_idx][robot_tile].values(), key=operator.attrgetter('steps_to_take'))
            # { DEBUG
            # if cycle == 10:
            #     print(f'for robot {robot_idx} {robot_pos} {robot_tile}  connections are {pformat(connections)}  if looking at map: {pformat(tile_to_points[robot_idx])}')
            # } DEBUG
            for connection in connections:
                new_pos = connection.pos
                new_distance = connection.steps_to_take

                # NOT FOR USE OF CONNECTIONS
                # if new_pos[0] < 0 or new_pos[0] >= grid_size[0] or new_pos[1] < 0 or new_pos[1] >= grid_size[1]:
                #     continue
                # new_tile = grid[new_pos[1]][new_pos[0]]
                # if new_tile == '#':
                #     continue
                new_tile = connection.tile

                obtained_keys = robots.obtained_keys
                # obtained_keys_order = robots.obtained_keys_order
                if new_tile.isalpha():
                    if new_tile.isupper():
                        if new_tile.lower() not in obtained_keys:
                            # print(f"Not going to tile {new_pos} {new_tile}  because we don't have the key")
                            continue
                    elif new_tile.islower():
                        # if new_tile in obtained_keys:  # commented because we can walk back
                        #     continue
                        if new_tile not in obtained_keys:
                            obtained_keys = frozenset(obtained_keys) | frozenset({new_tile, })
                            # obtained_keys_order = obtained_keys_order + (new_tile, )
                            # obtained_keys_order = obtained_keys_order + ((new_tile, robot_idx, ), )

                        if set(obtained_keys) == all_keys:
                            found_solution = obtained_keys, robots.walked_distance + new_distance
                            # found_solution = obtained_keys_order, robots.walked_distance + new_distance
                            break
                new_robot_positions = tuple(robots.robot_positions[0:robot_idx] + (new_pos, ) + robots.robot_positions[robot_idx + 1:])

                seen_key = compute_seen_key(new_robot_positions, obtained_keys)
                if seen_key in seen and robots.walked_distance + new_distance >= seen[seen_key]:
                    continue

                frontier.append(Robots(
                    new_robot_positions,
                    obtained_keys,
                    # obtained_keys_order,
                    robots.walked_distance + new_distance
                ))

    print(f'found_solution={found_solution}')



def main():
    tests = [
        # ('pb01_input00.txt', 8, ),  # ab
        # ('pb01_input01.txt', 24, ),  # abcdef
        # ('pb01_input02.txt', 32, ),  # b, a, c, d, f, e, g
        # ('pb01_input03.txt', 72, ),  # a, f, b, j, g, n, h, d, l, o, e, p, c, i, k, m
        # ('pb00_input07.txt', 17, ),
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
