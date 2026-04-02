"""Test 1: File Serving Latency vs File Size

Measures HTTP GET latency for files of varying sizes served by the
ContextViewerMCP server through /api/file-content/<path>.
"""

import os
import statistics
import time

import matplotlib.pyplot as plt
import requests

# File sizes to test (in bytes)
FILE_SIZES = {
    "1KB": 1024,
    "5KB": 5 * 1024,
    "10KB": 10 * 1024,
    "50KB": 50 * 1024,
    "100KB": 100 * 1024,
    "500KB": 500 * 1024,
    "1MB": 1024 * 1024,
}

REQUESTS_PER_SIZE = 20


def generate_test_files(tmp_dir):
    """Generate text files of various sizes in tmp_dir."""
    filenames = {}
    for label, size in FILE_SIZES.items():
        fname = f"test_{label}.txt"
        path = os.path.join(tmp_dir, fname)
        with open(path, "w") as f:
            # Repeat a line to reach desired size
            line = "A" * 99 + "\n"  # 100 bytes per line
            lines_needed = max(1, size // 100)
            f.write(line * lines_needed)
        filenames[label] = fname
    return filenames


def run(base_url, tmp_dir, results_dir):
    """Run latency benchmark and save graph."""
    filenames = generate_test_files(tmp_dir)

    labels = []
    avg_times = []
    std_times = []
    sizes_kb = []

    for label, fname in filenames.items():
        url = f"{base_url}/api/file-content/{fname}"
        times = []

        # Warm-up request
        requests.get(url)

        for _ in range(REQUESTS_PER_SIZE):
            start = time.perf_counter()
            resp = requests.get(url)
            elapsed = (time.perf_counter() - start) * 1000  # ms
            assert resp.status_code == 200, f"Got {resp.status_code} for {fname}"
            times.append(elapsed)

        avg = statistics.mean(times)
        std = statistics.stdev(times) if len(times) > 1 else 0.0

        labels.append(label)
        avg_times.append(avg)
        std_times.append(std)
        sizes_kb.append(FILE_SIZES[label] / 1024)

        print(f"  {label:>6s}: avg={avg:.2f} ms  std={std:.2f} ms")

    # Plot
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(sizes_kb, avg_times, yerr=std_times, marker="o", capsize=4,
                linewidth=2, color="#2563eb", ecolor="#94a3b8")
    ax.set_xscale("log")
    ax.set_xlabel("File Size (KB)", fontsize=12)
    ax.set_ylabel("Response Time (ms)", fontsize=12)
    ax.set_title("File Serving Latency vs File Size", fontsize=14)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    out_path = os.path.join(results_dir, "latency_vs_filesize.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out_path}")
    return out_path
