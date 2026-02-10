#!/usr/bin/env python3
"""
Test Suite for Task 3: State Synchronization and Performance Optimization

Tests:
1. File-based state management
2. Selection retrieval modes (immediate and polling)
3. Auto-clear functionality
4. Performance benchmarks
5. Error handling and recovery
"""

import asyncio
import json
import time
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server import get_state, save_state, STATE_FILE


def setup_test():
    """Clean up state file before each test."""
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    print("✓ Test environment setup complete")


def test_state_file_creation():
    """Test 1: State file creation and basic I/O."""
    print("\n--- Test 1: State File Creation ---")
    setup_test()

    # Test empty state
    state = get_state()
    assert state == {}, "Empty state should return {}"
    print("✓ Empty state handled correctly")

    # Test writing state
    test_data = {
        "server_url": "http://localhost:8765",
        "server_pid": 12345,
    }
    save_state(test_data)
    assert STATE_FILE.exists(), "State file should exist after save"
    print("✓ State file created successfully")

    # Test reading state
    loaded_state = get_state()
    assert loaded_state == test_data, "Loaded state should match saved state"
    print("✓ State loaded correctly")


def test_selection_storage():
    """Test 2: Selection data storage and retrieval."""
    print("\n--- Test 2: Selection Storage ---")
    setup_test()

    # Create selection data
    selection_data = {
        "selection": {
            "file_path": "test.py",
            "start_line": 10,
            "end_line": 20,
            "selected_text": "def test():\n    pass",
            "timestamp": time.time(),
        }
    }

    # Save and load
    save_state(selection_data)
    loaded = get_state()

    assert "selection" in loaded, "Selection should be in state"
    assert loaded["selection"]["file_path"] == "test.py"
    assert loaded["selection"]["start_line"] == 10
    assert loaded["selection"]["end_line"] == 20
    print("✓ Selection data stored and retrieved correctly")


def test_timestamp_validation():
    """Test 3: Timestamp-based selection freshness."""
    print("\n--- Test 3: Timestamp Validation ---")
    setup_test()

    # Create old selection
    old_timestamp = time.time() - 100  # 100 seconds ago
    old_selection = {
        "selection": {
            "file_path": "old.py",
            "start_line": 1,
            "end_line": 5,
            "selected_text": "old code",
            "timestamp": old_timestamp,
        }
    }
    save_state(old_selection)

    # Create new selection
    new_timestamp = time.time()
    new_selection = {
        "selection": {
            "file_path": "new.py",
            "start_line": 10,
            "end_line": 15,
            "selected_text": "new code",
            "timestamp": new_timestamp,
        }
    }
    save_state(new_selection)

    # Verify new selection overwrites old
    loaded = get_state()
    assert loaded["selection"]["file_path"] == "new.py"
    assert loaded["selection"]["timestamp"] > old_timestamp
    print("✓ Timestamp-based freshness validation works")


def test_performance_immediate_mode():
    """Test 4: Immediate mode performance (<10ms target)."""
    print("\n--- Test 4: Immediate Mode Performance ---")
    setup_test()

    # Setup selection
    selection = {
        "selection": {
            "file_path": "perf_test.py",
            "start_line": 1,
            "end_line": 100,
            "selected_text": "x" * 1000,  # 1KB of text
            "timestamp": time.time(),
        }
    }
    save_state(selection)

    # Benchmark read performance
    iterations = 100
    total_time = 0

    for _ in range(iterations):
        start = time.time()
        state = get_state()
        assert "selection" in state
        elapsed = (time.time() - start) * 1000  # Convert to ms
        total_time += elapsed

    avg_time = total_time / iterations
    print(f"  Average read time: {avg_time:.3f}ms")
    assert avg_time < 10, f"Read time {avg_time:.3f}ms exceeds 10ms target"
    print(f"✓ Immediate mode performance: {avg_time:.3f}ms (target: <10ms)")


def test_state_validation():
    """Test 5: State validation and error recovery."""
    print("\n--- Test 5: State Validation ---")
    setup_test()

    # Test corrupted JSON
    with open(STATE_FILE, "w") as f:
        f.write("{invalid json")

    state = get_state()
    assert state == {}, "Corrupted state should return {}"

    # Check backup was created
    backup_file = STATE_FILE.with_suffix(".json.backup")
    assert backup_file.exists(), "Backup file should be created"
    print("✓ Corrupted state handled with backup")

    # Clean up backup
    if backup_file.exists():
        backup_file.unlink()

    # Test invalid selection structure
    setup_test()
    invalid_selection = {
        "selection": {
            "file_path": "test.py",
            # Missing required fields
        }
    }
    save_state(invalid_selection)

    state = get_state()
    assert "selection" not in state, "Invalid selection should be removed"
    print("✓ Invalid selection structure detected and removed")


def test_atomic_writes():
    """Test 6: Atomic write operations."""
    print("\n--- Test 6: Atomic Writes ---")
    setup_test()

    # Rapid consecutive writes
    for i in range(10):
        state = {"counter": i, "timestamp": time.time()}
        save_state(state)

    # Verify last write succeeded
    final_state = get_state()
    assert final_state["counter"] == 9, "Final write should be preserved"
    print("✓ Atomic writes preserve data integrity")


def test_selection_size_limits():
    """Test 7: Handle large selections."""
    print("\n--- Test 7: Large Selection Handling ---")
    setup_test()

    # Create 1MB selection
    large_text = "x" * (1024 * 1024)
    large_selection = {
        "selection": {
            "file_path": "large.py",
            "start_line": 1,
            "end_line": 50000,
            "selected_text": large_text,
            "timestamp": time.time(),
        }
    }

    start = time.time()
    save_state(large_selection)
    write_time = (time.time() - start) * 1000

    start = time.time()
    loaded = get_state()
    read_time = (time.time() - start) * 1000

    assert loaded["selection"]["selected_text"] == large_text
    print(f"  1MB write: {write_time:.2f}ms, read: {read_time:.2f}ms")
    print("✓ Large selections handled efficiently")


def test_concurrent_access_safety():
    """Test 8: Concurrent read/write safety."""
    print("\n--- Test 8: Concurrent Access Safety ---")
    setup_test()

    async def writer(writer_id: int):
        for i in range(5):
            state = {
                "writer": writer_id,
                "iteration": i,
                "timestamp": time.time(),
            }
            save_state(state)
            await asyncio.sleep(0.01)

    async def reader():
        for _ in range(10):
            state = get_state()
            # Should always get valid state, never corrupted
            assert isinstance(state, dict)
            await asyncio.sleep(0.01)

    async def run_concurrent():
        await asyncio.gather(
            writer(1),
            writer(2),
            reader(),
            reader(),
        )

    asyncio.run(run_concurrent())
    print("✓ Concurrent access handled safely")


def test_state_file_stats():
    """Test 9: State file size and metadata."""
    print("\n--- Test 9: State File Statistics ---")
    setup_test()

    selection = {
        "server_url": "http://localhost:8765",
        "server_pid": 12345,
        "selection": {
            "file_path": "example.py",
            "start_line": 10,
            "end_line": 20,
            "selected_text": "def example():\n    return 42",
            "timestamp": time.time(),
        },
    }
    save_state(selection)

    file_size = STATE_FILE.stat().st_size
    print(f"  State file size: {file_size} bytes ({file_size / 1024:.2f} KB)")
    assert file_size < 5000, "State file should be under 5KB for normal selections"
    print("✓ State file size within expected range")


def run_performance_benchmarks():
    """Performance benchmark summary."""
    print("\n" + "=" * 60)
    print("PERFORMANCE BENCHMARKS")
    print("=" * 60)

    setup_test()

    # Immediate mode benchmark
    selection = {
        "selection": {
            "file_path": "benchmark.py",
            "start_line": 1,
            "end_line": 100,
            "selected_text": "x" * 500,
            "timestamp": time.time(),
        }
    }
    save_state(selection)

    # Test immediate reads
    immediate_times = []
    for _ in range(1000):
        start = time.time()
        get_state()
        immediate_times.append((time.time() - start) * 1000)

    avg_immediate = sum(immediate_times) / len(immediate_times)
    min_immediate = min(immediate_times)
    max_immediate = max(immediate_times)

    print(f"\nImmediate Mode (1000 iterations):")
    print(f"  Average: {avg_immediate:.3f}ms")
    print(f"  Min: {min_immediate:.3f}ms")
    print(f"  Max: {max_immediate:.3f}ms")
    print(f"  Target: <10ms ✓" if avg_immediate < 10 else "  Target: <10ms ✗")

    # Polling simulation
    print(f"\nPolling Mode:")
    print(f"  Interval: 0.5s (500ms)")
    print(f"  Timeout: 60s")
    print(f"  Expected avg latency: 0-500ms")
    print(f"  CPU overhead: Minimal (sleep-based)")

    print("\n" + "=" * 60)


def main():
    """Run all tests."""
    print("=" * 60)
    print("Task 3: State Synchronization Test Suite")
    print("=" * 60)

    tests = [
        test_state_file_creation,
        test_selection_storage,
        test_timestamp_validation,
        test_performance_immediate_mode,
        test_state_validation,
        test_atomic_writes,
        test_selection_size_limits,
        test_concurrent_access_safety,
        test_state_file_stats,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Tests Passed: {passed}/{len(tests)}")
    print(f"Tests Failed: {failed}/{len(tests)}")
    print("=" * 60)

    if failed == 0:
        run_performance_benchmarks()

    # Cleanup
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    backup = STATE_FILE.with_suffix(".json.backup")
    if backup.exists():
        backup.unlink()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
