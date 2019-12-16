# cython: language_level=3


import itertools

# from more_itertools import take

# @functools.lru_cache
cpdef pattern(int position, int of_length):
    cdef:
        int e, i
        list base_pattern, resulting_pattern = []
        int first_value
    base_pattern = [0, 1, 0, -1, ]
    assert position > 0
    repeat_pattern = []
    for e in base_pattern:
        repeat_pattern.extend([e] * position)
    first_value = repeat_pattern[0]
    del repeat_pattern[0]
    repeat_pattern.append(first_value)

    for i, e in zip(range(of_length), itertools.cycle(repeat_pattern)):
        resulting_pattern.append(e)
    # for i in range(of_length)
    return resulting_pattern


cpdef apply_pattern(list elements, long application, list patterns):
    cdef:
        list new_elements
        long i, p
        long long s
    new_elements = []
    for i in range(len(elements)):
        s = 0
        # for e, p in zip(elements, pattern(i + 1)):
        for e, p in zip(elements, patterns[i]):
            # print(f"For elem idx {i}: {e} * {p}")
            # s += e * p
            if p == 0:
                continue
            elif p == -1:
                s -= e
            elif p == 1:
                s += e

        # print(f"For elem idx sum is {s}")
        new_elements.append(abs(s) % 10)
    return new_elements




cpdef solve(list elements, long nb_iterations, long nb_repetitions):
    cdef:
        list PATTERNS, first_seven, secret_message, new_elements, initial_elements
        long i = 0, message_offset
        str secret_message_str

    initial_elements = list(elements)

    first_seven = initial_elements[:7]
    message_offset = int(''.join(map(str, first_seven)))
    print(f"Message offset {message_offset}  len(elements) * 10000 == {len(elements) * 10000}")

    if nb_repetitions > 1:
        elements = elements * nb_repetitions

    # PATTERNS = {i: more_itertools.take(len(elements), pattern(i)) for i in range(1, len(elements))}
    # PATTERNS = [take(len(elements), pattern(i)) for i in range(1, len(elements) + 1)]
    PATTERNS = [pattern(i, len(elements)) for i in range(1, len(elements) + 1)]

    for i in range(1, nb_iterations + 1):
        new_elements = apply_pattern(elements, i, PATTERNS)
        # print(f"{''.join(map(str, elements))} becomes {''.join(map(str, new_elements))}")
        elements = new_elements
        # if i % 10 == 0:
        #     print(f'Iteration {i}')

    print(f"Message offset {message_offset}")

    secret_message = elements[message_offset: message_offset + 8]
    secret_message_str = ''.join(map(str, secret_message))
    print(f'Hidden value: {secret_message_str}')

    return secret_message_str


cpdef apply_pattern_pt2(list elements, long application):
    cdef:
        list new_elements
        long i, p
        long long s
    new_elements = [elements[-1]]
    for e in elements[-2::-1]:
        new_elements.append(new_elements[-1] + e)
    new_elements = [abs(e) % 10 for e in reversed(new_elements)]
    return new_elements


cpdef solve_pt2(list elements, long nb_iterations, long nb_repetitions):
    cdef:
        list PATTERNS, first_seven, secret_message, new_elements, initial_elements
        long i = 0, message_offset
        str secret_message_str

    initial_elements = list(elements)

    first_seven = initial_elements[:7]
    message_offset = long(''.join(map(str, first_seven)))
    print(f"Message offset {message_offset}  len(elements) * nb_repetitions == {len(elements) * nb_repetitions}   {len(elements) * nb_repetitions // 2}")
    # print(f"Long pattern: {pattern(len(elements) * 50 + 1, len(elements) * 100)}")  # Aaaaaa

    if nb_repetitions > 1:
        elements = elements * nb_repetitions

    # assert message_offset > len(elements) * nb_repetitions // 2
    elements = elements[message_offset:]
    print(f"len(elements) == {len(elements)}")

    for i in range(1, nb_iterations + 1):
        new_elements = apply_pattern_pt2(elements, i)
        # print(f"{''.join(map(str, elements))} becomes {''.join(map(str, new_elements))}")
        elements = new_elements
        # if i % 10 == 0:
        #     print(f'Iteration {i}')

    message_offset = 0
    secret_message = elements[message_offset: message_offset + 8]
    secret_message_str = ''.join(map(str, secret_message))
    print(f'Hidden value: {secret_message_str}')

    return secret_message_str
