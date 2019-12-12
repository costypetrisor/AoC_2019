
import collections
import copy
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

# Io, Europa, Ganymede, Callisto


class Moon:
    def __init__(self, moon_idx, px, py, pz):
        self.idx = moon_idx
        self.pos = [px, py, pz]
        self.vel = [0, 0, 0]
        # self.px, self.py, self.pz = px, py, pz
        # self.vx, self.vy, self.vz = 0, 0, 0

    def __str__(self):
        return f'pos=<x={self.pos[0]:3d}, y={self.pos[1]:3d}, z={self.pos[2]:3d}>, vel=<x={self.vel[0]:3d}, y={self.vel[1]:3d}, z={self.vel[2]:3d}>'

    def calc_energy(self):
        pot_energy = sum(abs(e) for e in self.pos)
        kin_energy = sum(abs(e) for e in self.vel)
        energy = pot_energy * kin_energy
        return energy

    def format_energy(self):
        return f'pot: {self.pos[0]} + {self.pos[1]} + {self.pos[2]} = {sum(self.pos):2};  kin: {self.vel[0]} + {self.vel[1]} + {self.vel[2]} = {sum(self.vel):2};  total = {sum(self.pos):2} * {sum(self.vel):2} = {sum(self.pos) + sum(self.vel):2}'

    def __hash__(self):
        return hash((self.idx, ) + tuple(self.pos) + tuple(self.vel))




def read(filepath):
    elements = []
    if os.path.isfile(filepath):
        with open(filepath) as f:
            content = f.read()
    else:
        content = filepath
    content = [e.strip() for e in content.strip().splitlines() if e.strip()]
    assert len(content) == 4

    moons = []
    for idx, line in enumerate(content):
        m = re.search(r'(?i)<x=([+-]?\d+),\s*y=([+-]?\d+),\s*z=([+-]?\d+)>', line)
        assert m
        moon = Moon(idx, int(m.group(1)), int(m.group(2)), int(m.group(3)))
        moons.append(moon)

    return (moons, )


def gcd(a, b):
    if a < b:
        a, b = b, a
    while b:
        a, b = b, a % b
    return a


def lcm(x, y):
   lcm = (x * y) // gcd(x, y)
   return lcm


def solve(moons):
    orig_moons = copy.deepcopy(moons)
    step_idx = 0
    print(f'After {step_idx} steps:')
    for moon in moons:
        print(str(moon))

    moon_axis_states = [list() for _ in range(3)]
    moon_axis_states_sets = [set() for _ in range(3)]
    for axis in range(3):
        h = hash(tuple(m.pos[axis] for m in moons) + tuple(m.vel[axis] for m in moons))
        moon_axis_states[axis].append(h)
        moon_axis_states_sets[axis].add(h)
    moon_axis_found = [-1, -1, -1]

    while True:
        step_idx += 1

        moons = [copy.copy(moon) for moon in moons]

        for moon in moons:
            for other_moon in moons:
                if moon.idx == other_moon.idx:
                    continue
                for idx in range(3):
                    if moon.pos[idx] < other_moon.pos[idx]:
                        moon.vel[idx] += 1
                    elif moon.pos[idx] > other_moon.pos[idx]:
                        moon.vel[idx] -= 1

        for moon in moons:
            for idx in range(3):
                moon.pos[idx] += moon.vel[idx]

        for axis in range(3):
            h = hash(tuple(m.pos[axis] for m in moons) + tuple(m.vel[axis] for m in moons))
            if h not in moon_axis_states_sets[axis]:
                moon_axis_states[axis].append(h)
                continue
            try:
                prev_state_idx = moon_axis_states[axis].index(h)
            except ValueError:
                # moon_axis_states[axis].append(h)
                continue
            if moon_axis_found[axis] < 0:
                moon_axis_found[axis] = step_idx - prev_state_idx

            # moon_axis_states[axis].add(h)

        if all(e >= 0 for e in moon_axis_found):
            print(moon_axis_found)
            system_repeats = lcm(moon_axis_found[0], lcm(moon_axis_found[1], moon_axis_found[2]))
            print(f'Moon position repeats after {system_repeats}')
            break

        if step_idx % 1000 == 0:
            print(f'Simulating step {step_idx}')
            # for moon in moons:
            #     print(str(moon))

    # for moon in moons:
    #     print(moon.format_energy())
    # total_energy = sum(moon.calc_energy() for moon in moons)
    # print(f'Total energy after {step_idx} steps: {total_energy}')


def main():
    tests = [
        # ('<x=-1, y=0, z=2>\n<x=2, y=-10, z=-7>\n<x=4, y=-8, z=8>\n<x=3, y=5, z=-1>', 17, ),
        # ('<x=-8, y=-10, z=0>\n<x=5, y=5, z=10>\n<x=2, y=-7, z=3>\n<x=9, y=-8, z=-3>', 17, ),
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
