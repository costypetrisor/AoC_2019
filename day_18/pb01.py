
import bisect
import collections
import copy
import datetime
import dataclasses
import enum
import functools
import itertools
import json
import logging
import math
import pickle
from pprint import pformat, pprint
import random
import re
import os
import sys
import time

import more_itertools
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
        self.memory.extend((0 for _ in range(100)))  # extend memory with zeroes
        self.input_counter = 0
        self.read_input_vec = []
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
                self.read_input_vec.append(value)
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
    # print('------------------------------------------------------------------------')
    for line in grid:
        print(''.join(line))
    # print('------------------------------------------------------------------------')




def get_beam(memory, x, y):
    program = Intcode('A', list(memory), verbose=logging.WARNING)
    program.run_until_input_or_end(give_input=x)
    program.run_until_input_or_end(give_input=y)
    program.run_until_input_or_end()
    ov = program.output_vec[-1]
    assert len(program.output_vec) == 1
    return ov


BEAM_BOUNDS_BY_ROW = {}


def read_row(memory, row_idx, starting_from=0):
    global BEAM_BOUNDS_BY_ROW
    if row_idx in BEAM_BOUNDS_BY_ROW:
        return BEAM_BOUNDS_BY_ROW[row_idx]
    col_idx = starting_from
    found_beam = -1
    end_beam = sys.maxsize
    while True:
        ov = get_beam(memory, row_idx, col_idx)
        if starting_from == col_idx and ov == 1:
            starting_from = int(max(1, starting_from / 2.0))
            col_idx = starting_from
            continue
        if found_beam > 0 and ov == 0:
            end_beam = col_idx
            break
        if ov == 1 and found_beam < 0:
            found_beam = col_idx
            searched_rows = sorted(BEAM_BOUNDS_BY_ROW.keys())
            idx = bisect.bisect_left(searched_rows, row_idx)
            if 0 <= idx - 1 < len(searched_rows):
                _, col_idx = BEAM_BOUNDS_BY_ROW[searched_rows[idx - 1]] 
                col_idx -= 1
                col_idx = max(col_idx, found_beam)

        col_idx += 1

    BEAM_BOUNDS_BY_ROW[row_idx] = (found_beam, end_beam)
    # print(f'read_row  row_idx={row_idx} {BEAM_BOUNDS_BY_ROW[row_idx]}  {line}')
    return found_beam, end_beam



def place_target_square(memory, target_square, row):
    current_location = [row, 0]
    higher_beam_bounds = read_row(memory, current_location[0], starting_from=0)
    # print(f"place_target_square  row={row}  higher_beam_bounds={higher_beam_bounds}")
    if higher_beam_bounds[1] - higher_beam_bounds[0] < target_square[1]:
        return None
    lower_beam_bounds = read_row(memory, current_location[0] + target_square[0] - 1, starting_from=higher_beam_bounds[0])
    wiggle_room = higher_beam_bounds[1] + 1 - target_square[1] - lower_beam_bounds[0]
    # print(f"place_target_square  row={row}  higher_beam_bounds={higher_beam_bounds}  low_row={current_location[0] + target_square[0] - 1} lower_beam_bounds={lower_beam_bounds}  wiggle_room={wiggle_room}")
    if wiggle_room < 0:
        return None
    for col_offset in range(wiggle_room):
        possible_square_location = (current_location[0], lower_beam_bounds[0] + col_offset)
        # print(f"place_target_square  row={row}  higher_beam_bounds={higher_beam_bounds}  low_row={current_location[0] + target_square[0] - 1} lower_beam_bounds={lower_beam_bounds}  wiggle_room={wiggle_room}  final={possible_square_location}")
        if lower_beam_bounds[0] <= possible_square_location[1] and possible_square_location[1] + target_square[1] - 1 < higher_beam_bounds[1]:
            return possible_square_location




def solve(memory, input_vector=()):
    target_square = (100, 100)

    def print_snapshot(current_location, margin=2):
        min_row, max_row, min_col, max_col = sys.maxsize, 0, sys.maxsize, 0
        if current_location[0] < min_row:
            min_row = current_location[0]
        if current_location[1] < min_col:
            min_col = current_location[1]
        if current_location[0] + target_square[0] > max_row:
            max_row = current_location[0] + target_square[0]
        if current_location[1] + target_square[1] > max_col:
            max_col = current_location[1] + target_square[1]
        row_beam_bounds = {}
        # for row in range(current_location[0] - margin, current_location[0] + target_square[0] + margin):
        for row in itertools.chain(
                range(current_location[0] - margin, current_location[0] + margin),
                range(current_location[0] + target_square[0] - margin, current_location[0] + target_square[0] + margin),
            ):
            beam_bounds = read_row(memory, row, starting_from=current_location[1] - 5)
            row_beam_bounds[row] = beam_bounds
            if row < min_row:
                min_row = row
            if row > max_row:
                max_row = row
            if beam_bounds[0] < min_col:
                min_col = beam_bounds[0]
            if beam_bounds[1] > max_col:
                max_col = beam_bounds[1]
        # grid = [['.' for _ in range(max_col - min_col + 1 + 2 * margin)] for _ in range(max_row - min_row + 1 + 2 * margin)]
        grid = {row: ['.' for _ in range(max_col - min_col + 1 + 2 * margin)] for row in row_beam_bounds}
        grid_size = (max_col - min_col + 1 + 2 * margin, len(grid))
        offset_row = min_row - margin
        offset_col = min_col - margin
        # print(f'grid_size={grid_size}  offset_row={offset_row}  offset_col={offset_col}')

        # for row in range(current_location[0] - margin, current_location[0] + target_square[0] + margin):
        for row in row_beam_bounds:
            # beam_bounds = read_row(memory, row, starting_from=current_location[1] - 5)
            beam_bounds = row_beam_bounds[row]
            # print(f'at row {row}  beam_bounds={beam_bounds}')
            for col in range(beam_bounds[0], beam_bounds[1]):
                # grid[row - offset_row][col - offset_col] = '#'
                grid[row][col - offset_col] = '#'
        # print_grid(grid)
        for row in range(current_location[0], current_location[0] + target_square[0]):
            if row not in row_beam_bounds: continue
        # for row in row_beam_bounds:
            for col in range(current_location[1], current_location[1] + target_square[1]):
                # if grid[row - offset_row][col - offset_col] != '#':
                #     grid[row - offset_row][col - offset_col] = 'X'
                # else:
                #     grid[row - offset_row][col - offset_col] = 'O'
                if grid[row][col - offset_col] != '#':
                    grid[row][col - offset_col] = 'X'
                else:
                    grid[row][col - offset_col] = 'O'

        grid = [grid[row] for row in sorted(row_beam_bounds.keys())]
        print_grid(grid)

    first_beam = None
    grid = [['.' for _ in range(50)] for _ in range(50)]
    for row_idx in range(50):
        for col_idx in range(50):
            if get_beam(memory, row_idx, col_idx) == 1:
                if not first_beam and (row_idx, col_idx) != (0, 0):
                    first_beam = (row_idx, col_idx, )
                grid[row_idx][col_idx] = '#'
                # break
        # if first_beam:
        #     break
    print_grid(grid)
    print(f"first_beam={first_beam}")


    narrowing = False
    location_jump = 1
    cycle = 0
    row = first_beam[0]
    row_bounds = [0, sys.maxsize]
    past_possible_locations = collections.defaultdict(set)

    while True:
        cycle += 1
        if cycle > 1000:
            raise Exception
        if row > 10000:
            raise Exception

        print(f'Trying to find beam at row {row}  row_bounds={row_bounds}')
        square = place_target_square(memory, target_square, row)
        if square:
            print(f'Too large beam, narrowing')
            if row < row_bounds[1]:
                row_bounds[1] = row
            location_jump = int(max(1, location_jump / 2.0))
            row -= location_jump
        else:
            print(f'Too small beam, enlarging')
            if row > row_bounds[0]:
                row_bounds[0] = row
            location_jump *= 2
            row += location_jump

        if abs(row_bounds[1] - row_bounds[0]) <= 16:  # 50 because between a large interval of a consecutive rows, a target_square 
            break

    for row in range(*row_bounds):
        print(f'Trying to find beam at row {row}')
        square = place_target_square(memory, target_square, row)
        if square:
            break

    print(f'Result: {10000 * square[0] + square[1]}')
    print_snapshot(square)
    return






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



