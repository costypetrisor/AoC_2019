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


def read(filepath):
    elements = []
    if os.path.isfile(filepath):
        with open(filepath) as f:
            content = f.read()
    else:
        content = filepath
    content = [e.strip() for e in content.splitlines() if e.strip()]
    assert len(content) == 1
    elements = [int(e.strip()) for e in content[0].split(',')]
    return (elements, )


def solve(memory):
    computers = [
        Intcode(i, list(memory), logging.WARNING)
        for i in range(50)
    ]
    for computer in computers:
        computer.run_until_input_or_end(give_input=computer.pid)

    keep_running = True

    router = collections.defaultdict(collections.deque)
    while keep_running:
        for computer in computers[:]:
            if computer.running_state == Intcode.RunningState.Finished:
                computers.remove(computer)
                continue

            nb_packets = len(computer.output_vec) // 3
            if nb_packets:
                packets = computer.output_vec[:nb_packets * 3]
                computer.output_vec = computer.output_vec[nb_packets * 3:]
                for pkt_idx in range(nb_packets):
                    packet = packets[pkt_idx * 3: (pkt_idx + 1) * 3]
                    print(f'packet={packet}')
                    if packet[0] == 255:
                        print(f'Packet 255: {packet}')
                        return
                    router[packet[0]].append(packet)

            inbox = router[computer.pid]
            if inbox:
                packet = inbox.popleft()
                computer.run_until_input_or_end(give_input=packet[1])
                computer.run_until_input_or_end(give_input=packet[2])
            else:
                computer.run_until_input_or_end(give_input=-1)





def main():
    tests = [
        ('pb00_input00.txt', 17, ),
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
