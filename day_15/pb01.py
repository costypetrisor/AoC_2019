
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


# @functools.lru_cache
def pattern(position):
    base_pattern = [0, 1, 0, -1, ]
    assert position > 0
    repeat_pattern = []
    for e in base_pattern:
        repeat_pattern.extend([e] * position)
    first_value = repeat_pattern[0]
    del repeat_pattern[0]
    repeat_pattern.append(first_value)
    yield from itertools.cycle(repeat_pattern)


def apply_pattern(elements, application, patterns):
    new_elements = []
    for i in range(len(elements)):
        s = 0
        # for e, p in zip(elements, pattern(i + 1)):
        for e, p in zip(elements, patterns[i]):
            # print(f"For elem idx {i}: {e} * {p}")
            s += e * p
        # print(f"For elem idx sum is {s}")
        new_elements.append(abs(s) % 10)
    return new_elements




def solve(elements):
    # PATTERNS = {i: more_itertools.take(len(elements), pattern(i)) for i in range(1, len(elements))}
    PATTERNS = [more_itertools.take(len(elements), pattern(i)) for i in range(1, len(elements) + 1)]

    for i in range(1, 10000 + 1):
        new_elements = apply_pattern(elements, i, PATTERNS)
        # print(f"{''.join(map(str, elements))} becomes {''.join(map(str, new_elements))}")
        elements = new_elements
        if i % 100 == 0:
            print(f'Iteration {i}')

    first_seven = elements[:7]
    first_seven = int(''.join(map(str, first_seven)))
    print(f"Message offset {first_seven}")

    value = elements[first_seven: first_seven + 8]
    value_str = ''.join(map(str, value))
    print(f'Hidden value: {value}')

    return value_str




def main():
    tests = [
        # ('12345678', 17, ),
        # ('03036732577212944063491565474664', '84462026', ),
        # ('02935109699940807407585447034323', '78725270', ),
        # ('02935109699940807407585447034323', '53553731', ),
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
