__version__ = '0.1.1'

from functools import partial
from itertools import starmap
from typing import Optional


def _starfunc(f, x):
    '''return f(*x)
    '''
    return f(*x)


def _map_parallel_multiprocessing(
    f, *args,
    processes: Optional[int] = None,
):
    from concurrent.futures import ProcessPoolExecutor

    with ProcessPoolExecutor(max_workers=processes) as process_pool_executor:
        return list(process_pool_executor.map(f, *args))


def _starmap_parallel_multiprocessing(
    f, args,
    processes: Optional[int] = None,
):
    from concurrent.futures import ProcessPoolExecutor

    with ProcessPoolExecutor(max_workers=processes) as process_pool_executor:
        return list(process_pool_executor.map(partial(_starfunc, f), args))


def _map_parallel_multithreading(
    f, *args,
    processes: Optional[int] = None,
):
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=processes) as thread_pool_executor:
        return list(thread_pool_executor.map(f, *args))


def _starmap_parallel_multithreading(
    f, args,
    processes: Optional[int] = None,
):
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=processes) as thread_pool_executor:
        return list(thread_pool_executor.map(partial(_starfunc, f), args))


def _map_parallel_dask(
    f, *args,
    processes: Optional[int] = None,
):
    from dask.distributed import Client
    from dask.distributed import LocalCluster

    cluster = LocalCluster(n_workers=processes, dashboard_address=None)
    client = Client(cluster)
    return [future.result() for future in client.map(f, *args)]


def _starmap_parallel_dask(
    f, args,
    processes: Optional[int] = None,
):
    from dask.distributed import Client
    from dask.distributed import LocalCluster

    cluster = LocalCluster(n_workers=processes, dashboard_address=None)
    client = Client(cluster)
    return [future.result() for future in client.map(partial(_starfunc, f), args)]


def _map_parallel_mpi(f, *args, **kwargs):
    from mpi4py.futures import MPIPoolExecutor

    with MPIPoolExecutor() as mpi_pool_executor:
        return list(mpi_pool_executor.map(f, *args))


def _starmap_parallel_mpi(f, args, **kwargs):
    from mpi4py.futures import MPIPoolExecutor

    with MPIPoolExecutor() as mpi_pool_executor:
        return list(mpi_pool_executor.starmap(f, args))


_map_parallel_func = {
    'multiprocessing': _map_parallel_multiprocessing,
    'multithreading': _map_parallel_multithreading,
    'dask': _map_parallel_dask,
    'mpi': _map_parallel_mpi,
}


_starmap_parallel_func = {
    'multiprocessing': _starmap_parallel_multiprocessing,
    'multithreading': _starmap_parallel_multithreading,
    'dask': _starmap_parallel_dask,
    'mpi': _starmap_parallel_mpi,
}


def map_parallel(
    f, *args,
    processes: Optional[int] = None,
    mode: str = 'multiprocessing',
):
    '''equiv to `map(f, *args)` but in parallel

    :param str mode: backend for parallelization
        - multiprocessing: using multiprocessing from standard library
        - multithreading: using multithreading from standard library
        - dask: using dask.distributed
        - mpi: using mpi4py.futures. May not work depending on your MPI vendor
        - serial: using map
    :param int processes: no. of parallel processes

    (in the case of mpi, it is determined by mpiexec/mpirun args)
    '''
    if processes is None or processes > 1:
        try:
            return _map_parallel_func[mode](f, *args, processes=processes)
        except KeyError:
            pass
    return list(map(f, *args))


def starmap_parallel(
    f, args,
    processes: Optional[int] = None,
    mode: str = 'multiprocessing',
):
    '''equiv to `starmap(f, args)` but in parallel

    :param str mode: backend for parallelization
        - multiprocessing: using multiprocessing from standard library
        - multithreading: using multithreading from standard library
        - dask: using dask.distributed
        - mpi: using mpi4py.futures. May not work depending on your MPI vendor
        - serial: using map
    :param int processes: no. of parallel processes

    (in the case of mpi, it is determined by mpiexec/mpirun args)
    '''
    if processes is None or processes > 1:
        try:
            return _starmap_parallel_func[mode](f, args, processes=processes)
        except KeyError:
            pass
    return list(starmap(f, args))
