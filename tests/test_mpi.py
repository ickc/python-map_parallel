"""Tests of mode="mpi" and mode="mpi_simple": tests/mpi/check.py, run under mpiexec."""

import os
import platform
import re
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

pytest.importorskip("mpi4py")

MPIEXEC = shutil.which("mpiexec")
TESTS = Path(__file__).parent
N = 3

pytestmark = [
    pytest.mark.mpi,
    pytest.mark.skipif(MPIEXEC is None, reason="mpiexec not found"),
]

# On GitHub's macos-15-intel runners, a call of MPIPoolExecutor took up to 70 s
# on a free-threaded build (0.2 s on Linux, a few seconds on macOS ARM64), which
# is mpi4py.futures', not map_parallel's; mpi_simple stays tested there.
slow_futures = pytest.mark.skipif(
    bool(sysconfig.get_config_var("Py_GIL_DISABLED")) and sys.platform == "darwin" and platform.machine() == "x86_64",
    reason="mpi4py.futures is too slow on free-threaded Python on macOS x86-64",
)


def mpiexec(mode: str, *args: str, n: int = N) -> dict[int, str]:
    """Run check.py on ``n`` MPI processes, and return the line each rank printed, by rank."""
    assert MPIEXEC is not None
    python = [sys.executable, "-m", "mpi4py.futures"] if mode == "mpi" else [sys.executable]
    env = {
        # on one node, UCX (MPICH's transport on Linux) needs no network but
        # TCP: on some CI runners, it fails to open the RDMA device it finds
        "UCX_TLS": "self,sm,tcp",
        **os.environ,
        "PYTHONPATH": os.pathsep.join(filter(None, [str(TESTS), os.environ.get("PYTHONPATH")])),
    }
    # a timeout, rather than a hung job, if a rank waits for another that failed
    try:
        proc = subprocess.run(
            [MPIEXEC, "-n", str(n), *python, str(TESTS / "mpi" / "check.py"), mode, *args],
            capture_output=True,
            text=True,
            env=env,
            timeout=120,
        )
    except subprocess.TimeoutExpired as e:
        pytest.fail(f"timed out after {e.timeout} s\nstdout:\n{e.stdout}\nstderr:\n{e.stderr}")
    assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    lines = {}
    for match in re.finditer(r"^rank (\d+)/(\d+): (.*)$", proc.stdout, re.MULTILINE):
        rank, size, outcome = match.groups()
        assert int(size) == n
        lines[int(rank)] = outcome
    return lines


def test_mpi_simple():
    assert mpiexec("mpi_simple") == {rank: "ok" for rank in range(N)}


@pytest.mark.parametrize("return_results", [True, False])
def test_mpi_simple_exception(return_results):
    """Every rank raises the exception; on the ranks it did not come from, with the remote traceback as its cause."""
    lines = mpiexec("mpi_simple", "--exception", *([] if return_results else ["--no-return-results"]))
    own, remote = "(cause: NoneType)", "(cause: _RemoteTraceback)"
    assert lines == {
        0: f"Bad: bad input: 3 {own}; Bad: bad input: 12 {remote}",
        1: f"Bad: bad input: 3 {remote}; Bad: bad input: 12 {remote}",
        2: f"Bad: bad input: 3 {remote}; Bad: bad input: 12 {own}",
    }


@slow_futures
def test_mpi():
    """With python -m mpi4py.futures, only rank 0 runs the script; the others are the pool's workers."""
    assert mpiexec("mpi") == {0: "ok"}


@slow_futures
@pytest.mark.parametrize("return_results", [True, False])
def test_mpi_exception(return_results):
    lines = mpiexec("mpi", "--exception", *([] if return_results else ["--no-return-results"]))
    assert list(lines) == [0]
    assert re.fullmatch(r"Bad: bad input: 3 \(cause: \w+\); Bad: bad input: 12 \(cause: \w+\)", lines[0]), lines
