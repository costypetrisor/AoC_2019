
import pyximport; pyximport.install()

import collections
import copy
import datetime
import functools
import itertools
import json
import logging
import math
from pprint import pformat, pprint
import re
import os
import sys
import time

import more_itertools
from more_itertools import windowed

import pb01_cy


def read(filepath):
    elements = []
    if os.path.isfile(filepath):
        with open(filepath) as f:
            content = f.read()
    else:
        content = filepath
    content = content.strip()
    elements = [int(e) for e in content]
    return (elements, )


def main():
    tests = [
        # ('12345678', 17, ),
        ('03036732577212944063491565474664', '84462026', ),
        ('02935109699940807407585447034323', '78725270', ),
        ('02935109699940807407585447034323', '53553731', ),
        ('pb00_input00.txt', 17, ),
    ]
    for test, expected in tests:
        _input = read(test)
        # res = solve(*_input)
        # res = pb01_cy.solve(*_input, nb_iterations=100, nb_repetitions=1)
        res = pb01_cy.solve_pt2(*_input, nb_iterations=100, nb_repetitions=10000)
        print(test, expected, res)

    # test = 'pb00_input01.txt'
    # _input = read(test)
    # result = solve(*_input)
    # print(result)


__name__ == '__main__' and main()
