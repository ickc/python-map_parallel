from itertools import starmap

from map_parallel import map_parallel
from map_parallel import starmap_parallel

ARGS = [
    [3, 4, 5],
    [5, 12, 13],
    [1, 2, 3]
]


def f(x, y, z):
    return x * x + y * y == z * z


def test_map_parallel():
    args = list(map(list, zip(*ARGS)))
    truth = list(map(f, *args))
    # MPI is difficult to test
    for mode in ('multiprocessing', 'multithreading'):
        for processes in (None, 1, 2):
            assert map_parallel(f, *args, mode=mode, processes=processes) == truth


def test_starmap_parallel():
    args = ARGS
    truth = list(starmap(f, args))
    # MPI is difficult to test
    for mode in ('multiprocessing', 'multithreading'):
        for processes in (None, 1, 2):
            assert starmap_parallel(f, args, mode=mode, processes=processes) == truth
