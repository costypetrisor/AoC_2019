
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


def read(filepath):
    asteroids = []
    if os.path.isfile(filepath):
        with open(filepath) as f:
            content = f.read()
    else:
        content = filepath
    galaxy_map = [list(l.strip()) for l in content.splitlines()]
    for row_idx, line in enumerate(galaxy_map):
        for col_idx, elem in enumerate(line):
            if elem != '.':
                asteroids.append((row_idx, col_idx))

    return (galaxy_map, asteroids, )


def is_collinear(A, B, C):
    # A = (A[0] + 0.5, A[1] + 0.5)
    # B = (B[0] + 0.5, B[1] + 0.5)
    # C = (C[0] + 0.5, C[1] + 0.5)
    # term = float(A[0]) * (B[1] - C[1])
    # term += float(B[0]) * (C[1] - A[1])
    # term += float(C[0]) * (A[1] - B[1])
    term = float(A[0]) * (B[1] - C[1])
    term += float(B[0]) * (C[1] - A[1])
    term += float(C[0]) * (A[1] - B[1])
    # print(f'is_collinear {A}  {B}  {C}  {term}')
    return math.fabs(term) < 0.5


def sq_distance(A, B):
    return (A[0] - B[0]) * (A[0] - B[0]) + (A[1] - B[1]) * (A[1] - B[1])

def distance(A, B):
    return math.sqrt((A[0] - B[0]) * (A[0] - B[0]) + (A[1] - B[1]) * (A[1] - B[1]))


def solve(galaxy_map, asteroids, best_asteroid):
    # best_asteroid, best_asteroid_count = None, 0
    best_asteroid, best_asteroid_count = best_asteroid
    best_asteroid = (best_asteroid[1], best_asteroid[0], )

    original_asteroids = copy.deepcopy(asteroids)

    print(f'Number of asteroids: {len(asteroids)}')

    def build_distances_map(asteroids):
        distances = {}
        for A, B in itertools.combinations(asteroids, 2):
            dist = sq_distance(A, B)
            # dist = distance(A, B)
            distances[(A, B)] = dist
            distances[(B, A)] = dist
        return distances

    distances = build_distances_map(asteroids)

    def build_collinearity_map(asteroids):
        collinearity_map = {}
        # collinearity_map_with_others = collections.defaultdict(list)
        for A, B, C in itertools.combinations(asteroids, 3):
            collinear = is_collinear(A, B, C)
            if collinear:
                collinearity_map[tuple(sorted((A, B, C)))] = collinear
                # collinearity_map_with_others[A].append((B, C))
                # collinearity_map_with_others[B].append((A, C))
                # collinearity_map_with_others[C].append((A, B))
        return collinearity_map

    collinearity_map = build_collinearity_map(asteroids)

    # pprint(distances)
    # pprint(collinearity_map)
    # pprint(collinearity_map_with_others)

    who_can_see = collections.defaultdict(list)

    def find_visible_asteroids(from_asteroid, asteroids, distances, collinearity_map):
        A = from_asteroid
        who_can_he_see = []
        count = 0

        for B in asteroids:
            if A == B: continue

            visibile = True

            for C in asteroids:
                if C == A or C == B: continue

                collinear = collinearity_map.get(tuple(sorted((A, B, C))))
                if collinear:
                    if distances[(A, B)] > distances[(A, C)] and not (distances[(A, C)] + distances[(C, B)] - 0.5) > distances[(A, B)] :
                        visibile = False
                        break

            if visibile:
                count += 1
                who_can_he_see.append(B)
        return count, who_can_he_see

    destroyed_count = 0

    while destroyed_count < 200 and len(asteroids) > 1:
        point_above = (best_asteroid[0], best_asteroid[1] - 1)

        _, visible_asteroids = find_visible_asteroids(best_asteroid, asteroids, distances, collinearity_map)
        if not visible_asteroids:
            print('no more visible asteroids')
            break

        visible_asteroids_offsets = [
            (idx, (a[0] - best_asteroid[0], a[1] - best_asteroid[1]))
            for idx, a in enumerate(visible_asteroids)]
        visible_asteroids_offsets = [
            (idx, a, math.atan2(-(a[1] + 0.001), a[0])) for idx, a in visible_asteroids_offsets]

        visible_asteroids_offsets = sorted(visible_asteroids_offsets, key=lambda x: x[2])
        # print(visible_asteroids_offsets)
        visible_asteroids = [visible_asteroids[e[0]] for e in visible_asteroids_offsets]
        print(f'Destroying {len(visible_asteroids)} asteroids: {visible_asteroids}')

        for asteroid in visible_asteroids:
            destroyed_count += 1
            if destroyed_count == 200:
                print(f'Destroyed 200th astroid {asteroid} {asteroid[1]},{asteroid[0]}  {asteroid[1] * 100 + asteroid[0]}')
                continue

            for collinearity in list(collinearity_map.keys()):
                A, B, C = collinearity
                if A == asteroid or B == asteroid or C == asteroid:
                    del collinearity_map[collinearity]
            asteroids.remove(asteroid)


    # best_asteroid, best_asteroid_count = None, 0
    # for A in asteroids:
    #     count, who_can_he_see = find_visible_asteroids(A, asteroids, distances, collinearity_map)
    #     who_can_see[A] = who_can_he_see
    #     print(f'Asteroid {A}  can see {count}  {who_can_see[A]}')
    #     # count_map[A[0]][A[1]] = str(count)
    #     if count > best_asteroid_count:
    #         best_asteroid = A
    #         best_asteroid_count = count



    return (best_asteroid[1], best_asteroid[0]), best_asteroid_count


def main():
    tests = [
        # ('pb00_input00.txt', ((3, 4), 8), ),
        # ('pb00_input01.txt', ((0, 0), 7), ),
        # ('pb00_input02.txt', ((5, 8), 33), ),
        # ('pb00_input03.txt', ((1, 2), 35), ),
        # ('pb00_input04.txt', ((6, 3), 41), ),
        # ('pb00_input05.txt', ((11, 13), 210), ),
        # ('pb01_input00.txt', ((8, 3), 30), ),
        ('pb00_input06.txt', ((30, 34), 344), ),
    ]
    for test, expected in tests:
        _input = read(test)
        res = solve(*_input, expected)
        print(test, expected, res)

    # test = 'pb00_input01.txt'
    # _input = read(test)
    # result = solve(*_input)
    # print(result)


__name__ == '__main__' and main()
