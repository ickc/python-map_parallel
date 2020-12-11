from itertools import product

from pytest import mark

from map_parallel import map_parallel
from map_parallel import starmap_parallel

ARGS = [
    [3, 4, 5],
    [5, 12, 13],
    [1, 2, 3]
]
args = list(map(list, zip(*ARGS)))

# MPI is tested separately
cases = list(product(('multiprocessing', 'multithreading', 'dask', 'serial'), (None, 1, 2)))


def f(x, y, z):
    return x * x + y * y == z * z


truth = list(map(f, *args))


@mark.parametrize(
    'mode, processes',
    cases,
)
def test_map_parallel(mode, processes):
    assert map_parallel(f, *args, mode=mode, processes=processes) == truth


@mark.parametrize(
    'mode, processes',
    cases,
)
def test_starmap_parallel(mode, processes):
    assert starmap_parallel(f, ARGS, mode=mode, processes=processes) == truth
