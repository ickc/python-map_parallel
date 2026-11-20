# Changelog

## v0.3.0 (2026-11-20)

Fixes:

- An exception raised by the mapped function now always propagates. With
  `return_results=False`, it was silently discarded
  ([#2](https://github.com/ickc/python-map_parallel/issues/2)). For
  `mpi_simple`, it is now raised on every rank, where the other ranks used to
  wait for the failed one forever.
- An unknown `mode` raises `ValueError`, where it used to run serially, so that
  a typo such as `mode="multiprocesing"` went unnoticed. **This may break code
  that relied on it**; `mode="serial"` is the way to run serially.
- `starmap_parallel` on the `multiprocessing`, `multithreading` and `dask`
  backends calls `f(*args)` for each tuple of arguments, as
  `itertools.starmap` does, where tuples of unequal lengths were mixed up.
- `dask`: equal arguments are no longer taken for one call whose result is
  reused (`pure=False`), and the `LocalCluster` and `Client` are closed after
  the call, where they were left running.
- `return_results=False` returns `[]` whatever the mode or the number of
  processes; serially it returned the results.
- `mpi_simple` joins the ranks' results in one pass, where `sum(..., [])` copied
  them once per rank.

New:

- `mode="multiinterpreter"`, on `concurrent.futures.InterpreterPoolExecutor`
  (Python 3.14 on): parallel pure Python in one process.
- `chunksize`, for every backend but `mpi_simple` and `serial`: the number of
  calls sent to a worker at a time, to cut the overhead when each call is quick.
- `dask` runs on the active `distributed.Client` if there is one, so on any
  cluster it is connected to; and with `processes`, starts that many
  single-threaded workers.
- `mpi` passes `processes` to `MPIPoolExecutor` as `max_workers`, which matters
  when it spawns its workers (without `python -m mpi4py.futures`).
- `map_parallel.MODES`, the valid values of `mode`, and type hints (`py.typed`).
- Tested on Python 3.11 to 3.15 and on the free-threaded builds 3.13t to 3.15t,
  on Linux (x86-64 and ARM64), macOS (x86-64 and ARM64) and Windows (x86-64).
- The docs, at <https://ickc.github.io/python-map_parallel>, have a page on
  choosing a backend.

Packaging:

- Require Python 3.11 or later.
- The optional dependencies are extras: `map-parallel[dask]`,
  `map-parallel[mpi]`.
- Built with uv_build and released from GitHub Actions through trusted
  publishing; developed with pixi.

## v0.2.0 (2021-06-09)

- Add the `mpi_simple` mode.

## v0.1.1 (2020-11-20)

- First release on PyPI.
