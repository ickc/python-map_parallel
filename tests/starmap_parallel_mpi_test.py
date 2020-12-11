#!/usr/bin/env python

from map_parallel import starmap_parallel

ARGS = [
    [3, 4, 5],
    [5, 12, 13],
    [1, 2, 3]
]


def f(x, y, z):
    return x * x + y * y == z * z


if __name__ == "__main__":
    args = list(map(list, zip(*ARGS)))
    truth = list(map(f, *args))
    res = starmap_parallel(f, ARGS, mode='mpi')
    assert res == truth
