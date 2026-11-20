# Choosing a backend

`map_parallel` runs the same map on any backend, so trying another is a change
of `mode`. Which is fastest depends on what `f` spends its time on, and on
what crosses between the workers and the caller.

## What `f` spends its time on

**CPU-bound pure Python.** With a GIL, only one thread runs Python bytecode at a
time, so `multithreading` is no faster than `serial`. `multiprocessing` and
`multiinterpreter` give each worker a GIL of its own. On a free-threaded build
(3.14t on), there is no GIL, and `multithreading` scales too, without starting
processes or interpreters.

**I/O-bound** (waiting on files, the network, subprocesses). Every backend
overlaps the waiting; `multithreading` costs the least. For code written with
`async`/`await`, `asyncio.gather` is the native way, and not a job for
`map_parallel`.

**Work that releases the GIL**: most of NumPy, SciPy, compression, hashing, and
many C extensions. `multithreading`, which shares memory and copies nothing.
How far it scales, though, depends on more than the GIL: work bound by memory
bandwidth (sorting or copying arrays larger than the caches) stops scaling once
the cores together saturate the memory bus, whatever the backend.

## What crosses between the workers and the caller

Except for `multithreading` and `serial`, every argument and every result is
pickled, sent, and unpickled. For `multiprocessing` they go through a pipe, one
at a time through the caller. If `f` takes or returns large objects, such as
arrays of hundreds of megabytes, the transfer can cost more than `f` itself, and
the pool can be slower than `serial`. Then:

- send something small, from which the worker can make the large object itself:
  a path, a seed, an index into a file;
- return something small, or write the output to a file in the worker and pass
  `return_results=False`;
- or, if `f` releases the GIL, use `multithreading`, which copies nothing.

On Linux before Python 3.14, `multiprocessing` starts the workers by `fork`,
and a worker inherits the caller's memory as it was when the pool started. That shares
only what the worker inherits, not what it is sent: the arguments are pickled
whatever the start method.

## Chunks

Each call has a fixed overhead: a future, a lock, and for the backends other
than `multithreading`, pickling. When `f` is quick, the overhead dominates;
`chunksize` sends that many calls to a worker at once. A larger `chunksize`
divides the overhead, at the cost of balancing the load less well when the
duration of `f` varies.

## Measured

`tools/benchmark.py` on a Ryzen 9 9950X (16 cores, 32 threads), Python 3.15.2,
wall time:

- `cpu ×8`: 8 calls of CPU-bound pure Python, ~0.27 s each, on 8 workers;
- `io ×8`: 8 calls that each sleep 0.25 s, on 8 workers;
- `overhead`: 100,000 calls that do nearly nothing, on 4 workers, at
  `chunksize` 1 and 100.

With the GIL:

| `mode` | cpu ×8 | io ×8 | overhead, chunksize 1 | chunksize 100 |
| --- | --: | --: | --: | --: |
| `serial` | 2.13 s | 2.00 s | 0.00 s | 0.00 s |
| `multiprocessing` | 0.32 s | 0.26 s | 2.72 s | 0.04 s |
| `multithreading` | 2.14 s | 0.25 s | 0.55 s | 0.02 s |
| `multiinterpreter` | 0.33 s | 0.29 s | 2.09 s | 0.08 s |

Free-threaded:

| `mode` | cpu ×8 | io ×8 | overhead, chunksize 1 | chunksize 100 |
| --- | --: | --: | --: | --: |
| `serial` | 2.20 s | 2.00 s | 0.00 s | 0.00 s |
| `multiprocessing` | 0.34 s | 0.26 s | 1.67 s | 0.05 s |
| `multithreading` | 0.31 s | 0.25 s | 0.38 s | 0.01 s |
| `multiinterpreter` | 0.52 s | 0.52 s | 1.16 s | 0.15 s |

- With the GIL, CPU-bound work in threads takes as long as `serial`; without
  it, threads do as well as processes.
- Every backend overlaps waiting.
- One call at a time, the overhead of a process or an interpreter is some
  20–30 µs a call, four to five times a thread's; in chunks of 100, it is
  nearly gone. The
  cost of starting the workers is in every number here, and is the most of
  what `multiinterpreter` takes beyond the others: interpreters start more
  slowly on the free-threaded build.

## Beyond one machine

`dask` runs on the active `distributed.Client`, if there is one, so the same
call runs on whatever cluster the client is connected to: SLURM or PBS through
dask-jobqueue, Kubernetes, and so on. Without one, it starts a
`distributed.LocalCluster` of `processes` workers, which is useful mostly for
trying the code out before a real cluster.

`mpi` and `mpi_simple` run under `mpiexec`, across the nodes of an HPC job.
`mpi` hands out calls dynamically to workers as they become free, and suits
calls whose duration varies; `mpi_simple` splits the calls into one contiguous
block per rank up front, with no scheduler, and works with any MPI
implementation, including those that `mpi4py.futures` does not.

## Gotchas

- **Picklability.** `f` must be importable by name in the workers: defined at
  the top level of a module, not a lambda, a closure, or a method of a local
  class. `functools.partial` of such a function works, which is how to pass
  keyword arguments. `multithreading` and `serial` have no such limit.
  `dask` pickles with cloudpickle, and `multiinterpreter` can share functions
  that use no closure, so both accept lambdas too.
- **`if __name__ == "__main__":`.** Where workers start by `spawn` (macOS,
  Windows) or `forkserver` (Linux from Python 3.14), each one imports the main
  module afresh, which then must not start the map again at import.
- **Oversubscription.** `processes=None` is each backend's default: one
  worker per core for `multiprocessing`, but `min(32, cores + 4)` for
  `multithreading` and `multiinterpreter`, since I/O-bound work wants more
  threads than cores; for CPU-bound work in interpreters, pass `processes`. If `f` is itself multi-threaded, as NumPy's
  linear algebra is, many workers times many threads each oversubscribe the
  cores; limit one or the other, e.g. with `OMP_NUM_THREADS=1`.
