mpi:
	mpiexec -oversubscribe -np 2 coverage run --parallel-mode --branch tests/map_parallel_mpi_test.py
	mpiexec -oversubscribe -np 2 coverage run --parallel-mode --branch tests/starmap_parallel_mpi_test.py
	mpiexec -oversubscribe -np 1 coverage run --parallel-mode --branch tests/starmap_parallel_mpi_test.py
	mpiexec -oversubscribe -np 1 coverage run --parallel-mode --branch tests/map_parallel_mpi_test.py
