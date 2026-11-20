"""Time the backends on three workloads, for docs/backends.md.

    pixi run -e test-py315 python tools/benchmark.py
    pixi run -e test-py315t python tools/benchmark.py

- cpu: 8 calls of CPU-bound pure Python, ~0.25 s each, on 8 workers;
- io: 8 calls that each wait 0.25 s, on 8 workers;
- overhead: 100,000 calls that do nearly nothing, on 4 workers, at
  chunksize 1 and 100.
"""

import sys
import sysconfig
import time

from map_parallel import map_parallel

# about 0.25 s on a Ryzen 9 9950X
N = 9_000_000
MODES = ["serial", "multiprocessing", "multithreading"]
if sys.version_info >= (3, 14):
    MODES.append("multiinterpreter")


def cpu(n: int) -> int:
    return sum(i * i for i in range(n))


def io(seconds: float) -> None:
    time.sleep(seconds)


def nothing(x: int) -> int:
    return x


def timed(f, *args, **kwargs) -> float:
    t = time.perf_counter()
    map_parallel(f, *args, **kwargs)
    return time.perf_counter() - t


def main() -> None:
    gil = "free-threaded" if sysconfig.get_config_var("Py_GIL_DISABLED") else "GIL"
    print(f"Python {sys.version.split()[0]} ({gil})")
    print(f"{'mode':<18}{'cpu ×8':>10}{'io ×8':>10}{'overhead, chunksize 1':>24}{'100':>8}")
    for mode in MODES:
        cpu_time = timed(cpu, [N] * 8, mode=mode, processes=8)
        io_time = timed(io, [0.25] * 8, mode=mode, processes=8)
        overhead = [timed(nothing, range(100_000), mode=mode, processes=4, chunksize=c) for c in (1, 100)]
        print(f"{mode:<18}{cpu_time:>9.2f}s{io_time:>9.2f}s{overhead[0]:>23.2f}s{overhead[1]:>7.2f}s")


if __name__ == "__main__":
    main()
