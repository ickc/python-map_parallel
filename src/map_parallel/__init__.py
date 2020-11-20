__version__ = '0.1'
from typing import Optional


def _starfunc(f, x):
    '''return f(*x)
    '''
    return f(*x)


def map_parallel(
    f, *args,
    mode: str = 'multiprocessing',
    processes: Optional[int] = None,
):
    '''equiv to map(f, *args) but in parallel

    :param str mode: backend for parallelization

    - multiprocessing: using multiprocessing from standard library
    - multithreading: using multithreading from standard library
    - mpi: using mpi4py.futures. May not work depending on your MPI vendor
    - serial: using map

    :param int processes: no. of parallel processes
    (in the case of mpi, it is determined by mpiexec/mpirun args)
    '''
    if processes is not None and processes == 1:
        result = list(map(f, *args))
    elif mode == 'multiprocessing':
        from concurrent.futures import ProcessPoolExecutor

        with ProcessPoolExecutor(max_workers=processes) as process_pool_executor:
            result = list(process_pool_executor.map(f, *args))
    elif mode == 'multithreading':
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=processes) as thread_pool_executor:
            result = list(thread_pool_executor.map(f, *args))
    elif mode == 'mpi':
        from mpi4py.futures import MPIPoolExecutor

        with MPIPoolExecutor() as mpi_pool_executor:
            result = mpi_pool_executor.map(f, *args)
    else:
        # fallback
        result = list(map(f, *args))
    return result


def starmap_parallel(
    f, args,
    mode: str = 'multiprocessing',
    processes: Optional[int] = None,
):
    '''equiv to starmap(f, args) but in parallel

    :param str mode: backend for parallelization

    - multiprocessing: using multiprocessing from standard library
    - multithreading: using multithreading from standard library
    - mpi: using mpi4py.futures. May not work depending on your MPI vendor
    - serial: using map

    :param int processes: no. of parallel processes
    (in the case of mpi, it is determined by mpiexec/mpirun args)
    '''
    if processes is not None and processes == 1:
        from itertools import starmap

        result = list(starmap(f, args))
    elif mode == 'multiprocessing':
        from functools import partial
        from concurrent.futures import ProcessPoolExecutor

        with ProcessPoolExecutor(max_workers=processes) as process_pool_executor:
            result = list(process_pool_executor.map(partial(_starfunc, f), args))
    elif mode == 'multithreading':
        from functools import partial
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=processes) as thread_pool_executor:
            result = list(thread_pool_executor.map(partial(_starfunc, f), args))
    elif mode == 'mpi':
        from mpi4py.futures import MPIPoolExecutor

        with MPIPoolExecutor() as mpi_pool_executor:
            result = mpi_pool_executor.starmap(f, args)
    else:
        # fallback
        from itertools import starmap
        result = list(starmap(f, args))
    return result
