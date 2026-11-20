"""Functions to map in the tests.

They live in a module of their own, so that they pickle by reference into worker
processes and interpreters, and so that the MPI scripts can share them.
"""

import os
import sys
import threading
import time

N_ARGS = 3
# a not so small prime no. > 8, so that chunks and MPI blocks are uneven
N_JOBS = 17

#: one tuple of arguments per call, for starmap
ARGS = [tuple(2 * i * i + 3 * j * j + 5 * i * j for j in range(N_ARGS)) for i in range(N_JOBS)]
#: one iterable per argument, for map
COLUMNS = [list(column) for column in zip(*ARGS, strict=True)]


def f(x, y, z):
    return x * x + y * y - z * z


TRUTH = [f(*args) for args in ARGS]


def total(*xs):
    return sum(xs)


def scale(x, *, k):
    return x * k


class Bad(ValueError):
    pass


def fail_on(x, bad=3):
    if x == bad:
        raise Bad(f"bad input: {x}")
    return x


def token(_):
    """A different result on every call, even with the same argument."""
    return os.urandom(16).hex()


def sleep_then_return(x):
    """The earlier the argument, the later it finishes."""
    time.sleep(0.01 * (5 - x))
    return x


def thread_id(_):
    return threading.get_ident()


def pid(_):
    return os.getpid()


def sys_path(_):
    return list(sys.path)
