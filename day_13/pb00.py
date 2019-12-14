
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

    # def substitute(pool):
    #     # print(f'------- substitute {pool}')
    #     while True:
    #         if len(pool) == 1 and tuple(pool.keys())[0] == 'ORE':
    #             # print(f'--- returning {pool}')
    #             return pool
    #         min_elem_ore = sys.maxsize
    #         min_elem = None
    #         min_elem_pool = None

    #         for elem_name, elem_count in pool.items():  # TODO order of reaction application
    #             if elem_name == 'ORE':
    #                 continue
    #             elem_pool = copy.copy(pool)

    #             reactions_that_produce_element = reactions_reverse[elem_name]

    #             min_reaction_ore = sys.maxsize
    #             min_reaction_pool = None

    #             for r in reactions_that_produce_element:
    #                 needed_reactions = elem_count // r.outputs[0].count
    #                 if elem_count % r.outputs[0].count != 0:
    #                     needed_reactions += 1

    #                 new_pool = copy.copy(elem_pool)
    #                 new_pool.pop(elem_name)
    #                 for ie in r.inputs:
    #                     new_pool[ie.elem_name] = new_pool.get(ie.elem_name, 0) + needed_reactions * ie.count

    #                 r = substitute(new_pool)
    #                 assert len(r) == 1
    #                 if r['ORE'] < min_reaction_ore:
    #                     min_reaction_ore = r['ORE']
    #                     min_reaction_pool = new_pool

    #             elem_pool = min_reaction_pool

    #             r = substitute(elem_pool)
    #             assert len(r) == 1
    #             if r['ORE'] < min_elem_ore:
    #                 min_elem_ore = r['ORE']
    #                 min_elem_pool = elem_pool
    #                 min_elem = elem_name, elem_count

    #         pool = min_elem_pool

    #     # print(f'--- returning {pool}')
    #     return pool

    # pool = collections.defaultdict(int)
    # pool['FUEL'] = 1
    # result = substitute(pool)
    # print(f'result={dict(result)}   pool={dict(pool)}')

    needed = collections.defaultdict(int)
    needed['FUEL'] = 1
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
    print(f'result={needed["ORE"]}')


def main():
    tests = [
        ('pb00_input00.txt', 31, ),
        ('pb00_input01.txt', 165, ),
        ('pb00_input02.txt', 13312, ),
        ('pb00_input03.txt', 180697, ),
        ('pb00_input04.txt', 2210736, ),
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
