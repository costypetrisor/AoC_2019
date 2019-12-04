
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
    A, B = content.split('-')
    A = int(A)
    B = int(B)
    return (A, B, )


def to_digits(N):
    return [int(d) for d in str(N)]


def meets_criteria(n_digits):
    return (
        len(n_digits) == 6 and
        # (n_digits[0] == n_digits[1] or n_digits[1] == n_digits[2] or n_digits[2] == n_digits[3] or n_digits[3] == n_digits[4] or n_digits[4] == n_digits[5]) and
        any(a == b for a, b in windowed(n_digits, 2)) and
        all(a <= b for a, b in windowed(n_digits, 2))
    )


def solve(A, B):
    count = 0
    for N in range(A + 1, B):
        N_digits = to_digits(N)
        if meets_criteria(N_digits):
            print(N)
            count += 1
    print(f"Result: {count}")
    return count


def main():
    tests = [
        ('248345-746315', 17, ),
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
