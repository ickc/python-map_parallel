"""Print what the tests depend on, at the top of a CI job's log."""

import importlib.util
import multiprocessing
import platform
import shutil
import subprocess
import sys
import sysconfig

import map_parallel

print(f"map_parallel {map_parallel.__version__} on Python {sys.version}")
print(f"platform: {platform.platform()} ({platform.machine()})")
print(f"free-threaded build: {bool(sysconfig.get_config_var('Py_GIL_DISABLED'))}")
print(f"multiprocessing start method: {multiprocessing.get_start_method()}")
print(f"InterpreterPoolExecutor: {sys.version_info >= (3, 14)}")
for module in ("distributed", "mpi4py"):
    spec = importlib.util.find_spec(module)
    if spec is None:
        print(f"{module}: missing")
    else:
        mod = __import__(module)
        print(f"{module}: {mod.__version__}")
if importlib.util.find_spec("mpi4py") is not None:
    import mpi4py

    print(f"mpi4py config: {mpi4py.get_config()}")
mpiexec = shutil.which("mpiexec")
print(f"mpiexec: {mpiexec}")
if hasattr(sys, "_is_gil_enabled"):
    # after importing the optional backends, which might re-enable it
    print(f"GIL enabled: {sys._is_gil_enabled()}")
if mpiexec is not None and platform.system() != "Windows":
    subprocess.run([mpiexec, "--version"], check=False)
