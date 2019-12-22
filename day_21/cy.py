import pyximport; pyximport.install()

import os
import sys

cwd = os.getcwd()
if cwd not in sys.path:
    sys.path.insert(0, cwd)


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


import pb00cy as solver
# import pb01cy as solver


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
    # return (elements, 10007)
    return (elements, 119315717514047, 101741582076661)


def main():
    tests = [
        # ('pb00_input01.txt', 17, ),
        # ('pb00_input02.txt', 17, ),
        # ('pb00_input03.txt', 17, ),
        # ('pb00_input04.txt', 17, ),
        ('pb00_input00.txt', 17, ),
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
