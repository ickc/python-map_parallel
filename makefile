MPIARGS ?= -oversubscribe
N_PROC ?= 1

all:
	$(MAKE) mpi N_PROC=1
	$(MAKE) mpi N_PROC=2

mpi:
	mpiexec $(MPIARGS) -np $(N_PROC) coverage run --parallel-mode --branch tests/map_parallel_mpi_test.py
	mpiexec $(MPIARGS) -np $(N_PROC) coverage run --parallel-mode --branch tests/map_parallel_mpi_simple_test.py
	mpiexec $(MPIARGS) -np $(N_PROC) coverage run --parallel-mode --branch tests/starmap_parallel_mpi_test.py
	mpiexec $(MPIARGS) -np $(N_PROC) coverage run --parallel-mode --branch tests/starmap_parallel_mpi_simple_test.py
