#!/usr/bin/env python3
"""
Test script for ContextViewer MCP server.

This script helps verify that the MCP server is working correctly.
"""

import json
import subprocess
import sys
import time
from pathlib import Path


def test_dependencies():
    """Test that required dependencies are installed."""
    print("Testing dependencies...")

    # Test Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print("✓ Python version OK")

    # Test MCP module
    try:
        import mcp
        print("✓ MCP module installed")
    except ImportError:
        print("❌ MCP module not installed. Run: pip install -r requirements.txt")
        return False

    # Test pdflatex (optional)
    try:
        result = subprocess.run(
            ["pdflatex", "--version"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0:
            print("✓ pdflatex installed")
        else:
            print("⚠ pdflatex not working properly")
    except FileNotFoundError:
        print("⚠ pdflatex not installed (LaTeX rendering will not work)")
    except subprocess.TimeoutExpired:
        print("⚠ pdflatex timeout")

    return True


def test_file_structure():
    """Test that required files exist."""
    print("\nTesting file structure...")

    required_files = [
        "mcp_server.py",
        "server.py",
        "requirements.txt",
    ]

    all_exist = True
    for filename in required_files:
        filepath = Path(__file__).parent / filename
        if filepath.exists():
            print(f"✓ {filename} exists")
        else:
            print(f"❌ {filename} missing")
            all_exist = False

    return all_exist


def test_http_server():
    """Test that the HTTP server can start."""
    print("\nTesting HTTP server...")

    try:
        # Start server on a random port
        port = 9999
        proc = subprocess.Popen(
            [sys.executable, str(Path(__file__).parent / "server.py"), str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Give it time to start
        time.sleep(2)

        # Check if process is still running
        if proc.poll() is None:
            print(f"✓ HTTP server started on port {port}")
            proc.terminate()
            proc.wait(timeout=5)
            return True
        else:
            stdout, stderr = proc.communicate()
            print(f"❌ HTTP server failed to start")
            print(f"stdout: {stdout}")
            print(f"stderr: {stderr}")
            return False

    except Exception as e:
        print(f"❌ Error testing HTTP server: {e}")
        return False


def test_state_file():
    """Test state file creation."""
    print("\nTesting state file...")

    state_file = Path.home() / ".context-viewer-state.json"

    # Create a test state
    test_state = {
        "test": True,
        "timestamp": time.time(),
    }

    try:
        with open(state_file, "w") as f:
            json.dump(test_state, f)
        print(f"✓ State file writable at {state_file}")

        # Read it back
        with open(state_file, "r") as f:
            state = json.load(f)

        if state.get("test") is True:
            print("✓ State file readable")
            return True
        else:
            print("❌ State file content mismatch")
            return False

    except Exception as e:
        print(f"❌ State file error: {e}")
        return False


def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("\n1. Install dependencies (if not already done):")
    print("   pip install -r requirements.txt")
    print("\n2. Update Claude Desktop config:")
    print("   File: ~/Library/Application Support/Claude/claude_desktop_config.json")
    print("\n   Add this server configuration (update path):")
    config = {
        "mcpServers": {
            "context-viewer": {
                "command": "python3",
                "args": [str(Path(__file__).parent / "mcp_server.py")],
            }
        }
    }
    print(json.dumps(config, indent=2))
    print("\n3. Restart Claude Desktop")
    print("\n4. In Claude, try:")
    print("   'Can you open the context viewer?'")
    print("\n" + "=" * 60)


def main():
    """Run all tests."""
    print("=" * 60)
    print("ContextViewer MCP Server - Test Suite")
    print("=" * 60)

    tests = [
        ("Dependencies", test_dependencies),
        ("File Structure", test_file_structure),
        ("HTTP Server", test_http_server),
        ("State File", test_state_file),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ {name} test failed with exception: {e}")
            results[name] = False

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n✅ All tests passed! The MCP server is ready to use.")
        print_next_steps()
        return 0
    else:
        print("\n⚠ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
