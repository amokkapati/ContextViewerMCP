#!/usr/bin/env python3
"""Orchestrator: runs all evaluation tests against the ContextViewerMCP server.

Usage:
    python evaluation/run_all.py
"""

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time

import requests

# Resolve paths relative to this script
EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(EVAL_DIR)
RESULTS_DIR = os.path.join(EVAL_DIR, "results")
SERVER_SCRIPT = os.path.join(PROJECT_ROOT, "server.py")


def find_free_port():
    """Find an available TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


def wait_for_server(url, timeout=15):
    """Poll the server until it responds or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200:
                return True
        except requests.ConnectionError:
            pass
        time.sleep(0.3)
    return False


def main():
    # Create temp directory for test data
    tmp_dir = tempfile.mkdtemp(prefix="ctxviewer_eval_")
    os.makedirs(RESULTS_DIR, exist_ok=True)

    port = find_free_port()
    base_url = f"http://localhost:{port}"

    print(f"Evaluation temp dir: {tmp_dir}")
    print(f"Results dir:         {RESULTS_DIR}")
    print(f"Server port:         {port}")
    print()

    # Start the server
    print("Starting server...")
    server_proc = subprocess.Popen(
        [sys.executable, SERVER_SCRIPT, str(port), "--serve-dir", tmp_dir],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        if not wait_for_server(base_url):
            print("ERROR: Server failed to start within timeout.")
            server_proc.terminate()
            sys.exit(1)
        print(f"Server ready at {base_url}\n")

        # Import test modules
        sys.path.insert(0, EVAL_DIR)
        import test_latency
        import test_pdf_accuracy
        import test_concurrency

        saved = []

        # Test 1
        print("=" * 60)
        print("Test 1: File Serving Latency vs File Size")
        print("=" * 60)
        saved.append(test_latency.run(base_url, tmp_dir, RESULTS_DIR))
        print()

        # Test 2
        print("=" * 60)
        print("Test 2: PDF Text Extraction Accuracy")
        print("=" * 60)
        saved.append(test_pdf_accuracy.run(base_url, tmp_dir, RESULTS_DIR))
        print()

        # Test 3
        print("=" * 60)
        print("Test 3: Concurrent Request Throughput")
        print("=" * 60)
        saved.append(test_concurrency.run(base_url, tmp_dir, RESULTS_DIR))
        print()

        # Summary
        print("=" * 60)
        print("All tests complete. Saved graphs:")
        print("=" * 60)
        for path in saved:
            print(f"  {path}")

    finally:
        # Stop server
        print("\nStopping server...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_proc.kill()

        # Clean up temp directory
        shutil.rmtree(tmp_dir, ignore_errors=True)
        print("Cleanup complete.")


if __name__ == "__main__":
    main()
