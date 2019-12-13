
import collections
import datetime
import enum
import functools
import itertools
import json
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


def decode_instruction(instr):
    instr = str(instr)
    opcode = int(instr[-2:])
    modes = list(reversed(tuple(int(i) for i in instr[:-2])))
    if len(modes) != 3:
        for i in range(len(modes), 3):
            modes.append(0)
    # print(f'decoded instr={instr}  as opcode={opcode}  modes={modes}')
    return opcode, modes


class Mode(object):
    POS = 0
    IMM = 1
    REL = 2

    tstr = {
        POS: 'la',
        IMM: 'iv',
        REL: 'rv',
    }


def intcode(pid, memory, verbose=True):
    initial_memory_backup = list(memory)
    memory.extend((0 for _ in range(10000)))  # extend memory with zeroes
    input_counter = 0
    output_vec = []

    pc = 0
    relative_base = 0
    cycle = 0
    while True:
        instr = memory[pc]
        opcode, modes = decode_instruction(instr)

        if modes[0] == Mode.IMM:
            r0 = pc + 1
        elif modes[0] == Mode.POS:
            r0 = memory[pc + 1]
        elif modes[0] == Mode.REL:
            r0 = memory[pc + 1] + relative_base

        if modes[1] == Mode.IMM:
            r1 = pc + 2
        elif modes[1] == Mode.POS:
            r1 = memory[pc + 2]
        elif modes[1] == Mode.REL:
            r1 = memory[pc + 2] + relative_base

        try:
            if modes[2] == Mode.IMM:
                r2 = pc + 3
            elif modes[2] == Mode.POS:
                r2 = memory[pc + 3]
            elif modes[2] == Mode.REL:
                r2 = memory[pc + 3] + relative_base
        except IndexError:
            pass # if this happens, you don't need it

        if verbose:
            print(f'pc={pc}  opcode={opcode}  modes={"".join(map(str, modes))}    r0={r0} r1={r1} r2={r2}')
        if opcode == 1:
            x1 = memory[r0]
            x2 = memory[r1]
            value = x1 + x2
            if verbose:
                print(f'sum x1={Mode.tstr[modes[0]]} {x1}  x2={Mode.tstr[modes[1]]} {x2}  x3={Mode.tstr[modes[2]]} {memory[r2]}  value={value}')
            memory[r2] = value
            pc += 4
        elif opcode == 2:
            x1 = memory[r0]
            x2 = memory[r1]
            value = x1 * x2
            if verbose:
                print(f'mul x1={Mode.tstr[modes[0]]} {x1}  x2={Mode.tstr[modes[1]]} {x2}  x3={Mode.tstr[modes[2]]} {memory[r2]}  value={value}')
            memory[r2] = value
            pc += 4
        elif opcode == 3:
            # value = int(input('-- Program asks for input: '))
            # value = input_vec[input_counter]
            value = yield
            assert isinstance(value, int)
            input_counter += 1
            # if verbose:
            print(f'-- Program {pid} asks for input: {value}  stores at {Mode.tstr[modes[0]]} {r0}')
            memory[r0] = value
            # print(f'Input wrote in memory at address {dest}  value {value}  {memory[dest]}')
            pc += 2
        elif opcode == 4:
            # if len(output_vec) % 3 == 2 and output_vec[-1] == 22:
                # memory[r0] = Tile.Wall.value
                # import pdb; pdb.set_trace()
            src = memory[r0]
            # print('')
            # if verbose:
            # print(f'-- pid={pid} output: {src}')
            assert isinstance(src, int)
            output_vec.append(src)
            yield src
            # print(f'-- output: {memory[src]}')
            pc += 2
        elif opcode == 5:  # jump-if-true
            x1 = memory[r0]
            x2 = memory[r1]
            if verbose:
                print(f'-- jump-if-true  x1={x1}  x2={x2}')
            if x1 != 0:
                pc = x2
            else:
                pc += 3
        elif opcode == 6:  # jump-if-false
            x1 = memory[r0]
            x2 = memory[r1]
            if verbose:
                print(f'-- jump-if-true  x1={x1}  x2={x2}')
            if x1 == 0:
                pc = x2
            else:
                pc += 3
        elif opcode == 7:  # less-then
            x1 = memory[r0]
            x2 = memory[r1]
            value = 1 if x1 < x2 else 0
            if verbose:
                print(f'-- less-then  x1={x1}  x2={x2}  value={value}')
            memory[r2] = value
            pc += 4
        elif opcode == 8:  # equals
            x1 = memory[r0]
            x2 = memory[r1]
            value = 1 if x1 == x2 else 0
            if verbose:
                print(f'-- equals  x1={x1}  x2={x2}  value={value}')
            memory[r2] = value
            pc += 4
        elif opcode == 9:  # adjust relative base
            x1 = memory[r0]
            if verbose:
                print(f'-- adj relative base  now={relative_base}  after {relative_base + x1}  x1={x1}')
            relative_base += x1
            pc += 2
        elif opcode == 99:
            pc += 1
            if verbose:
                print(f'-- halt {pid}')
            break
        else:
            print(f'Unknown instruction  pc={pc}  instr={instr}  opcode={opcode}  modes={modes}')
            break
        cycle += 1
        # if cycle == 100:
        #     return
        # print(memory)

    # return output_vec


class Tile(enum.Enum):
    Empty = 0
    Wall = 1
    Block = 2
    HorizontalPaddle = 3
    Ball = 4

Tile_print = {
    Tile.Empty.value: ' ',
    Tile.Wall.value: '#',
    Tile.Block.value: '@',
    Tile.HorizontalPaddle.value: '_',
    Tile.Ball.value: '*',
}


class Joystick(enum.Enum):
    Neutral = 0
    Left = -1
    Right = 1


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
    for line in grid:
        print(''.join(line))


def solve(memory, input_vector=()):
    memory[0] = 2
    output_vector = []

    program = intcode('A', memory, verbose=False)
    while True:
        try:
            output_vector.append(next(program))
            assert output_vector[-1] is not None
            # if len(output_vector) % 3 == 0 and output_vector[-3] == 0:
            #     import pdb; pdb.set_trace()
        except StopIteration:
            break
        if len(output_vector) == 3105:
            break
    # # output_vector.append(next(program))
    # ov = program.send(random.choice(list(Joystick)).value)
    # assert ov is not None
    # output_vector.append(ov)
    # output_vector.append(next(program))
    # output_vector.append(next(program))

    elements = []
    for i in range(len(output_vector) // 3):
        elem = list(output_vector[3 * i: 3 * (i + 1)])
        elements.append(elem)
        if elem[0] == -1 and elem[1] == 0:
            print(f'New score: {elem[2]}')

    block_count = 0
    for elem in elements:
        if elem[2] == Tile.Block.value:
            block_count += 1
    print(f'Block tile count: {block_count}')

    min_x, max_x, min_y, max_y = min_max_grid_coords(elements)
    print(min_x, max_x, min_y, max_y)

    grid = make_grid(elements, min_x, max_x, min_y, max_y)
    print_grid(grid)

    new_output_vector  = []
    while True:
        try:
            ov = program.send(Joystick.Neutral.value)
            # ov = program.send(random.choice(list(Joystick)).value)
            if ov is not None:
                new_output_vector.append(ov)
            # new_output_vector.append(next(program))
            # new_output_vector.append(next(program))

            try:
                if new_output_vector[-3] == -1 and new_output_vector[-2] == 0:
                    print(f'New score: {new_output_vector[-1]}')
            except IndexError:
                pass
        except StopIteration:
            break
    print(len(new_output_vector))




def main():
    tests = [
        # ('pb00_input00_untouched.txt', 17, ),
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
