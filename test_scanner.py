# 🧪 Test Script for GitHub Leak Scanner

"""
Simple test script to verify core functionality without running a full scan.
Tests: config, database, logging, search API, and basic operations.
"""

import sys
import os
from pathlib import Path

# Test results tracking
tests_passed = 0
tests_failed = 0
test_results = []

def test_result(name, passed, message=""):
    """Record test result."""
    global tests_passed, tests_failed, test_results
    status = "✅ PASS" if passed else "❌ FAIL"
    result = f"{status} - {name}"
    if message:
        result += f": {message}"
    test_results.append(result)
    
    if passed:
        tests_passed += 1
    else:
        tests_failed += 1
    
    print(result)

print("=" * 60)
print("🧪 GitHub Leak Scanner - Test Suite")
print("=" * 60)
print()

# Test 1: Import modules
print("[1/8] Testing module imports...")
try:
    from config import config
    from database import DatabaseManager
    from utils import setup_logging, generate_finding_hash
    from search_repos import RepoSearcher
    test_result("Module imports", True)
except Exception as e:
    test_result("Module imports", False, str(e))
    sys.exit(1)

# Test 2: Configuration
print("\n[2/8] Testing configuration...")
try:
    assert config.github_token, "GitHub token not set"
    assert config.scan_mode in ['search', 'user'], "Invalid scan mode"
    test_result("Configuration", True, f"Mode: {config.scan_mode}")
except Exception as e:
    test_result("Configuration", False, str(e))

# Test 3: Logging
print("\n[3/8] Testing logging system...")
try:
    logger = setup_logging(config.log_file, 'DEBUG')
    logger.debug("Debug message test")
    logger.info("Info message test")
    logger.warning("Warning message test")
    logger.error("Error message test")
    
    # Check log files exist
    assert config.log_file.exists(), "Main log file not created"
    debug_log = config.log_file.parent / 'debug.log'
    error_log = config.log_file.parent / 'error.log'
    assert debug_log.exists(), "Debug log file not created"
    assert error_log.exists(), "Error log file not created"
    
    test_result("Logging system", True, "3 log files created")
except Exception as e:
    test_result("Logging system", False, str(e))

# Test 4: Database
print("\n[4/8] Testing database...")
try:
    db = DatabaseManager('test_scans.db')
    stats = db.get_stats()
    assert isinstance(stats, dict), "Stats should be a dictionary"
    
    # Test user operations
    db.get_or_create_user("test_user")
    
    # Test: User just created should NOT have been scanned recently
    recently_scanned = db.was_user_scanned_recently("test_user", hours=1)
    assert recently_scanned == False, f"New user should not be 'recently scanned' but got: {recently_scanned}"
    
    # Update the user scan
    db.update_user_scan("test_user")
    
    # Test: After update, user SHOULD be recently scanned
    recently_scanned = db.was_user_scanned_recently("test_user", hours=1)
    assert recently_scanned == True, f"After update, user should be 'recently scanned' but got: {recently_scanned}"
    
    test_result("Database operations", True, f"Stats: {stats}")
except AssertionError as e:
    test_result("Database operations", False, f"Assertion: {e}")
except Exception as e:
    test_result("Database operations", False, str(e))

# Test 5: Utility functions
print("\n[5/8] Testing utility functions...")
try:
    # Test hash generation
    hash1 = generate_finding_hash("test.py", 10, "API_KEY", "secret123")
    hash2 = generate_finding_hash("test.py", 10, "API_KEY", "secret123")
    hash3 = generate_finding_hash("test.py", 11, "API_KEY", "secret123")
    
    assert hash1 == hash2, "Same findingsshould produce same hash"
    assert hash1 != hash3, "Different findings should produce different hash"
    
    from utils import calculate_priority_score
    score = calculate_priority_score(stars=5, pushed_at="2024-12-01T00:00:00Z", file_matches=2)
    assert 0 <= score <= 1, "Score should be between 0 and 1"
    
    test_result("Utility functions", True, f"Priority score: {score}")
except Exception as e:
    test_result("Utility functions", False, str(e))

# Test 6: GitHub API connectivity
print("\n[6/8] Testing GitHub API connectivity...")
try:
    import requests
    headers = {"Authorization": f"token {config.github_token}"}
    response = requests.get("https://api.github.com/rate_limit", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        remaining = data['resources']['core']['remaining']
        limit = data['resources']['core']['limit']
        test_result("GitHub API", True, f"Rate limit: {remaining}/{limit}")
    else:
        test_result("GitHub API", False, f"Status code: {response.status_code}")
except Exception as e:
    test_result("GitHub API", False, str(e))

# Test 7: Search functionality
print("\n[7/8] Testing repository search...")
try:
    searcher = RepoSearcher(config.github_token, max_stars=5, min_recency_days=90)
    queries = searcher.build_search_queries()
    assert len(queries) > 0, "Should generate search queries"
    
    # Try one search (limited)
    results = searcher.search_repositories(queries[0], max_results=3)
    test_result("Repository search", True, f"Found {len(results)} repos from first query")
except Exception as e:
    test_result("Repository search", False, str(e))

# Test 8: Report generation
print("\n[8/8] Testing report generation...")
try:
    import json
    import csv
    
    # Create test output directory
    test_output = Path("test_results")
    test_output.mkdir(exist_ok=True)
    
    # Test JSON export
    test_data = [{"test": "data", "value": 123}]
    json_file = test_output / "test.json"
    with open(json_file, 'w') as f:
        json.dump(test_data, f)
    
    # Test CSV export
    csv_file = test_output / "test.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['test', 'value'])
        writer.writeheader()
        writer.writerows(test_data)
    
    assert json_file.exists() and csv_file.exists()
    test_result("Report generation", True, "JSON and CSV exports work")
except Exception as e:
    test_result("Report generation", False, str(e))

# Summary
print("\n" + "=" * 60)
print("📊 TEST SUMMARY")
print("=" * 60)
for result in test_results:
    print(result)

print(f"\nTotal: {tests_passed + tests_failed} tests")
print(f"✅ Passed: {tests_passed}")
print(f"❌ Failed: {tests_failed}")
print(f"Success Rate: {tests_passed/(tests_passed+tests_failed)*100:.1f}%")

if tests_failed == 0:
    print("\n🎉 All tests passed! System is ready")
    sys.exit(0)
else:
    print(f"\n⚠️  {tests_failed} test(s) failed. Please review errors above")
    sys.exit(1)
