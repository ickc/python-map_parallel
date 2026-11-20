# map_parallel

[![Test](https://github.com/ickc/python-map_parallel/actions/workflows/test.yml/badge.svg)](https://github.com/ickc/python-map_parallel/actions/workflows/test.yml)
[![Documentation](https://github.com/ickc/python-map_parallel/actions/workflows/docs.yml/badge.svg)](https://ickc.github.io/python-map_parallel)
[![PyPI](https://img.shields.io/pypi/v/map-parallel.svg)](https://pypi.org/project/map-parallel)
[![Python versions](https://img.shields.io/pypi/pyversions/map-parallel.svg)](https://pypi.org/project/map-parallel)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/map_parallel.svg)](https://anaconda.org/conda-forge/map_parallel)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4641295.svg)](https://doi.org/10.5281/zenodo.4641295)
[![License](https://img.shields.io/pypi/l/map-parallel.svg)](https://github.com/ickc/python-map_parallel/blob/main/LICENSE)

A drop-in replacement of `map` and `itertools.starmap`, but in parallel, with
backends to choose from: processes, threads, subinterpreters, dask and MPI.

```python
from map_parallel import map_parallel, starmap_parallel


def f(x, y):
    return x**y


if __name__ == "__main__":
    # list(map(f, [1, 2, 3], [2, 2, 2])), on a pool of processes
    map_parallel(f, [1, 2, 3], [2, 2, 2])  # [1, 4, 9]
    # list(itertools.starmap(f, [(1, 2), (2, 2), (3, 2)])), on 4 threads
    starmap_parallel(f, [(1, 2), (2, 2), (3, 2)], mode="multithreading", processes=4)  # [1, 4, 9]
```

The same code runs on any backend: change `mode`, and nothing else.

## Installation

```sh
pip install map-parallel
# with the optional backends
pip install "map-parallel[dask]"
pip install "map-parallel[mpi]"  # needs an MPI implementation, see mpi4py's documentation
# or
conda install -c conda-forge map_parallel
```

map_parallel itself is pure Python with no dependencies, supports Python 3.11
and later, and is tested on free-threaded builds of Python (3.13t on).

## Backends

| `mode` | runs on | suits |
| --- | --- | --- |
| `multiprocessing` (default) | [`ProcessPoolExecutor`](https://docs.python.org/3/library/concurrent.futures.html#processpoolexecutor) | CPU-bound pure Python, with a GIL |
| `multithreading` | [`ThreadPoolExecutor`](https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor) | I/O-bound work; work that releases the GIL; anything, on free-threaded Python |
| `multiinterpreter` | [`InterpreterPoolExecutor`](https://docs.python.org/3/library/concurrent.futures.html#interpreterpoolexecutor), Python 3.14+ | CPU-bound pure Python, in one process |
| `dask` | [dask.distributed](https://distributed.dask.org): the active `Client`, or a `LocalCluster` | a cluster you already have |
| `mpi` | [`mpi4py.futures.MPIPoolExecutor`](https://mpi4py.readthedocs.io/en/stable/mpi4py.futures.html) | HPC, with dynamic load balancing |
| `mpi_simple` | [mpi4py](https://mpi4py.readthedocs.io), one equal block of work per rank | HPC, where `mpi` does not work |
| `serial` | `map` | debugging |

[Choosing a backend](https://ickc.github.io/python-map_parallel/backends/)
explains which to use when, and why.

Both functions take the same keyword arguments:

- `processes`: the number of workers, or `None` for the backend's default; `1`
  runs serially.
- `chunksize`: the number of calls sent to a worker at a time. Raise it when
  each call is quick, to cut the overhead per call.
- `return_results`: `False` to discard the results, e.g. when `f` writes its
  output to files.

An exception raised by `f` propagates to the caller, whatever the backend, and
whether or not the results are returned. For `mpi_simple`, it is raised on every
rank, so that no rank waits forever for the one that failed.

Except for `multithreading` and `serial`, `f`, its arguments and its results go
to other processes or interpreters, so they must be picklable: define `f` at
the top level of a module, and guard the script's entry point with
`if __name__ == "__main__":`.

The MPI modes run under `mpiexec`:

```sh
mpiexec -n 4 python -m mpi4py.futures script.py  # mode="mpi"
mpiexec -n 4 python script.py                    # mode="mpi_simple": every rank runs the script
```

## Documentation

<https://ickc.github.io/python-map_parallel>

## Citation

If map_parallel contributes to your research, please cite it through its
[Zenodo record](https://doi.org/10.5281/zenodo.4641295), whose DOI resolves to
the latest version.
