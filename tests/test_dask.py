"""Tests of mode="dask".

Kept apart from test_core.py, which runs first, because the cluster leaves
threads behind, and forking a process with threads (multiprocessing's default
on Linux before Python 3.14) can deadlock.
"""

import os
import time

import pytest

distributed = pytest.importorskip("distributed")

import test_core as core  # noqa: E402
import workloads as w  # noqa: E402

from map_parallel import map_parallel, starmap_parallel  # noqa: E402

# without an active client: a LocalCluster per call ###########################
# These run first, before the module's client below starts.


def _no_client():
    with pytest.raises(ValueError):
        distributed.default_client()


def test_local_cluster():
    _no_client()
    assert map_parallel(w.f, *w.COLUMNS, mode="dask") == w.TRUTH
    assert starmap_parallel(w.f, w.ARGS, mode="dask", processes=2, chunksize=3) == w.TRUTH
    # and it is closed afterwards
    _no_client()


def test_local_cluster_processes():
    """processes is the number of single-threaded worker processes."""
    pids = map_parallel(w.pid, range(16), mode="dask", processes=2)
    assert os.getpid() not in pids
    assert 1 <= len(set(pids)) <= 2


def test_local_cluster_exception():
    with pytest.raises(w.Bad, match="bad input: 3"):
        map_parallel(w.fail_on, range(8), mode="dask", processes=2, return_results=False)
    _no_client()


# with an active client ########################################################


@pytest.fixture(scope="module")
def client():
    with (
        distributed.LocalCluster(n_workers=2, threads_per_worker=1, dashboard_address=None) as cluster,
        distributed.Client(cluster) as client,
    ):
        yield client


@pytest.fixture
def mode(client):
    return "dask"


def test_active_client(client):
    """The active client is used, rather than a new cluster."""
    workers = set(client.scheduler_info()["workers"])
    addresses = map_parallel(lambda _: distributed.get_worker().address, range(8), mode="dask", processes=8)
    assert set(addresses) <= workers


def test_active_client_cancels_on_exception(client):
    """On an exception, the other tasks are cancelled: nothing is left on the user's cluster."""
    with pytest.raises(w.Bad):
        map_parallel(w.fail_on, range(64), mode="dask")
    # cancelling is asynchronous
    deadline = time.monotonic() + 30
    while client.who_has() and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not client.who_has()


# the backend-independent tests, on the active client
test_map_parallel = core.test_map_parallel
test_starmap_parallel = core.test_starmap_parallel
test_chunksize = core.test_chunksize
test_no_return_results = core.test_no_return_results
test_exception_propagates = core.test_exception_propagates
test_empty = core.test_empty
test_shortest_iterable = core.test_shortest_iterable
test_ragged_starmap = core.test_ragged_starmap
test_iterators = core.test_iterators
test_order = core.test_order
test_impure = core.test_impure
test_partial = core.test_partial
