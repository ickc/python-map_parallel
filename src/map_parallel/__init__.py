"""A drop-in replacement of :func:`map` and :func:`itertools.starmap`, but in parallel with different backends.

>>> from map_parallel import map_parallel, starmap_parallel
>>> map_parallel(pow, [1, 2, 3], [2, 2, 2], mode="multithreading")
[1, 4, 9]
>>> starmap_parallel(pow, [(1, 2), (2, 2), (3, 2)], mode="multiprocessing", processes=2)
[1, 4, 9]

Exceptions raised by the mapped function propagate to the caller, whether the
results are returned or not:

>>> map_parallel(int, ["1", "x"], mode="multithreading", return_results=False)
Traceback (most recent call last):
    ...
ValueError: invalid literal for int() with base 10: 'x'
"""

from __future__ import annotations

import sys
from collections import deque
from collections.abc import Callable, Iterable, Iterator
from functools import partial
from importlib.metadata import version
from itertools import chain, islice, starmap
from typing import Any, Literal, TypeVar

__version__ = version("map-parallel")

__all__ = [
    "MODES",
    "Mode",
    "map_parallel",
    "starmap_parallel",
]

T = TypeVar("T")

Mode = Literal[
    "multiprocessing",
    "multithreading",
    "multiinterpreter",
    "dask",
    "mpi",
    "mpi_simple",
    "serial",
]

# helpers ######################################################################


def _starmap_chunk(f: Callable[..., T], chunk: Iterable[tuple[Any, ...]]) -> list[T]:
    """Apply ``f`` to each tuple of arguments in a chunk, in the worker.

    Module-level, so that it pickles by reference.
    """
    return list(starmap(f, chunk))


def _batched(iterable: Iterable[T], n: int) -> Iterator[tuple[T, ...]]:
    """:func:`itertools.batched`, which is new in Python 3.12."""
    iterator = iter(iterable)
    while batch := tuple(islice(iterator, n)):
        yield batch


def _collect(results: Iterable[T], return_results: bool) -> list[T]:
    """Exhaust ``results``, so that an exception raised by any task propagates.

    An executor raises the exception of a task only when its result is
    retrieved, so the results are iterated even when they are not kept
    (https://github.com/ickc/python-map_parallel/issues/2).
    """
    if return_results:
        return list(results)
    deque(results, maxlen=0)
    return []


def _set_sys_path(path: tuple[str, ...]) -> None:
    """Initialize a worker interpreter with the main interpreter's ``sys.path``.

    A new interpreter computes ``sys.path`` afresh, missing changes made at run
    time (by pytest, or a script's own directory), so functions defined in such
    modules would not unpickle in the workers.
    """
    sys.path[:] = path


# backends #####################################################################
# Each backend computes ``f(*args)`` for each ``args`` in ``iterable``, in order.


def _starmap_serial(
    f: Callable[..., T],
    iterable: Iterable[tuple[Any, ...]],
    *,
    processes: int | None = None,
    return_results: bool = True,
    chunksize: int = 1,
) -> list[T]:
    return _collect(starmap(f, iterable), return_results)


def _starmap_executor(
    executor: Any,
    f: Callable[..., T],
    iterable: Iterable[tuple[Any, ...]],
    *,
    return_results: bool,
    chunksize: int,
) -> list[T]:
    """Run on a :class:`concurrent.futures.Executor`, ``chunksize`` tasks per submission.

    On an exception, the result iterator of ``Executor.map`` cancels the tasks
    not yet started, and leaving the ``with`` block waits for those running.
    """
    with executor:
        chunks = executor.map(partial(_starmap_chunk, f), _batched(iterable, chunksize))
        return _collect(chain.from_iterable(chunks), return_results)


def _starmap_multiprocessing(
    f: Callable[..., T],
    iterable: Iterable[tuple[Any, ...]],
    *,
    processes: int | None = None,
    return_results: bool = True,
    chunksize: int = 1,
) -> list[T]:
    from concurrent.futures import ProcessPoolExecutor

    return _starmap_executor(
        ProcessPoolExecutor(max_workers=processes),
        f,
        iterable,
        return_results=return_results,
        chunksize=chunksize,
    )


def _starmap_multithreading(
    f: Callable[..., T],
    iterable: Iterable[tuple[Any, ...]],
    *,
    processes: int | None = None,
    return_results: bool = True,
    chunksize: int = 1,
) -> list[T]:
    from concurrent.futures import ThreadPoolExecutor

    return _starmap_executor(
        ThreadPoolExecutor(max_workers=processes),
        f,
        iterable,
        return_results=return_results,
        chunksize=chunksize,
    )


def _starmap_multiinterpreter(
    f: Callable[..., T],
    iterable: Iterable[tuple[Any, ...]],
    *,
    processes: int | None = None,
    return_results: bool = True,
    chunksize: int = 1,
) -> list[T]:
    try:
        from concurrent.futures import InterpreterPoolExecutor
    except ImportError:
        raise ImportError(
            "mode='multiinterpreter' needs concurrent.futures.InterpreterPoolExecutor, new in Python 3.14; "
            f"this is Python {sys.version_info.major}.{sys.version_info.minor}."
        ) from None

    return _starmap_executor(
        InterpreterPoolExecutor(
            max_workers=processes,
            initializer=_set_sys_path,
            initargs=(tuple(sys.path),),
        ),
        f,
        iterable,
        return_results=return_results,
        chunksize=chunksize,
    )


def _starmap_dask_client(
    client: Any,
    f: Callable[..., T],
    iterable: Iterable[tuple[Any, ...]],
    *,
    return_results: bool,
    chunksize: int,
) -> list[T]:
    from dask.utils import funcname
    from distributed import wait

    futures = client.map(
        partial(_starmap_chunk, f),
        list(_batched(iterable, chunksize)),
        # f may be impure, so that equal arguments must not share one result
        pure=False,
        key=funcname(f),
    )
    try:
        if return_results:
            return [result for chunk in client.gather(futures) for result in chunk]
        wait(futures)
        for future in futures:
            if future.status == "error":
                future.result()
        return []
    except BaseException:
        client.cancel(futures)
        raise


def _starmap_dask(
    f: Callable[..., T],
    iterable: Iterable[tuple[Any, ...]],
    *,
    processes: int | None = None,
    return_results: bool = True,
    chunksize: int = 1,
) -> list[T]:
    from distributed import Client, LocalCluster, default_client

    kwargs = {"return_results": return_results, "chunksize": chunksize}
    try:
        client = default_client()
    except ValueError:
        pass
    else:
        return _starmap_dask_client(client, f, iterable, **kwargs)
    cluster_kwargs: dict[str, Any] = {"dashboard_address": None}
    if processes is not None:
        cluster_kwargs.update(n_workers=processes, threads_per_worker=1)
    with LocalCluster(**cluster_kwargs) as cluster, Client(cluster) as client:
        return _starmap_dask_client(client, f, iterable, **kwargs)


def _starmap_mpi(
    f: Callable[..., T],
    iterable: Iterable[tuple[Any, ...]],
    *,
    processes: int | None = None,
    return_results: bool = True,
    chunksize: int = 1,
) -> list[T]:
    from mpi4py.futures import MPIPoolExecutor

    with MPIPoolExecutor(max_workers=processes) as executor:
        return _collect(executor.starmap(f, iterable, chunksize=chunksize), return_results)


class _RemoteTraceback(Exception):
    """The formatted traceback of an exception raised on another MPI rank."""

    def __init__(self, tb: str) -> None:
        self.tb = tb

    def __str__(self) -> str:
        return self.tb


def _exception_payload(exc: BaseException) -> tuple[str, bytes]:
    """The traceback of ``exc`` as text, and ``exc`` pickled (or, if it does not pickle, its repr)."""
    import pickle
    from traceback import format_exception

    tb = "".join(format_exception(exc))
    try:
        pickled = pickle.dumps(exc)
    except Exception:
        pickled = pickle.dumps(RuntimeError(repr(exc)))
    return tb, pickled


def _exception_from_payload(rank: int, payload: tuple[str, bytes]) -> BaseException:
    import pickle

    tb, pickled = payload
    try:
        exc = pickle.loads(pickled)
    except Exception:
        exc = RuntimeError(f"an exception that does not unpickle was raised on MPI rank {rank}")
    exc.__cause__ = _RemoteTraceback(f'\n"""\nraised on MPI rank {rank}:\n{tb}"""')
    return exc


def _starmap_mpi_simple(
    f: Callable[..., T],
    iterable: Iterable[tuple[Any, ...]],
    *,
    processes: int | None = None,
    return_results: bool = True,
    chunksize: int = 1,
) -> list[T]:
    """Split the arguments into one contiguous block per rank of ``MPI.COMM_WORLD``.

    Every rank must call it, with the same arguments. If ``f`` raises on any
    rank, it raises on every rank: on the ranks where ``f`` raised, the
    exception itself, and on the others the first rank's exception, with that
    rank's traceback as its cause, as :mod:`concurrent.futures` does. Otherwise
    the ranks that succeeded would wait forever for the ones that failed.
    """
    from mpi4py import MPI

    comm = MPI.COMM_WORLD
    size = comm.Get_size()
    rank = comm.Get_rank()

    args = list(iterable)
    n = len(args)
    local_args = args[(rank * n) // size : ((rank + 1) * n) // size]
    del args

    error: Exception | None = None
    local_results: list[T] = []
    try:
        local_results = list(starmap(f, local_args))
    except Exception as e:
        error = e

    # collective: every rank learns whether any rank failed
    payloads = comm.allgather(None if error is None else _exception_payload(error))
    if error is not None:
        raise error
    for other_rank, payload in enumerate(payloads):
        if payload is not None:
            raise _exception_from_payload(other_rank, payload)

    if return_results:
        gathered = comm.gather(local_results, root=0)
        if rank == 0:
            return [result for block in gathered for result in block]
    return []


_BACKENDS: dict[str, Callable[..., list[Any]]] = {
    "multiprocessing": _starmap_multiprocessing,
    "multithreading": _starmap_multithreading,
    "multiinterpreter": _starmap_multiinterpreter,
    "dask": _starmap_dask,
    "mpi": _starmap_mpi,
    "mpi_simple": _starmap_mpi_simple,
    "serial": _starmap_serial,
}

MODES: tuple[str, ...] = tuple(_BACKENDS)
"""The valid values of ``mode``."""


def _validate(mode: str, chunksize: int) -> Callable[..., list[Any]]:
    try:
        backend = _BACKENDS[mode]
    except (KeyError, TypeError):
        raise ValueError(f"mode must be one of {', '.join(map(repr, MODES))}; got {mode!r}.") from None
    if not isinstance(chunksize, int) or chunksize < 1:
        raise ValueError(f"chunksize must be a positive integer; got {chunksize!r}.")
    return backend


# public API ###################################################################


def map_parallel(
    f: Callable[..., T],
    *args: Iterable[Any],
    processes: int | None = None,
    mode: Mode = "multiprocessing",
    return_results: bool = True,
    chunksize: int = 1,
) -> list[T]:
    """Equivalent to ``list(map(f, *args))``, but in parallel.

    :param f: the function to apply. Except for ``multithreading`` and
        ``serial``, it, its arguments and its results are sent to other
        processes or interpreters, so they must be picklable. For
        ``multiprocessing`` and the MPI modes, ``f`` pickles by reference, so
        it must be defined at the top level of a module: not a lambda nor a
        closure. ``dask`` (through cloudpickle) and ``multiinterpreter`` also
        take a lambda.
    :param args: iterables of the arguments of ``f``, as in :func:`map`. They
        are consumed in full before any result is returned.
    :param processes: the number of workers; ``None`` for the backend's
        default. If ``processes <= 1``, run serially (in every MPI rank, for
        ``mpi_simple``). For ``mpi``, the number of MPI processes is set by
        ``mpiexec`` if the script is run with ``python -m mpi4py.futures``,
        else it is the number of processes to spawn. For ``mpi_simple``, it is
        the number of MPI processes, set by ``mpiexec`` only.
    :param mode: the backend to run on:

        - ``multiprocessing``: :class:`concurrent.futures.ProcessPoolExecutor`,
          for CPU-bound work in pure Python on a build with a GIL.
        - ``multithreading``: :class:`concurrent.futures.ThreadPoolExecutor`,
          for I/O-bound work, work that releases the GIL (much of NumPy), or
          any work on a free-threaded build of Python.
        - ``multiinterpreter``: :class:`concurrent.futures.InterpreterPoolExecutor`,
          Python 3.14 or later: one interpreter per worker, each with its own
          GIL, in one process.
        - ``dask``: dask.distributed. Runs on the active
          :class:`distributed.Client` if there is one (``processes`` is then
          ignored), else on a :class:`distributed.LocalCluster` of
          ``processes`` single-threaded workers, closed afterwards.
        - ``mpi``: :class:`mpi4py.futures.MPIPoolExecutor`. May not work,
          depending on your MPI implementation; run with
          ``mpiexec -n N python -m mpi4py.futures script.py``.
        - ``mpi_simple``: :mod:`mpi4py`, splitting the work into equal
          contiguous blocks, one per MPI rank. Every rank must call it with the
          same arguments; run with ``mpiexec -n N python script.py``.
        - ``serial``: :func:`map`.
    :param return_results: if ``False``, return ``[]`` instead of the results,
        which are then not sent back (for ``mpi_simple``, not gathered to rank
        0). Exceptions raised by ``f`` still propagate.
    :param chunksize: the number of calls of ``f`` sent to a worker at a time.
        Larger chunks cost less overhead when ``f`` is quick; smaller ones
        balance the load better when its duration varies. Ignored by
        ``mpi_simple`` and ``serial``.
    :return: the results, in order. For ``mpi_simple``, on rank 0 only; the
        other ranks get ``[]``.
    :raises ValueError: if ``mode`` or ``chunksize`` is invalid.
    :raises ImportError: if the backend of ``mode`` is not available: dask or
        mpi4py is not installed, or ``multiinterpreter`` on Python < 3.14.

    Any exception that ``f`` raises is re-raised, with the remote traceback as
    its cause where the backend provides it.
    """
    backend = _validate(mode, chunksize)
    if processes is not None and processes <= 1:
        return _collect(map(f, *args), return_results)
    # like map, stop at the shortest iterable
    iterable = zip(*args, strict=False)
    return backend(f, iterable, processes=processes, return_results=return_results, chunksize=chunksize)


def starmap_parallel(
    f: Callable[..., T],
    args: Iterable[Iterable[Any]],
    processes: int | None = None,
    mode: Mode = "multiprocessing",
    return_results: bool = True,
    chunksize: int = 1,
) -> list[T]:
    """Equivalent to ``list(itertools.starmap(f, args))``, but in parallel.

    :param args: an iterable of iterables, each the arguments of one call of
        ``f``.

    See :func:`map_parallel` for the other parameters.
    """
    backend = _validate(mode, chunksize)
    if processes is not None and processes <= 1:
        return _collect(starmap(f, args), return_results)
    return backend(f, map(tuple, args), processes=processes, return_results=return_results, chunksize=chunksize)
