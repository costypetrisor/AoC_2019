
import collections
import copy
import datetime
import enum
import functools
import itertools
import json
import logging
import math
from pprint import pformat, pprint
import random
import re
import os
import sys
import time

from more_itertools import windowed


def read(filepath):
    with open(filepath) as f:
        return f.read()


def parse(_input):
    elements = [int(e.strip()) for e in _input.strip().split(',')]
    return elements



class Intcode(object):

    _no_input_sentinel = object()

    class Mode(object):
        POS = 0
        IMM = 1
        REL = 2

        tstr = {
            POS: 'la',
            IMM: 'iv',
            REL: 'rv',
        }

    class RunningState(object):
        NotStarted = 0
        Running = 1
        WantsInput = 2
        Finished = 3

    def __init__(self, pid, memory, verbose=logging.WARNING):
        self.pid = pid
        self.verbose = verbose
        self.initial_memory_backup = list(memory)
        self.reset()

    def reset(self):
        self.memory = list(self.initial_memory_backup)
        self.memory.extend((0 for _ in range(10000)))  # extend memory with zeroes
        self.input_counter = 0
        self.output_vec = []
        self.pc = 0
        self.relative_base = 0
        self.cycle = 0
        self.running_state = self.RunningState.NotStarted
        self.coroutine = None

    @staticmethod
    def decode_instruction(instr):
        instr = str(instr)
        opcode = int(instr[-2:])
        modes = tuple(reversed(tuple(int(i) for i in instr[:-2])))
        if len(modes) != 3:
            modes = modes + (0, ) * (3 - len(modes))
        # print(f'decoded instr={instr}  as opcode={opcode}  modes={modes}')
        return opcode, modes

    def _run(self):
        self.running_state = self.RunningState.Running

        while True:
            instr = self.memory[self.pc]
            opcode, modes = self.decode_instruction(instr)

            if modes[0] == self.Mode.IMM:
                r0 = self.pc + 1
            elif modes[0] == self.Mode.POS:
                r0 = self.memory[self.pc + 1]
            elif modes[0] == self.Mode.REL:
                r0 = self.memory[self.pc + 1] + self.relative_base

            if modes[1] == self.Mode.IMM:
                r1 = self.pc + 2
            elif modes[1] == self.Mode.POS:
                r1 = self.memory[self.pc + 2]
            elif modes[1] == self.Mode.REL:
                r1 = self.memory[self.pc + 2] + self.relative_base

            try:
                if modes[2] == self.Mode.IMM:
                    r2 = self.pc + 3
                elif modes[2] == self.Mode.POS:
                    r2 = self.memory[self.pc + 3]
                elif modes[2] == self.Mode.REL:
                    r2 = self.memory[self.pc + 3] + self.relative_base
            except IndexError:
                pass # if this happens, you don't need it

            if self.verbose <= logging.DEBUG:
                print(f'pc={self.pc}  opcode={opcode}  modes={"".join(map(str, modes))}    r0={r0} r1={r1} r2={r2}')
            if opcode == 1:
                x1 = self.memory[r0]
                x2 = self.memory[r1]
                value = x1 + x2
                if self.verbose <= logging.DEBUG:
                    print(f'sum x1={self.Mode.tstr[modes[0]]} {x1}  x2={self.Mode.tstr[modes[1]]} {x2}  x3={self.Mode.tstr[modes[2]]} {self.memory[r2]}  value={value}')
                self.memory[r2] = value
                self.pc += 4
            elif opcode == 2:
                x1 = self.memory[r0]
                x2 = self.memory[r1]
                value = x1 * x2
                if self.verbose <= logging.DEBUG:
                    print(f'mul x1={self.Mode.tstr[modes[0]]} {x1}  x2={self.Mode.tstr[modes[1]]} {x2}  x3={self.Mode.tstr[modes[2]]} {self.memory[r2]}  value={value}')
                self.memory[r2] = value
                self.pc += 4
            elif opcode == 3:
                # value = int(input('-- Program asks for input: '))
                # value = input_vec[self.input_counter]
                self.running_state = self.RunningState.WantsInput
                value = yield
                if value is self._no_input_sentinel:
                    value = yield
                assert isinstance(value, int)
                self.running_state = self.RunningState.Running
                self.input_counter += 1
                if self.verbose <= logging.INFO:
                    print(f'-- Program {self.pid} asks for input: {value}  stores at {self.Mode.tstr[modes[0]]} {r0}')
                self.memory[r0] = value
                # print(f'Input wrote in self.memory at address {dest}  value {value}  {self.memory[dest]}')
                self.pc += 2
            elif opcode == 4:
                src = self.memory[r0]
                # print('')
                if self.verbose <= logging.DEBUG:
                    print(f'-- self.pid={self.pid} output: {src}')
                assert isinstance(src, int)
                self.output_vec.append(src)
                yield src
                # print(f'-- output: {self.memory[src]}')
                self.pc += 2
            elif opcode == 5:  # jump-if-true
                x1 = self.memory[r0]
                x2 = self.memory[r1]
                if self.verbose <= logging.DEBUG:
                    print(f'-- jump-if-true  x1={x1}  x2={x2}')
                if x1 != 0:
                    self.pc = x2
                else:
                    self.pc += 3
            elif opcode == 6:  # jump-if-false
                x1 = self.memory[r0]
                x2 = self.memory[r1]
                if self.verbose <= logging.DEBUG:
                    print(f'-- jump-if-true  x1={x1}  x2={x2}')
                if x1 == 0:
                    self.pc = x2
                else:
                    self.pc += 3
            elif opcode == 7:  # less-then
                x1 = self.memory[r0]
                x2 = self.memory[r1]
                value = 1 if x1 < x2 else 0
                if self.verbose <= logging.DEBUG:
                    print(f'-- less-then  x1={x1}  x2={x2}  value={value}')
                self.memory[r2] = value
                self.pc += 4
            elif opcode == 8:  # equals
                x1 = self.memory[r0]
                x2 = self.memory[r1]
                value = 1 if x1 == x2 else 0
                if self.verbose <= logging.DEBUG:
                    print(f'-- equals  x1={x1}  x2={x2}  value={value}')
                self.memory[r2] = value
                self.pc += 4
            elif opcode == 9:  # adjust relative base
                x1 = self.memory[r0]
                if self.verbose <= logging.DEBUG:
                    print(f'-- adj relative base  now={self.relative_base}  after {self.relative_base + x1}  x1={x1}')
                self.relative_base += x1
                self.pc += 2
            elif opcode == 99:
                self.pc += 1
                self.running_state = self.RunningState.Finished
                if self.verbose <= logging.INFO:
                    print(f'-- halt {self.pid}')
                break
            else:
                print(f'Unknown instruction  pc={self.pc}  instr={instr}  opcode={opcode}  modes={modes}')
                break
            self.cycle += 1

    def run_until_input_or_end(self, give_input=_no_input_sentinel, output_count=-1):
        oc = 0

        if not self.coroutine:
            self.coroutine = self._run()
            ov = next(self.coroutine)
            if ov is not None:
                # self.output_vec.append(ov)
                oc += 1
                if output_count > 0 and oc >= output_count:
                    return
        while True:
            try:
                ov = self.coroutine.send(give_input)
                if ov is not None:
                    # self.output_vec.append(ov)
                    oc += 1
                    if output_count > 0 and oc >= output_count:
                        # import pdb; pdb.set_trace()
                        return
                if self.running_state == self.RunningState.WantsInput:
                    return
            except StopIteration:
                return


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
    print('')
    for line in grid:
        print(''.join(line))
    print('')



class Move(enum.IntEnum):
    North = 1
    South = 2
    West = 3
    East = 4

Move_opposite = {
    Move.North: Move.South,
    Move.South: Move.North,
    Move.West: Move.East,
    Move.East: Move.West,
}


class DroidStatus(enum.IntEnum):
    Wall = 0
    Moved = 1
    OxygenSystem = 2
    Droid = 3
    EmptySpace = 4


Tile_print = {
    DroidStatus.Wall.value: '#',
    DroidStatus.Moved.value: '.',
    DroidStatus.OxygenSystem.value: 'o',
    DroidStatus.Droid.value: 'D',
    DroidStatus.EmptySpace: ' ',
}


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
move_xy.offsets = ((0, -1), (1, 0), (0, 1), (-1, 0), )

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


def spiral(size=-1):
    # for spiral_size in range(1, size, 2):
    spiral_size = 1
    while True:
        for direction in (Move.North, Move.East, Move.South, Move.West):
            move_size = spiral_size if direction not in (Move.South, Move.West, ) else (spiral_size + 1)
            for idx in range(move_size):
                yield direction
        spiral_size += 2
        if size > 0 and spiral_size > size:
            break


def explore_point_return():
    yield
    responses = {}
    mini_grid = [[' ' for _ in range(3)] for _ in range(3)]
    for direction in (Move.North, Move.East, Move.South, Move.West):
        response, droid_pos = yield direction
        # print(f'explore_point_return issued {direction}   received {DroidStatus(response)} {Tile_print[DroidStatus(response).value]}  droid_pos={droid_pos}')
        responses[direction] = (response, droid_pos)
        p = move_xy(1, 1, direction)
        mini_grid[p[1]][p[0]] = Tile_print[response]
        if response != DroidStatus.Wall.value:
            opposite_direction = Move_opposite[direction]
            response, droid_pos = yield opposite_direction
            # print(f'explore_point_return issued return {direction}   received {DroidStatus(response)} {Tile_print[DroidStatus(response).value]}  droid_pos={droid_pos}')
    print(f'explore_point_return: {responses}')
    print_grid(mini_grid)
        


def get_surroundings(grid, pos):
    walls, spaces, unexplored = [], [], []
    for offsets in move_xy.offsets:
        new_pos = (pos[0] + offsets[0], pos[1] + offsets[1])
        if grid[new_pos[1]][new_pos[0]] == Tile_print[DroidStatus.Wall.value]:
            walls.append(new_pos)
        elif grid[new_pos[1]][new_pos[0]] == Tile_print[DroidStatus.EmptySpace.value]:
            unexplored.append(new_pos)
        else:
            spaces.append(new_pos)
    return walls, spaces, unexplored


def manhattan_distance(A, B):
    return abs(A[0] - B[0]) + abs(A[1] - B[1])

def sq_distance(A, B):
    return (A[0] - B[0]) * (A[0] - B[0]) + (A[1] - B[1]) * (A[1] - B[1])

def distance(A, B):
    return math.sqrt((A[0] - B[0]) * (A[0] - B[0]) + (A[1] - B[1]) * (A[1] - B[1]))


def compute_path(start_pos, end_pos, direct_connections):
    print(f'compute_path    start_pos={start_pos}, end_pos={end_pos},')  #  direct_connections={dict(direct_connections)}
    explored_points = set(direct_connections.keys())

    distances = {p: [sys.maxsize, []] for p in explored_points}
    # distances[end_pos] = [sys.maxsize, []]  # end_pos must be adjiacent to an explored_point
    distances[start_pos] = [0, [start_pos]]
    unvisited = collections.deque([start_pos])
    found_route = False

    while unvisited:
        current_pos = unvisited.popleft()
        # visited.add(current_pos)
        current_pos_route = distances[current_pos]
        direct_conns = direct_connections[current_pos]
        # print(f'current_pos={current_pos}  current_pos_route={current_pos_route}  direct_conns={direct_conns}  unvisited={unvisited}')
        for p in direct_conns:
            p_route = distances[p]
            if p_route[0] == sys.maxsize:
                unvisited.append(p)
            if current_pos_route[0] + 1 < p_route[0]:
                p_route = [current_pos_route[0] + 1, current_pos_route[1] + [p]]
                distances[p] = p_route
            if p == end_pos:
                found_route = True
                break
        # print(f'current_pos={current_pos}  current_pos_route={current_pos_route}  direct_conns={direct_conns}  unvisited={unvisited}')
        if found_route:
            break

    route = distances[end_pos]
    assert route[0] < sys.maxsize
    return route[1][1:]



def goto_node_with_unexplored(droid_pos, grid, direct_connections):
    explored_points = set(direct_connections.keys())
    unexplored_points = set()
    unexplored_points_conns = collections.defaultdict(list)
    print(f'Explored points: {explored_points}')
    for point in explored_points:
        _, _, unexplored_to_point = get_surroundings(grid, point)
        print(f'for point {point}, unexplored={unexplored_to_point}')
        unexplored_points.update(unexplored_to_point)
        for unexplored_point in unexplored_to_point:
            unexplored_points_conns[unexplored_point].append(point)
    unexplored_points = sorted(unexplored_points, key=lambda p: manhattan_distance(droid_pos, p))
    print(f'Unexplored points: {unexplored_points}')

    new_pos = unexplored_points[0]
    new_pos_conns = unexplored_points_conns[new_pos]
    path = compute_path(droid_pos, new_pos_conns[0], direct_connections)
    path.append(new_pos)
    print(f'Path from {droid_pos} to {new_pos_conns[0]} and then {new_pos}: {path}')
    yield
    for point in path:
        direction = diff_points_to_direction(droid_pos, point)
        # print(f'goto_node_with_unexplored  travelling from {droid_pos} to {point}  issuing {direction.name}')
        _, droid_pos = yield direction
    # direction = diff_points_to_direction(droid_pos, new_pos)
    # _, droid_pos = yield direction


class NoMorePointsToExplore(Exception): pass

def goto_unexplored_point(droid_pos, direct_connections, points_to_explore, visited):
    print(f'goto_unexplored_point  droid_pos={droid_pos}')  #   points_to_explore={points_to_explore}
    while True:
        if not points_to_explore:
            raise NoMorePointsToExplore
        point_to_explore = points_to_explore.popleft()
        if point_to_explore[0] not in visited:
            break
    connections = copy.deepcopy(direct_connections)
    # for visited_point in visited:
    #     if manhattan_distance(point_to_explore, visited_point) == 1:
    #         connections[point_to_explore].append(visited_point)
    #         connections[visited_point].append(point_to_explore)
    connections[point_to_explore[0]].append(point_to_explore[1])
    connections[point_to_explore[1]].append(point_to_explore[0])
    print(f'goto_unexplored_point  picked point_to_explore={point_to_explore}')  #    connections={pformat(connections)}
    path = compute_path(droid_pos, point_to_explore[0], connections)
    print(f'Path from {droid_pos} to {point_to_explore[0]}: {path}')
    yield
    for point in path:
        direction = diff_points_to_direction(droid_pos, point)
        if not direction:
            print(f'droid_pos {droid_pos}  point={point}')
        assert direction
        print(f'goto_unexplored_point  travelling from {droid_pos} to {point}  issuing {direction.name}')
        _, droid_pos = yield direction




def solve(memory, input_vector=()):
    program = Intcode('A', memory, verbose=logging.WARNING)

    grid_size = [120, 120]
    grid = [[' ' for _ in range(grid_size[0])] for _ in range(grid_size[1])]
    droid_pos = (60, 60)
    start_pos = droid_pos
    grid[droid_pos[1]][droid_pos[0]] = DroidStatus.Droid.value

    direct_connections = collections.defaultdict(list)  # point to list of connected points (reverse entries too)
    shortest_paths = {}  # (point A, point B) to precomputed shortest path
    locations_with_unexplored_edges = [droid_pos]
    points_to_explore = collections.deque([((droid_pos[0] + offset[0], droid_pos[1] + offset[1]), droid_pos) for offset in move_xy.offsets])
    visited = {droid_pos, }

    found_oxygen_system = None
    finished = False
    last_droid_output = DroidStatus.Droid.value
    movement_program = explore_point_return()
    next(movement_program)
    movement_program_cycle = 0

    while True:
        try:
            # if movement_program_cycle == 0:
            #     direction = next(movement_program)
            # else:
            direction = movement_program.send((last_droid_output, droid_pos))
            movement_program_cycle += 1
            # try:
            # except TypeError:
            #     direction = next(movement_program)
        except StopIteration:
            # movement program ended, pick a different program
            if movement_program.__name__ == explore_point_return.__name__:
                # movement_program = goto_node_with_unexplored(droid_pos, grid, direct_connections)
                movement_program = goto_unexplored_point(droid_pos, direct_connections, points_to_explore, visited)
            elif movement_program.__name__ == goto_node_with_unexplored.__name__:
                movement_program = explore_point_return()
            elif movement_program.__name__ == goto_unexplored_point.__name__:
                movement_program = explore_point_return()
            else:
                import pdb; pdb.set_trace
                break
            movement_program_cycle = 0
            # time.sleep(0.2)
            # direction = next(movement_program)
            try:
                next(movement_program)
            except NoMorePointsToExplore:
                finished = True
                break
            direction = movement_program.send((last_droid_output, droid_pos))

        program.run_until_input_or_end(give_input=direction.value)
        if program.running_state == Intcode.RunningState.Finished:
            finished = True
            finished_spiral = True

        droid_output = program.output_vec[-1]
        if droid_output == DroidStatus.Wall.value:
            wall_pos = move_xy(*droid_pos, direction)
            grid[wall_pos[1]][wall_pos[0]] = Tile_print[DroidStatus.Wall.value]
            # finished = True
        elif droid_output in (DroidStatus.Moved.value, DroidStatus.OxygenSystem.value, ):
            grid[droid_pos[1]][droid_pos[0]] = Tile_print[DroidStatus.EmptySpace.value]
            old_droid_pos = droid_pos
            droid_pos = move_xy(*droid_pos, direction)
            print(f'Droid moved from {old_droid_pos} to {droid_pos}')
            grid[droid_pos[1]][droid_pos[0]] = Tile_print[DroidStatus.Droid.value]
            if droid_output == DroidStatus.OxygenSystem.value:
                found_oxygen_system = droid_pos
                grid[droid_pos[1]][droid_pos[0]] = Tile_print[DroidStatus.OxygenSystem.value]

            if droid_pos not in direct_connections[old_droid_pos]:
                direct_connections[old_droid_pos].append(droid_pos)
            if old_droid_pos not in direct_connections[droid_pos]:
                direct_connections[droid_pos].append(old_droid_pos)

            for offset in move_xy.offsets:
                point_to_explore = (droid_pos[0] + offset[0], droid_pos[1] + offset[1])
                if grid[point_to_explore[1]][point_to_explore[0]] != Tile_print[DroidStatus.Wall.value] and point_to_explore not in visited:
                    points_to_explore.insert(0, (point_to_explore, droid_pos))

        # elif droid_output == DroidStatus.OxygenSystem.value:
        #     found_oxygen_system = move_xy(*droid_pos, direction)
        #     droid_pos = found_oxygen_system
        #     grid[found_oxygen_system[1]][found_oxygen_system[0]] = Tile_print[DroidStatus.OxygenSystem.value]

        #     if droid_pos not in direct_connections[old_droid_pos]:
        #         direct_connections[old_droid_pos].append(droid_pos)
        #     if old_droid_pos not in direct_connections[droid_pos]:
        #         direct_connections[droid_pos].append(old_droid_pos)

            # finished = True

        visited.add(droid_pos)

        # print_grid(grid)
        # time.sleep(0.2)

        last_droid_output = droid_output
        if finished:
            break

    print_grid(grid)
    print(f'found_oxygen_system={found_oxygen_system}')

    path_from_start_to_oxygen = compute_path(start_pos, found_oxygen_system, direct_connections)
    print(f'path_from_start_to_oxygen[{len(path_from_start_to_oxygen)}]=  {path_from_start_to_oxygen}')
    grid_with_path = copy.deepcopy(grid)
    for p in path_from_start_to_oxygen:
        grid_with_path[p[1]][p[0]] = '*'
    print_grid(grid_with_path)


def main():
    tests = [
        ('pb00_input00.txt', 17, ),
    ]
    for test, expected in tests:
        if os.path.exists(test):
            test = read(test)
        memory = parse(test)
        res = solve(memory)
        # print(test, expected, res)

    # test = 'pb00_input01.txt'
    # _input = read(test)
    # result = solve(*_input)
    # print(result)


__name__ == '__main__' and main()
