"""Test 3: Concurrent Request Throughput

Measures average response time and success rate under varying levels of
concurrent HTTP load against the ContextViewerMCP server.
"""

import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import matplotlib.pyplot as plt
import requests

CONCURRENCY_LEVELS = [1, 5, 10, 25, 50]
REQUESTS_PER_LEVEL = 50  # total requests at each concurrency level
TEST_FILE_SIZE = 50 * 1024  # 50KB


def generate_test_file(tmp_dir):
    """Generate a 50KB test file."""
    fname = "concurrent_test.txt"
    path = os.path.join(tmp_dir, fname)
    line = "X" * 99 + "\n"
    lines_needed = TEST_FILE_SIZE // 100
    with open(path, "w") as f:
        f.write(line * lines_needed)
    return fname


def _fetch(url):
    """Make a single GET request, return (elapsed_ms, success)."""
    try:
        start = time.perf_counter()
        resp = requests.get(url, timeout=30)
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed, resp.status_code == 200
    except Exception:
        return None, False


def run(base_url, tmp_dir, results_dir):
    """Run concurrency benchmark and save graph."""
    fname = generate_test_file(tmp_dir)
    url = f"{base_url}/api/file-content/{fname}"

    # Warm-up
    requests.get(url)

    levels = []
    avg_times = []
    success_rates = []

    for n in CONCURRENCY_LEVELS:
        times = []
        successes = 0

        with ThreadPoolExecutor(max_workers=n) as pool:
            futures = [pool.submit(_fetch, url) for _ in range(REQUESTS_PER_LEVEL)]
            for f in as_completed(futures):
                elapsed, ok = f.result()
                if ok and elapsed is not None:
                    times.append(elapsed)
                    successes += 1

        avg = statistics.mean(times) if times else 0
        rate = (successes / REQUESTS_PER_LEVEL) * 100

        levels.append(n)
        avg_times.append(avg)
        success_rates.append(rate)
        print(f"  Concurrency {n:>3d}: avg={avg:.2f} ms  success={rate:.1f}%")

    # Plot — dual-axis
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax2 = ax1.twinx()

    line1, = ax1.plot(levels, avg_times, "o-", color="#2563eb", linewidth=2,
                      label="Avg Response Time")
    line2, = ax2.plot(levels, success_rates, "s--", color="#16a34a", linewidth=2,
                      label="Success Rate")

    ax1.set_xlabel("Concurrency Level", fontsize=12)
    ax1.set_ylabel("Avg Response Time (ms)", fontsize=12, color="#2563eb")
    ax2.set_ylabel("Success Rate (%)", fontsize=12, color="#16a34a")
    ax1.tick_params(axis="y", labelcolor="#2563eb")
    ax2.tick_params(axis="y", labelcolor="#16a34a")
    ax2.set_ylim(0, 105)

    ax1.set_title("Concurrent Request Throughput", fontsize=14)
    ax1.grid(True, alpha=0.3)

    lines = [line1, line2]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="center right", fontsize=10)

    fig.tight_layout()

    out_path = os.path.join(results_dir, "concurrent_throughput.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out_path}")
    return out_path
