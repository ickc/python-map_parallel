# Contributing

Contributions are welcome. Please report bugs and request features at
<https://github.com/ickc/python-map_parallel/issues>.

## Development

Development environments are managed by [pixi](https://pixi.sh), which also
provides dask, mpi4py and an MPI implementation (MPICH; MS-MPI on Windows) from
conda-forge:

```sh
pixi run test                     # run the tests, with the latest Python
pixi run coverage                 # and report coverage
pixi run -e test-py311 test       # with a specific Python version, 3.11 to 3.15
pixi run -e test-py314t test      # on a free-threaded build: 3.13t to 3.15t
pixi run format                   # format and fix with ruff
pixi run lint                     # check with ruff
pixi run -e docs docs             # build the docs to dist/docs
pixi run -e build build           # build the sdist and wheel to dist/
pixi run -e test-py315 python tools/benchmark.py  # the numbers in docs/backends.md
```

The MPI tests run `tests/mpi/check.py` under `mpiexec`, and are skipped where
mpi4py or `mpiexec` is missing; deselect them with `-m "not mpi"`. conda-forge
does not have every optional dependency for every free-threaded build yet; the
tests of a backend that is missing are skipped.

If you prefer not to use pixi, `uv run pytest` runs the tests of the backends in
the standard library.

## Releasing

1. Update `CHANGELOG.md`.
2. `pixi run -e build bump minor` (or `major`, `patch`) bumps the version in
   `pyproject.toml`, commits, tags and pushes.
3. The tag triggers the `Release` workflow, which tests, builds, publishes to
   PyPI through trusted publishing, and creates a GitHub release, which Zenodo
   archives under a new DOI.
4. The conda-forge bot then opens a pull request on
   [map_parallel-feedstock](https://github.com/conda-forge/map_parallel-feedstock).
