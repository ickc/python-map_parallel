"""Checks of mode="mpi" and mode="mpi_simple", run under mpiexec by test_mpi.py.

    mpiexec -n 3 python tests/mpi/check.py mpi_simple
    mpiexec -n 3 python -m mpi4py.futures tests/mpi/check.py mpi

Each rank that runs this prints one line, "rank <rank>/<size>: <outcome>"; any
failure raises. ``workloads`` must be importable, e.g. through PYTHONPATH.
"""

import argparse
import sys
import time

import workloads as w
from mpi4py import MPI

from map_parallel import map_parallel, starmap_parallel


def progress(rank: int, step: str, t: float) -> None:
    """On stderr, so that a test that times out shows how far each rank got."""
    print(f"rank {rank}: {step} done in {time.perf_counter() - t:.2f} s", file=sys.stderr, flush=True)


def check_results(mode: str, rank: int) -> str:
    # rank 0 gets the results; for mpi_simple, the other ranks get []
    def expected(results):
        return results if rank == 0 else []

    for chunksize in (1, 4):
        kwargs = dict(mode=mode, chunksize=chunksize)
        t = time.perf_counter()
        assert (res := map_parallel(w.f, *w.COLUMNS, **kwargs)) == expected(w.TRUTH), res
        progress(rank, f"map_parallel, chunksize={chunksize}", t)
        assert (res := starmap_parallel(w.f, w.ARGS, **kwargs)) == expected(w.TRUTH), res
        assert (res := starmap_parallel(w.total, [(1,), (1, 2), (1, 2, 3)], **kwargs)) == expected([1, 3, 6]), res
        assert map_parallel(w.f, *w.COLUMNS, return_results=False, **kwargs) == []
        assert map_parallel(w.f, [], [], [], **kwargs) == []
        progress(rank, f"all, chunksize={chunksize}", t)
    # processes=1 is serial, on every rank
    assert map_parallel(w.f, *w.COLUMNS, mode=mode, processes=1) == w.TRUTH
    return "ok"


def check_exception(mode: str, return_results: bool) -> str:
    """Every rank raises: none waits forever for the rank that failed."""
    # with 17 calls on 3 ranks, the bad input 3 is on rank 0 only, and 12 on rank 2 only
    outcomes = []
    for bad in (3, 12):
        try:
            map_parallel(w.fail_on, range(w.N_JOBS), [bad] * w.N_JOBS, mode=mode, return_results=return_results)
        except w.Bad as e:
            outcomes.append(f"{type(e).__name__}: {e} (cause: {type(e.__cause__).__name__})")
        else:
            raise AssertionError("no exception raised")
    return "; ".join(outcomes)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["mpi", "mpi_simple"])
    parser.add_argument("--exception", action="store_true")
    parser.add_argument("--no-return-results", dest="return_results", action="store_false")
    args = parser.parse_args()

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    if args.exception:
        outcome = check_exception(args.mode, args.return_results)
    else:
        outcome = check_results(args.mode, rank)
    print(f"rank {rank}/{comm.Get_size()}: {outcome}", flush=True)


if __name__ == "__main__":
    main()
