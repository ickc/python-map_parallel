"""Tests of the backends in the standard library, and of what every backend shares.

The tests taking the ``mode`` fixture are backend-independent: ``test_dask.py``
runs them again on dask.
"""

import os
import subprocess
import sys
import sysconfig
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from importlib.metadata import version
from itertools import starmap
from typing import get_args

import pytest
import workloads as w

import map_parallel as package
from map_parallel import MODES, Mode, map_parallel, starmap_parallel

HAS_INTERPRETERS = sys.version_info >= (3, 14)
FREE_THREADED = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))

STDLIB_MODES = [
    "multiprocessing",
    "multithreading",
    pytest.param(
        "multiinterpreter",
        marks=pytest.mark.skipif(not HAS_INTERPRETERS, reason="InterpreterPoolExecutor is new in Python 3.14"),
    ),
    "serial",
]


@pytest.fixture(params=STDLIB_MODES)
def mode(request):
    return request.param


# backend-independent ##########################################################


@pytest.mark.parametrize("processes", [None, 1, 2])
def test_map_parallel(mode, processes):
    assert map_parallel(w.f, *w.COLUMNS, mode=mode, processes=processes) == w.TRUTH


@pytest.mark.parametrize("processes", [None, 1, 2])
def test_starmap_parallel(mode, processes):
    assert starmap_parallel(w.f, w.ARGS, mode=mode, processes=processes) == w.TRUTH


@pytest.mark.parametrize("chunksize", [1, 2, 5, 100])
def test_chunksize(mode, chunksize):
    assert map_parallel(w.f, *w.COLUMNS, mode=mode, processes=2, chunksize=chunksize) == w.TRUTH
    assert starmap_parallel(w.f, w.ARGS, mode=mode, processes=2, chunksize=chunksize) == w.TRUTH


@pytest.mark.parametrize("processes", [None, 1])
def test_no_return_results(mode, processes):
    assert map_parallel(w.f, *w.COLUMNS, mode=mode, processes=processes, return_results=False) == []
    assert starmap_parallel(w.f, w.ARGS, mode=mode, processes=processes, return_results=False) == []


@pytest.mark.parametrize("chunksize", [1, 4])
@pytest.mark.parametrize("return_results", [True, False])
@pytest.mark.parametrize("processes", [None, 1])
def test_exception_propagates(mode, processes, return_results, chunksize):
    """https://github.com/ickc/python-map_parallel/issues/2"""
    kwargs = dict(mode=mode, processes=processes, return_results=return_results, chunksize=chunksize)
    with pytest.raises(w.Bad, match="bad input: 3"):
        map_parallel(w.fail_on, range(8), **kwargs)
    with pytest.raises(w.Bad, match="bad input: 3"):
        starmap_parallel(w.fail_on, [(i,) for i in range(8)], **kwargs)


def test_empty(mode):
    assert map_parallel(w.f, [], [], [], mode=mode) == []
    assert starmap_parallel(w.f, [], mode=mode) == []


def test_shortest_iterable(mode):
    """Like map, stop at the shortest iterable."""
    assert map_parallel(w.total, [1, 2, 3], [10, 20], mode=mode) == list(map(w.total, [1, 2, 3], [10, 20])) == [11, 22]


def test_ragged_starmap(mode):
    """Each tuple of arguments is a call of its own, whatever its length."""
    args = [(1,), (1, 2), (1, 2, 3), ()]
    assert starmap_parallel(w.total, args, mode=mode) == list(starmap(w.total, args)) == [1, 3, 6, 0]


def test_iterators(mode):
    assert map_parallel(w.f, *map(iter, w.COLUMNS), mode=mode) == w.TRUTH
    assert starmap_parallel(w.f, (iter(args) for args in w.ARGS), mode=mode) == w.TRUTH


def test_order(mode):
    """Results come in the order of the arguments, not of completion."""
    assert map_parallel(w.sleep_then_return, range(5), mode=mode, processes=5) == list(range(5))


def test_impure(mode):
    """Equal arguments are separate calls: no result is reused."""
    assert len(set(map_parallel(w.token, [0] * 8, mode=mode))) == 8


def test_partial(mode):
    """Keyword arguments, through functools.partial."""
    assert map_parallel(partial(w.scale, k=3), range(4), mode=mode) == [0, 3, 6, 9]


# validation ###################################################################


@pytest.mark.parametrize("mode", ["multiprocesing", "MPI", "", None, ["serial"]])
def test_invalid_mode(mode):
    with pytest.raises(ValueError, match="mode must be one of"):
        map_parallel(w.f, *w.COLUMNS, mode=mode)
    with pytest.raises(ValueError, match="mode must be one of"):
        starmap_parallel(w.f, w.ARGS, mode=mode, processes=1)


@pytest.mark.parametrize("chunksize", [0, -1, 1.5, "1", None])
def test_invalid_chunksize(chunksize):
    with pytest.raises(ValueError, match="chunksize must be a positive integer"):
        map_parallel(w.f, *w.COLUMNS, mode="serial", chunksize=chunksize)


def test_modes():
    assert MODES == get_args(Mode) == tuple(package._BACKENDS)


def test_public_api():
    assert package.__version__ == version("map-parallel")
    assert all(hasattr(package, name) for name in package.__all__)


# backend-specific #############################################################


@pytest.mark.parametrize("mode", ["multiprocessing", "multithreading", "multiinterpreter", "serial"])
def test_one_process_is_serial(mode):
    """processes=1 runs in the calling thread, whatever the mode."""
    assert map_parallel(w.thread_id, range(4), mode=mode, processes=1) == [threading.get_ident()] * 4


def test_multithreading_threads():
    ids = map_parallel(w.thread_id, range(8), mode="multithreading", processes=2)
    assert threading.get_ident() not in ids
    assert 1 <= len(set(ids)) <= 2


def test_multiprocessing_processes():
    pids = map_parallel(w.pid, range(8), mode="multiprocessing", processes=2)
    assert os.getpid() not in pids
    assert 1 <= len(set(pids)) <= 2


def test_multiprocessing_unpicklable():
    """A function that does not pickle raises, instead of hanging."""
    with pytest.raises(Exception, match="lambda"):
        map_parallel(lambda x: x, range(4), mode="multiprocessing", processes=2)


@pytest.mark.skipif(not HAS_INTERPRETERS, reason="InterpreterPoolExecutor is new in Python 3.14")
def test_multiinterpreter_sys_path():
    """Workers see sys.path as changed at run time, e.g. by pytest, so that workloads imports in them."""
    (path,) = map_parallel(w.sys_path, [0], mode="multiinterpreter", processes=2)
    assert path == sys.path


@pytest.mark.skipif(HAS_INTERPRETERS, reason="InterpreterPoolExecutor is new in Python 3.14")
def test_multiinterpreter_unavailable():
    with pytest.raises(ImportError, match="new in Python 3.14"):
        map_parallel(w.f, *w.COLUMNS, mode="multiinterpreter")


def test_multithreading_concurrent_callers():
    """map_parallel is thread-safe: call it from several threads at once (on a free-threaded build, truly at once)."""
    with ThreadPoolExecutor(8) as executor:
        futures = [
            executor.submit(map_parallel, w.f, *w.COLUMNS, mode="multithreading", processes=4, chunksize=chunksize)
            for chunksize in [1, 2, 3, 4] * 4
        ]
        assert all(future.result() == w.TRUTH for future in futures)


@pytest.mark.skipif(not FREE_THREADED, reason="needs a free-threaded build")
def test_free_threaded_gil_stays_disabled():
    """Importing map_parallel does not re-enable the GIL."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("COVERAGE")}
    out = subprocess.run(
        [sys.executable, "-c", "import sys, map_parallel; print(sys._is_gil_enabled())"],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    )
    assert out.stdout.strip() == "False"


# how mpi_simple sends an exception to the other ranks #########################
# (pure functions: tested here, without MPI)


class Unpicklable(Exception):
    def __init__(self):
        super().__init__("unpicklable")
        self.attribute = lambda: None


@pytest.mark.parametrize(
    "exc, type_, message",
    [
        (w.Bad("bad input: 3"), w.Bad, "bad input: 3"),
        (Unpicklable(), RuntimeError, "Unpicklable('unpicklable')"),
    ],
)
def test_exception_payload(exc, type_, message):
    try:
        raise exc
    except Exception as e:
        payload = package._exception_payload(e)
    remote = package._exception_from_payload(2, payload)
    assert type(remote) is type_
    assert message in str(remote)
    assert type(remote.__cause__).__name__ == "_RemoteTraceback"
    assert "raised on MPI rank 2" in str(remote.__cause__)
    assert f"{type(exc).__name__}" in str(remote.__cause__)


def test_exception_payload_does_not_unpickle():
    """Whether an exception unpickles depends on more than its class: importing
    distributed, for one, installs tblib's pickling of exceptions, which does
    not call __init__. So the payload is made by hand, of a class that is
    nowhere to be found."""
    payload = ("Traceback: ...", b"cno_such_module\nNoSuchError\n.")
    remote = package._exception_from_payload(2, payload)
    assert type(remote) is RuntimeError
    assert "does not unpickle was raised on MPI rank 2" in str(remote)
    assert "Traceback: ..." in str(remote.__cause__)
