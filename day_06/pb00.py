
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



def intcode(memory, input_vec):
    print(input_vec)
    input_counter = 0
    output_vec = []

    pc = 0
    cycle = 0
    while True:
        instr = memory[pc]
        opcode, modes = decode_instruction(instr)
        print(f'pc={pc}  opcode={opcode}  modes={"".join(map(str, modes))}')
        if opcode == 1:
            x1 = memory[pc + 1] if modes[0] == 1 else memory[memory[pc + 1]]
            x2 = memory[pc + 2] if modes[1] == 1 else memory[memory[pc + 2]]
            value = x1 + x2
            print(f'sum x1={"iv" if modes[0] == 1 else "la"} {memory[pc + 1]}  x2={"iv" if modes[1] == 1 else "la"} {memory[pc + 2]}  x3={"iv" if modes[2] == 1 else "la"} {memory[pc + 3]}  value={value}')
            # import pdb; pdb.set_trace()
            if modes[2] == 1:
                memory[pc + 3] = value
            else:
                memory[memory[pc + 3]] = value
            pc += 4
        elif opcode == 2:
            x1 = memory[pc + 1] if modes[0] == 1 else memory[memory[pc + 1]]
            x2 = memory[pc + 2] if modes[1] == 1 else memory[memory[pc + 2]]
            value = x1 * x2
            print(f'mul x1={"iv" if modes[0] == 1 else "la"} {memory[pc + 1]}  x2={"iv" if modes[1] == 1 else "la"} {memory[pc + 2]}  x3={"iv" if modes[2] == 1 else "la"} {memory[pc + 3]}  value={value}')
            if modes[2] == 1:
                memory[pc + 3] = value
            else:
                memory[memory[pc + 3]] = value
            pc += 4
        elif opcode == 3:
            # dest = memory[pc + 1] if modes[0] == 1 else memory[memory[pc + 1]]
            dest = memory[pc + 1]
            # value = int(input('-- Program asks for input: '))
            value = input_vec[input_counter]
            input_counter += 1
            print(f'-- Programs asks for input: {value}  stores at {"iv" if modes[0] == 1 else "la"} {memory[pc + 1]}')
            memory[dest] = value
            # print(f'Input wrote in memory at address {dest}  value {value}  {memory[dest]}')
            pc += 2
        elif opcode == 4:
            src = memory[pc + 1] if modes[0] == 1 else memory[memory[pc + 1]]
            # src = memory[pc + 1]
            # print('')
            print(f'-- output: {src}')
            output_vec.append(src)
            # print(f'-- output: {memory[src]}')
            pc += 2
        elif opcode == 5:
            x1 = memory[pc + 1] if modes[0] == 1 else memory[memory[pc + 1]]
            x2 = memory[pc + 2] if modes[1] == 1 else memory[memory[pc + 2]]
            if x1 != 0:
                pc = x2
            else:
                pc += 3
        elif opcode == 6:
            x1 = memory[pc + 1] if modes[0] == 1 else memory[memory[pc + 1]]
            x2 = memory[pc + 2] if modes[1] == 1 else memory[memory[pc + 2]]
            if x1 == 0:
                pc = x2
            else:
                pc += 3
        elif opcode == 7:
            x1 = memory[pc + 1] if modes[0] == 1 else memory[memory[pc + 1]]
            x2 = memory[pc + 2] if modes[1] == 1 else memory[memory[pc + 2]]
            value = 1 if x1 < x2 else 0
            if modes[2] == 1:
                memory[pc + 3] = value
            else:
                memory[memory[pc + 3]] = value
            pc += 4
        elif opcode == 8:
            x1 = memory[pc + 1] if modes[0] == 1 else memory[memory[pc + 1]]
            x2 = memory[pc + 2] if modes[1] == 1 else memory[memory[pc + 2]]
            value = 1 if x1 == x2 else 0
            if modes[2] == 1:
                memory[pc + 3] = value
            else:
                memory[memory[pc + 3]] = value
            pc += 4
        elif opcode == 99:
            pc += 1
            print('-- halt')
            break
        else:
            print(f'Unknown instruction  pc={pc}  instr={instr}  opcode={opcode}  modes={modes}')
            break
        cycle += 1
        # if cycle == 100:
        #     return
        # print(memory)

    return output_vec


def solve(memory):

    highest_signal = 0
    highest_phase_settting = None
    for phase_settings in itertools.permutations(range(0, 5), 5):
        print(f'phase_settings={phase_settings}')

        input_signal = 0
        for phase in phase_settings:
            input_vec = [phase, input_signal]

            memory_copy = list(memory)
            output_vec = intcode(memory_copy, input_vec)
            input_signal = output_vec[0]

        if input_signal > highest_signal:
            highest_signal = input_signal
            highest_phase_settting = phase_settings

    print(f'highest_signal={highest_signal}  highest_phase_settting={highest_phase_settting}')
    return highest_signal




def main():
    tests = [
        # ('1,9,10,3,2,3,11,0,99,30,40,50', 1 ),
        # ('3,15,3,16,1002,16,10,16,1,16,15,15,4,15,99,0,0', 43210, ),
        # ('3,23,3,24,1002,24,10,24,1002,23,-1,23,101,5,23,23,1,24,23,23,4,23,99,0,0', 54321, ),
        # ('3,31,3,32,1002,32,10,32,1001,31,-2,31,1007,31,0,33,1002,33,7,33,1,33,31,31,1,32,31,31,4,31,99,0,0,0', 65210, ),
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
