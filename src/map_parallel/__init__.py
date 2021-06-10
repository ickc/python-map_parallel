# py37
# from __future__ import annotations

__version__ = '0.2.0'

from itertools import starmap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, Callable, Dict
    from collections.abc import Iterable


def _map_parallel_multiprocessing(
    f: 'Callable',
    *args: 'Iterable',
    processes: 'Optional[int]' = None,
    return_results: 'bool' = True,
) -> 'list':
    from concurrent.futures import ProcessPoolExecutor

    with ProcessPoolExecutor(max_workers=processes) as process_pool_executor:
        res = process_pool_executor.map(f, *args)
        if return_results:
            return list(res)
        else:
            return []


def _map_parallel_multithreading(
    f: 'Callable',
    *args: 'Iterable',
    processes: 'Optional[int]' = None,
    return_results: 'bool' = True,
) -> 'list':
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=processes) as thread_pool_executor:
        res = thread_pool_executor.map(f, *args)
        if return_results:
            return list(res)
        else:
            return []


def _map_parallel_dask(
    f: 'Callable',
    *args: 'Iterable',
    processes: 'Optional[int]' = None,
    return_results: 'bool' = True,
) -> 'list':
    from dask.distributed import Client
    from dask.distributed import LocalCluster

    cluster = LocalCluster(n_workers=processes, dashboard_address=None)
    client = Client(cluster)
    if return_results:
        return [future.result() for future in client.map(f, *args)]
    else:
        for future in client.map(f, *args):
            future.result()
        return []


def _map_parallel_mpi(f: 'Callable', *args: 'Iterable', return_results: 'bool' = True, **kwargs) -> 'list':
    from mpi4py.futures import MPIPoolExecutor

    with MPIPoolExecutor() as mpi_pool_executor:
        res = mpi_pool_executor.map(f, *args)
        if return_results:
            return list(res)
        else:
            return []


def _starmap_parallel_mpi(f: 'Callable', args: 'Iterable[Iterable]', return_results: 'bool' = True, **kwargs) -> 'list':
    from mpi4py.futures import MPIPoolExecutor

    with MPIPoolExecutor() as mpi_pool_executor:
        res = mpi_pool_executor.starmap(f, args)
        if return_results:
            return list(res)
        else:
            return []


def _starmap_parallel_mpi_simple(
    f: 'Callable',
    args: 'Iterable[Iterable]',
    return_results: 'bool' = True,
    **kwargs,
) -> 'list':
    from mpi4py import MPI

    comm = MPI.COMM_WORLD
    size = comm.Get_size()
    rank = comm.Get_rank()

    args_list = list(args)
    if args_list:
        n = len(args_list)
        start = (rank * n) // size
        end = ((rank + 1) * n) // size
        local_args = args_list[start:end]
        res = list(starmap(f, local_args))

        if return_results:
            res = comm.gather(res, root=0)
            if rank == 0:
                return sum(res, [])
    return []


_map_parallel_func: 'Dict[str, Callable]' = {
    'multiprocessing': _map_parallel_multiprocessing,
    'multithreading': _map_parallel_multithreading,
    'dask': _map_parallel_dask,
    'mpi': _map_parallel_mpi,
}

_starmap_parallel_func: 'Dict[str, Callable]' = {
    'mpi': _starmap_parallel_mpi,
    'mpi_simple': _starmap_parallel_mpi_simple,
}


def map_parallel(
    f: 'Callable',
    *args: 'Iterable',
    processes: 'Optional[int]' = None,
    mode: 'str' = 'multiprocessing',
    return_results: 'bool' = True,
) -> 'list':
    '''equiv to `map(f, *args)` but in parallel

    :param str mode: backend for parallelization

        - multiprocessing: using multiprocessing from standard library
        - multithreading: using multithreading from standard library
        - dask: using dask.distributed
        - mpi: using mpi4py.futures. May not work depending on your MPI vendor
        - mpi_simple: using mpi4py with simple scheduling that divides works into equal chunks
        - serial: using map
    :param int processes: no. of parallel processes

        (in the case of mpi, it is determined by mpiexec/mpirun args)

    :param bool return_results: (Only affects mode == 'mpi_simple') if True, return results in rank 0.
    '''
    if processes is None or processes > 1:
        if mode in _map_parallel_func:
            return _map_parallel_func[mode](f, *args, processes=processes, return_results=return_results)
        elif mode in _starmap_parallel_func:
            return _starmap_parallel_func[mode](f, zip(*args), processes=processes, return_results=return_results)
    return list(map(f, *args))


def starmap_parallel(
    f: 'Callable',
    args: 'Iterable[Iterable]',
    processes: 'Optional[int]' = None,
    mode: 'str' = 'multiprocessing',
    return_results: 'bool' = True,
) -> 'list':
    '''equiv to `starmap(f, args)` but in parallel

    See docstring from :func:`~map_parallel.map_parallel`
    '''
    if processes is None or processes > 1:
        if mode in _starmap_parallel_func:
            return _starmap_parallel_func[mode](f, args, processes=processes, return_results=return_results)
        elif mode in _map_parallel_func:
            return _map_parallel_func[mode](f, *zip(*args), processes=processes, return_results=return_results)
    return list(starmap(f, args))
