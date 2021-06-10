#!/usr/bin/env python

from map_parallel import map_parallel

from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

n_args = 3
# a not so small prime no. > 8
n_jobs = 17

ARGS = [[2 * i * i + 3 * j * j + 5 * i * j for j in range(n_args)] for i in range(n_jobs)]


def f(x, y, z):
    return x * x + y * y - z * z


if __name__ == "__main__":
    args = list(map(list, zip(*ARGS)))
    truth = list(map(f, *args))
    res = map_parallel(f, *args, mode='mpi_simple', return_results=True)

    if rank == 0:
        if res != truth:
            print(res, truth)
            raise AssertionError
