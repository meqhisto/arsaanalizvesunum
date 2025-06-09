#!/usr/bin/env python3
"""
Test runner script for the Flask application
"""

import os
import sys
import subprocess
import argparse


def run_tests(test_type="all", coverage=True, verbose=True):
    """
    Run tests with specified options
    
    Args:
        test_type (str): Type of tests to run (all, unit, integration, api)
        coverage (bool): Whether to generate coverage report
        verbose (bool): Whether to run in verbose mode
    """
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test type filter
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "api":
        cmd.extend(["-m", "api"])
    elif test_type == "auth":
        cmd.extend(["-m", "auth"])
    elif test_type == "crm":
        cmd.extend(["-m", "crm"])
    elif test_type == "analysis":
        cmd.extend(["-m", "analysis"])
    
    # Add coverage options
    if coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml"
        ])
    
    # Add verbose option
    if verbose:
        cmd.append("-v")
    
    # Add other useful options
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    print(f"🧪 Running tests: {' '.join(cmd)}")
    print("-" * 50)
    
    # Run the tests
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def run_quick_tests():
    """Run a quick subset of tests for development."""
    print("🚀 Running quick tests...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/test_models.py",
        "-v",
        "--tb=short",
        "--disable-warnings"
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"❌ Error running quick tests: {e}")
        return 1


def run_coverage_report():
    """Generate and display coverage report."""
    print("📊 Generating coverage report...")
    
    # Run tests with coverage
    cmd = [
        "python", "-m", "pytest",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--quiet"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Coverage report generated!")
        print("📁 HTML report: htmlcov/index.html")
        print("📄 XML report: coverage.xml")
        return 0
    except subprocess.CalledProcessError:
        print("❌ Failed to generate coverage report")
        return 1
    except Exception as e:
        print(f"❌ Error generating coverage report: {e}")
        return 1


def check_test_environment():
    """Check if test environment is properly set up."""
    print("🔍 Checking test environment...")
    
    # Check if pytest is installed
    try:
        import pytest
        print(f"✅ pytest {pytest.__version__} is installed")
    except ImportError:
        print("❌ pytest is not installed")
        return False
    
    # Check if coverage is installed
    try:
        import coverage
        print(f"✅ coverage {coverage.__version__} is installed")
    except ImportError:
        print("❌ coverage is not installed")
        return False
    
    # Check if test directory exists
    if os.path.exists("tests"):
        print("✅ tests directory exists")
    else:
        print("❌ tests directory not found")
        return False
    
    # Check if conftest.py exists
    if os.path.exists("tests/conftest.py"):
        print("✅ tests/conftest.py exists")
    else:
        print("❌ tests/conftest.py not found")
        return False
    
    print("✅ Test environment is ready!")
    return True


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="Run tests for the Flask application")
    
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "api", "auth", "crm", "analysis"],
        default="all",
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disable coverage reporting"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Run tests in quiet mode"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick tests only"
    )
    
    parser.add_argument(
        "--coverage-only",
        action="store_true",
        help="Generate coverage report only"
    )
    
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Check test environment setup"
    )
    
    args = parser.parse_args()
    
    # Check environment if requested
    if args.check_env:
        if check_test_environment():
            return 0
        else:
            return 1
    
    # Generate coverage report only
    if args.coverage_only:
        return run_coverage_report()
    
    # Run quick tests
    if args.quick:
        return run_quick_tests()
    
    # Check environment before running tests
    if not check_test_environment():
        print("❌ Test environment is not properly set up")
        return 1
    
    # Run tests
    return run_tests(
        test_type=args.type,
        coverage=not args.no_coverage,
        verbose=not args.quiet
    )


if __name__ == "__main__":
    sys.exit(main())
