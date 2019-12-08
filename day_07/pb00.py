
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
    elements = []
    if os.path.isfile(filepath):
        with open(filepath) as f:
            content = f.read()
    else:
        content = filepath
    content = content.strip()
    content = [int(e) for e in content]
    width, height = 25, 6
    layers = []
    index = 0
    slicing_content = content
    layer_length = width * height
    assert len(content) % layer_length == 0
    while index < len(content):
        slice_ = slicing_content[index: index + layer_length]
        layers.append(slice_)
        index += layer_length
    return (width, height, layers, )


def solve(width, height, layers):
    min_nb_zero = sys.maxsize
    nb_ones_on_min_zero = 0
    nb_twos_on_min_zero = 0
    for layer in layers:
        counts = collections.Counter(layer)
        # nb_zero = sum(1 if p == 0 for p in layer)
        if counts[0] < min_nb_zero:
            min_nb_zero = counts[0]
            nb_ones_on_min_zero = counts[1]
            nb_twos_on_min_zero = counts[2]

    print(f'min_nb_zero={min_nb_zero}  nb_ones_on_min_zero={nb_ones_on_min_zero}  nb_twos_on_min_zero={nb_twos_on_min_zero}')
    print(f'solution = {nb_ones_on_min_zero * nb_twos_on_min_zero}')


def main():
    tests = [
        ('pb00_input00.txt', 17, ),
    ]
    for test, expected in tests:
        _input = read(test)
        res = solve(*_input)
        print(test, expected, res)

    # test = 'pb00_input01.txt'
    # _input = read(test)
    # result = solve(*_input)
    # print(result)


__name__ == '__main__' and main()
