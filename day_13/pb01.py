
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

from more_itertools import windowed


def n_at_a_time(iterator, n):
    iterator = iter(iterator)
    while True:
        try:
            elems = [next(iterator) for _ in range(n)]
            yield elems
        except StopIteration:
            break


def try_parse_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def gcd(a, b):
    if a < b:
        a, b = b, a
    while b:
        a, b = b, a % b
    return a


def lcm(x, y):
   lcm = (x * y) // gcd(x, y)
   return lcm



ReactionElement = collections.namedtuple('RE', 'count, elem_name')
Reaction = collections.namedtuple('Reaction', 'inputs, outputs')


def read(filepath):
    elements = []
    if os.path.isfile(filepath):
        with open(filepath) as f:
            content = f.read()
    else:
        content = filepath

    for line in content.splitlines():
        line = line.strip()
        inputs, outputs = [e.strip() for e in line.split('=>', 1)]
        outputs = [ReactionElement(*tuple(try_parse_int(v.strip()) for v in e.strip().split(' '))) for e in outputs.split(',')]
        inputs = [ReactionElement(*tuple(try_parse_int(v.strip()) for v in e.strip().split(' '))) for e in inputs.split(',')]
        elements.append(Reaction(inputs, outputs))

    return (elements, )


def solve(reactions):
    reactions_reverse = collections.defaultdict(list)
    for r in reactions:
        reactions_reverse[r.outputs[0].elem_name].append(r)

    def compute_for_needed_fuel(needed_fuel):
        needed = collections.defaultdict(int)
        needed['FUEL'] = needed_fuel
        produced = collections.defaultdict(int)


        def non_optimum_substitute(elem_name, needed, produced):
            if elem_name == 'ORE':
                return
            reaction = reactions_reverse[elem_name][0]
            needed_reactions = math.ceil(
                max(0, needed[elem_name] - produced[elem_name])
                / float(reaction.outputs[0].count))

            produced[elem_name] += needed_reactions * reaction.outputs[0].count
            # needed[elem_name] -= needed_reactions * reaction.outputs[0].count

            for input_elem in reaction.inputs:
                needed[input_elem.elem_name] += needed_reactions * input_elem.count

            for input_elem in reaction.inputs:
                non_optimum_substitute(input_elem.elem_name, needed, produced)

        result = non_optimum_substitute('FUEL', needed, produced)
        # print(f'needed={dict(needed)}  produced={dict(produced)}')
        # print(f'result={needed["ORE"]}')
        return needed["ORE"]

    have_ore = 1000000000000
    req_fuel = 1
    fuel_jump = 1
    narrowing = False
    bounds = [0, sys.maxsize]
    while True:
        needed_ore = compute_for_needed_fuel(req_fuel)
        # print(f"Trying fuel req_fuel={req_fuel} fuel_jump={fuel_jump} bounds={bounds}: needed_ore={needed_ore} {'<' if needed_ore < 1000000000000 else '>'} 1000000000000")
        if needed_ore > have_ore:
            if req_fuel < bounds[1]:
                bounds[1] = req_fuel
            narrowing = True
            fuel_jump = int(max(1, fuel_jump / 2.0))
            req_fuel -= fuel_jump
        elif needed_ore < have_ore:
            if bounds[0] < req_fuel:
                bounds[0] = req_fuel
            fuel_jump *= 2
            req_fuel += fuel_jump
        if fuel_jump == 1 and abs(bounds[1] - bounds[0]) <= 1:
            print(f'Can produce fuel: {bounds[0]}')
            break
        
    print(compute_for_needed_fuel(1))


def main():
    tests = [
        # ('pb00_input00.txt', 31, ),
        # ('pb00_input01.txt', 165, ),
        ('pb00_input02.txt', 82892753, ),  # 13312
        ('pb00_input03.txt', 5586022, ),  # 180697
        ('pb00_input04.txt', 460664, ),  # 2210736
        ('pb00_input07.txt', 17, ),
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
