
import collections
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

    program = Intcode('A', memory, verbose=logging.WARNING)
    program.run_until_input_or_end(output_count=3105)

    elements = []
    print(len(program.output_vec))
    for i in range(len(program.output_vec) // 3):
        elem = list(program.output_vec[3 * i: 3 * (i + 1)])
        elements.append(elem)
        if elem[0] == -1 and elem[1] == 0:
            print(f'New score: {elem[2]}')
    program.output_vec = []

    paddle_pos_x = 0
    ball_pos_x = 0
    block_count = 0
    for elem in elements:
        if elem[2] == Tile.Ball.value:
            ball_pos_x = elem[0]
        elif elem[2] == Tile.HorizontalPaddle.value:
            paddle_pos_x = elem[0]
        elif elem[2] == Tile.Block.value:
            block_count += 1
    print(f'Block tile count: {block_count}')

    min_x, max_x, min_y, max_y = min_max_grid_coords(elements)
    print(min_x, max_x, min_y, max_y)

    grid = make_grid(elements, min_x, max_x, min_y, max_y)
    print_grid(grid)

    last_output_pos = 0
    high_score = 0
    while program.running_state != Intcode.RunningState.Finished:
        # program.run_until_input_or_end(Joystick.Neutral.value)
        joy = Joystick.Neutral.value
        if ball_pos_x > paddle_pos_x:
            joy = Joystick.Right.value
        elif ball_pos_x < paddle_pos_x:
            joy = Joystick.Left.value
        program.run_until_input_or_end(joy)

        for i in range(last_output_pos, len(program.output_vec), 3):
            # print(program.output_vec[i: i + 3], end=', ')
            if program.output_vec[i] == -1 and program.output_vec[i + 1] == 0:
                score = program.output_vec[i + 2]
                if score > high_score:
                    high_score = score
            else:
                x, y, tile = program.output_vec[i: i + 3]
                grid[y][x] = Tile_print[tile]
                if tile == Tile.Ball.value:
                    ball_pos_x = x
                elif tile == Tile.HorizontalPaddle.value:
                    paddle_pos_x = x
        last_output_pos = len(program.output_vec)
        # print('')

        os.system('clear')
        print_grid(grid)
        time.sleep(0.01)

    print(f'High score: {high_score}')




def main():
    tests = [
        ('pb00_input00_untouched.txt', 17, ),
        # ('pb00_input00.txt', 17, ),
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
