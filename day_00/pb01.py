
import collections
import datetime
import functools
import itertools
import json
import math
from pprint import pformat, pprint
import re
import sys
import time

from more_itertools import windowed


def read(filepath):
    elements = []
    with open(filepath) as f:
        for line in f:
            e = int(line.strip())
            elements.append(e)
    return (elements, )


def solve(_input):
    S = 0
    for e in _input:
        me = 0
        f = e
        f = f // 3 - 2
        while f > 0:
            me += f
            f = f // 3 - 2

        print(e, me)
        S += me
    return S

def main():
    tests = [
        ([14], 2),
        ([1969], 966),
        ([100756], 50346),
        # ('pb00_input00.txt', 17, ),
    ]
    for test, expected in tests:
        # _input = read(test)
        res = solve(test)
        print(test, expected, res)

    _input = read('pb00_input00.txt')
    print(_input)
    res = solve(_input[0])
    print(res)

    # test = 'pb00_input01.txt'
    # _input = read(test)
    # result = solve(*_input)
    # print(result)


__name__ == '__main__' and main()
