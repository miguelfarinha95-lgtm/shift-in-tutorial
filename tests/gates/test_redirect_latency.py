"""SLI 1 gate: p95 server latency for GET /{code} must be < 50 ms (docs/slis.md).

Starts a real uvicorn server in a subprocess so the measurement travels a real
TCP loopback stack. On loopback, socket overhead is sub-millisecond constant
noise; RTT ≈ server processing time for this SLO margin.
"""

import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

import httpx2
import pytest

SAMPLE_COUNT = 200
P95_SLO_MS = 50  # docs/slis.md SLI 1


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def live_server():
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "snip.main:app",
            "--app-dir", "src",
            "--host", "127.0.0.1",
            "--port", str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(f"{base_url}/api/links", timeout=1)
            break
        except urllib.error.URLError:
            time.sleep(0.1)
    else:
        proc.terminate()
        pytest.fail("uvicorn did not start within 15 s")

    yield base_url

    proc.terminate()
    proc.wait(timeout=5)


def test_p95_redirect_latency_under_slo(live_server):
    """SLI 1: p95 latency for GET /{code} must be under the SLO of 50 ms."""
    with httpx2.Client(base_url=live_server) as client:
        resp = client.post("/api/links", json={"url": "https://example.com/perf-target"})
        assert resp.status_code == 201
        code = resp.json()["code"]

        latencies_ms = []
        for _ in range(SAMPLE_COUNT):
            t0 = time.perf_counter()
            client.get(f"/{code}", follow_redirects=False)
            latencies_ms.append((time.perf_counter() - t0) * 1000)

    sorted_ms = sorted(latencies_ms)
    p95 = sorted_ms[int(SAMPLE_COUNT * 0.95) - 1]
    p50 = sorted_ms[int(SAMPLE_COUNT * 0.50) - 1]

    print(
        f"\nredirect latency  p50={p50:.2f} ms  p95={p95:.2f} ms"
        f"  SLO=<{P95_SLO_MS} ms  n={SAMPLE_COUNT}"
    )

    assert p95 < P95_SLO_MS, (
        f"p95 redirect latency {p95:.2f} ms exceeds SLO of {P95_SLO_MS} ms"
    )
