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
import operator
from pprint import pformat, pprint
import re
import os
import sys
from typing import *
import time

from future.types import int

from more_itertools import windowed




def xgcd(a, b):
    # http://anh.cs.luc.edu/331/notes/xgcd.pdf
    # Extended Euclidian GCD Algorithm
    # https://en.wikipedia.org/wiki/Extended_Euclidean_algorithm
    # returns gcd(a, b) and x. y from g = ax + by where g= gcd(a, b)
    # x, _, g = sympy.numbers.igcdex(a, m)
    # gmpy.divm(1, 1234567, 1000000007)
    # gmpy2.invert(0,5)
    # sympy.mod_inverse(11, 35) # returns 16    sympy.mod_inverse(15, 35) # raises ValueError: 'inverse of 15 (mod 35) does not exist'
    # from Py3.8  pow(38, -1, 97)
    prevx, x = 1, 0
    prevy, y = 0, 1
    while b:
        q = a // b
        x, prevx = prevx - q * x, x
        y, prevy = prevy - q * y, y
        a, b = b, a % b
    return a, prevx, prevy

# cpdef tuple xgcd(long a, long b):
#     # http://anh.cs.luc.edu/331/notes/xgcd.pdf
#     # Extended Euclidian GCD Algorithm
#     # https://en.wikipedia.org/wiki/Extended_Euclidean_algorithm
#     # returns gcd(a, b) and x. y from g = ax + by where g= gcd(a, b)
#     # x, _, g = sympy.numbers.igcdex(a, m)
#     # gmpy.divm(1, 1234567, 1000000007)
#     # gmpy2.invert(0,5)
#     # sympy.mod_inverse(11, 35) # returns 16    sympy.mod_inverse(15, 35) # raises ValueError: 'inverse of 15 (mod 35) does not exist'
#     # from Py3.8  pow(38, -1, 97)
#     cdef long x, y, prevx, prevy
#     prevx, x = 1, 0
#     prevy, y = 0, 1
#     while b:
#         q = a // b
#         x, prevx = prevx - q * x, x
#         y, prevy = prevy - q * y, y
#         a, b = b, a % b
#     return a, prevx, prevy


def modinv(a, b):
    # https://en.wikipedia.org/wiki/Modular_multiplicative_inverse
    # a modular multiplicative inverse of an integer A is an integer x such that the product Ax is congruent to 1 with respect to the modulus m
    # 
    # a**-1 mod b
    g, x, y = xgcd(a, b)
    if g == 1:
        return x % b
    return 0

# cpdef long modinv(long a, long b):
#     # https://en.wikipedia.org/wiki/Modular_multiplicative_inverse
#     # a modular multiplicative inverse of an integer A is an integer x such that the product Ax is congruent to 1 with respect to the modulus m
#     # 
#     # a**-1 mod b
#     cdef long g, x, y
#     g, x, y = xgcd(a, b)
#     if g == 1:
#         return x % b
#     return 0




def solve(orders, N, R):
    position = 2020

    # orders.reverse()

    # start_time = time.time()
    # for r_idx in range(R):
    #     for order_idx, order in enumerate(orders):
    #         if order == 'deal into new stack':
    #             position = N - position - 1
    #         elif order.startswith('cut '):
    #             m = long(order.split()[-1])
    #             if m < 0:
    #                 m = N + m
    #             if position < m:
    #                 position = N - m + position
    #             else:
    #                 position = position - m
    #             # position = (position + m + N) % N
    #         elif order.startswith('deal with increment'):
    #             m = int(order.split()[-1])

    #             for divisor in range(0, N):
    #                 A = (divisor * N) + position
    #                 if A % m == 0:
    #                     PA = A // m
    #                     # print(f'Position {position} was dealt with increment from {PA}')
    #                     position = PA
    #                     break

    #     if r_idx % 10000 == 0:
    #         print(f'Progress: {r_idx} / {R}  {float(r_idx) / R * 100:.2f}')

    increment_mul = 1
    offset_diff = 0

    for order_idx, order in enumerate(orders):
        if order == 'deal into new stack':
            # reverse sequence & shift 1 ledt
            increment_mul = (increment_mul * -1) % N
            offset_diff = (offset_diff + increment_mul) % N
        elif order.startswith('cut '):
            m = int(order.rsplit(maxsplit=1)[-1])
            # shift m left
            offset_diff = (offset_diff + m * increment_mul) % N
        elif order.startswith('deal with increment'):
            m = int(order.rsplit(maxsplit=1)[-1])
            # diff between 2 consecutive numbers is multiplied by the mmi of the increment
            increment_mul = (increment_mul * modinv(m, N)) % N
        # print(f'  order_idx={order_idx}  increment_mul={increment_mul}  offset_diff={offset_diff}  line={order}')

    # print(f'increment_mul={increment_mul}  offset_diff={offset_diff}')

    def do_repetitions(repetitions):
        increment = pow(increment_mul, repetitions, N)
        # sum of geometric series
        offset = (1 - increment) * modinv((1 - increment_mul) % N, N)
        offset = (offset_diff % N) * (offset % N)
        return increment, offset

    increment, offset = do_repetitions(R)

    initial_position = (offset + position * increment) % N

    print(f'Result: {initial_position}')



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
        res = solve(*_input)
        print(f'test={test}  expected={expected}  res={res}')

    # test = 'pb00_input01.txt'
    # _input = read(test)
    # result = solve(*_input)
    # print(result)


__name__ == '__main__' and main()

