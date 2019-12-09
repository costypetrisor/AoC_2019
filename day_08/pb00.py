
import collections
import datetime
import functools
import itertools
import json
import math
from pprint import pformat, pprint
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
            src = memory[r0]
            # print('')
            # if verbose:
            print(f'-- pid={pid} output: {src}')
            # output_vec.append(src)
            assert isinstance(src, int)
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


def solve(memory, input_vector=()):

    input_vector = [2, ]
    output_vector = []

    program = intcode('A', memory, verbose=True)
    output_vector.append(next(program))

    # while True:
    #     try:
    #         ov = next(program)
    #         print(ov)
    #     except StopIteration:
    #         break

    for iv in input_vector:
        ov = program.send(iv)
        output_vector.append(ov)
        print(ov)
    # try:
    #     ov = next(program)
    # except StopIteration:
    #     pass
    while True:
        try:
            ov = next(program)
            output_vector.append(ov)
            print(ov)
        except StopIteration:
            break
    print(f'output_vector  {output_vector}')




def main():
    tests = [
        # ('109,1,204,-1,1001,100,1,100,1008,100,16,101,1006,101,0,99', 17, ),  # copy of iteself
        # ('1102,34915192,34915192,7,4,7,99,0', 17, ),  # 16 digit number
        # ('104,1125899906842624,99', 17, ),  # that big number in the middle
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
