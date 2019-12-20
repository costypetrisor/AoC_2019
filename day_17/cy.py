import pyximport; pyximport.install()

import os
import sys

cwd = os.getcwd()
if cwd not in sys.path:
    sys.path.insert(0, cwd)


# if __name__ == '__main__':
#     import pb01cy
#     pb01cy.main()


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
from pprint import pformat, pprint
import re
import os
import sys
from typing import *
import time

from more_itertools import windowed


import pb01cy as solver


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


def main():
    tests = [
        # ('pb01_input00.txt', 8, ),  # ab
        # ('pb01_input01.txt', 24, ),  # abcdef
        # ('pb01_input02.txt', 32, ),  # b, a, c, d, f, e, g
        # ('pb01_input03.txt', 72, ),  # a, f, b, j, g, n, h, d, l, o, e, p, c, i, k, m
        ('pb00_input07.txt', 17, ),
    ]
    for test, expected in tests:
        _input = read(test)
        res = solver.solve(*_input)
        print(f'test={test}  expected={expected}  res={res}')

    # test = 'pb00_input01.txt'
    # _input = read(test)
    # result = solve(*_input)
    # print(result)


__name__ == '__main__' and main()
