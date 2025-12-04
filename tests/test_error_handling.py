# 🧪 Test Error Handling Module

"""Test script for error handling utilities."""

import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.utils import retry_with_backoff, NetworkError, RateLimitError, handle_github_response
import requests

print("=" * 60)
print("🧪 Testing Error Handling Module")
print("=" * 60)

tests_passed = 0
tests_failed = 0

# Test 1: Retry decorator with success
print("\n[1/4] Testing retry decorator - success case...")
call_count = 0

@retry_with_backoff(max_retries=3, initial_delay=0.1)
def flaky_function():
    global call_count
    call_count += 1
    if call_count < 3:
        raise ValueError("Temporary error")
    return "success"

try:
    call_count = 0
    result = flaky_function()
    assert result == "success"
    assert call_count == 3  # Should have retried twice
    print(f"✅ PASS - Retry decorator works (retried {call_count - 1} times)")
    tests_passed += 1
except Exception as e:
    print(f"❌ FAIL - {e}")
    tests_failed += 1

# Test 2: Retry decorator with max retries exceeded
print("\n[2/4] Testing retry decorator - max retries...")

@retry_with_backoff(max_retries=2, initial_delay=0.1)
def always_fails():
    raise ValueError("Always fails")

try:
    always_fails()
    print("❌ FAIL - Should have raised exception")
    tests_failed += 1
except ValueError:
    print("✅ PASS - Correctly raised exception after max retries")
    tests_passed += 1

# Test 3: GitHub response handler - success
print("\n[3/4] Testing GitHub response handler...")

class MockResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text

try:
    response = MockResponse(200, "OK")
    handled = handle_github_response(response)
    assert handled.status_code == 200
    print("✅ PASS - Successfully handled 200 response")
    tests_passed += 1
except Exception as e:
    print(f"❌ FAIL - {e}")
    tests_failed += 1

# Test 4: GitHub response handler - rate limit
print("\n[4/4] Testing rate limit detection...")

try:
    response = MockResponse(403, "API rate limit exceeded")
    handle_github_response(response)
    print("❌ FAIL - Should have raised RateLimitError")
    tests_failed += 1
except RateLimitError as e:
    print(f"✅ PASS - Correctly detected rate limit: {e}")
    tests_passed += 1
except Exception as e:
    print(f"❌ FAIL - Wrong exception type: {e}")
    tests_failed += 1

# Summary
print("\n" + "=" * 60)
print("📊 TEST SUMMARY")
print("=" * 60)
print(f"✅ Passed: {tests_passed}/4")
print(f"❌ Failed: {tests_failed}/4") 
print(f"Success Rate: {tests_passed/4*100:.1f}%")

if tests_failed == 0:
    print("\n🎉 All error handling tests passed!")
    sys.exit(0)
else:
    print(f"\n⚠️  {tests_failed} test(s) failed")
    sys.exit(1)
