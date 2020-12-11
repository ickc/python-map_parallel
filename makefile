MPIARGS ?= -oversubscribe

mpi:
	mpiexec $(MPIARGS) -np 2 coverage run --parallel-mode --branch tests/map_parallel_mpi_test.py
	mpiexec $(MPIARGS) -np 2 coverage run --parallel-mode --branch tests/starmap_parallel_mpi_test.py
	mpiexec $(MPIARGS) -np 1 coverage run --parallel-mode --branch tests/starmap_parallel_mpi_test.py
	mpiexec $(MPIARGS) -np 1 coverage run --parallel-mode --branch tests/map_parallel_mpi_test.py
