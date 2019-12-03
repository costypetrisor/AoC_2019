
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


def solve(_input):
    memory = _input
    original_memory = list(memory)

    for A, B in itertools.product(range(100), range(100)):
        memory = list(original_memory)
        memory[1] = A
        memory[2] = B
        pc = 0
        counter = 0
        while True:
            instr = memory[pc]
            x1, x2, x3 = memory[pc + 1: pc + 4]
            if instr == 1:
                memory[x3] = memory[x1] + memory[x2]
                pc += 4
            elif instr == 2:
                memory[x3] = memory[x1] * memory[x2]
                pc += 4
            elif instr == 99:
                pc += 1
                # print('halt')
                break
            else:
                print(f'Unknown instruction {instr}')
            counter += 1
            # if counter == 100:
            #     return
            # print(memory)
        if memory[0] == 19690720:
            print(f'A= {A}  B={B}')
            return




def main():
    tests = [
        # ('1,9,10,3,2,3,11,0,99,30,40,50', 1 ),
        ('pb00_input00.txt', 17, ),
    ]
    for test, expected in tests:
        if os.path.exists(test):
            test = read(test)
        _input = parse(test)
        res = solve(_input)
        # print(test, expected, res)

    # test = 'pb00_input01.txt'
    # _input = read(test)
    # result = solve(*_input)
    # print(result)


__name__ == '__main__' and main()
