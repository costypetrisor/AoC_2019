
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
    final_image = [2 for _ in range(width * height)]

    for layer in layers:
        for idx in range(width * height):
            p = layer[idx]
            if final_image[idx] == 2:
                final_image[idx] = p

    for hi in range(height):
        print(''.join(map(str, final_image[hi * width: hi * width + width]))
            .replace('1', '#').replace('0', ' ')
        )


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
