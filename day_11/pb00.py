
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


def solve(moons):
    orig_moons = copy.deepcopy(moons)
    step_idx = 0
    print(f'After {step_idx} steps:')
    for moon in moons:
        print(str(moon))

    while step_idx < 1000:
        step_idx += 1

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

        if step_idx % 10 == 0:
            print(f'After {step_idx} steps:')
            for moon in moons:
                print(str(moon))

    for moon in moons:
        print(moon.format_energy())
    total_energy = sum(moon.calc_energy() for moon in moons)
    print(f'Total energy after {step_idx} steps: {total_energy}')


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
