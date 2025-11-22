#!/usr/bin/env python3
"""
APEX System - Installation Verification Script
Smoke test to verify the system can boot without errors

This script:
1. Checks if MongoDB and Redis are running
2. Verifies all critical modules can be imported
3. Checks for syntax errors and circular dependencies
4. Validates configuration files

Run this BEFORE starting Docker containers to catch issues early.
"""

import sys
import os
from pathlib import Path
import importlib.util

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.ENDC} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.ENDC} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.ENDC} {msg}")

def print_section(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}\n")

def check_python_version():
    """Verify Python version is 3.11+"""
    print_section("Checking Python Version")

    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python 3.11+ required, found {version.major}.{version.minor}.{version.micro}")
        return False

def check_project_structure():
    """Verify critical directories exist"""
    print_section("Checking Project Structure")

    project_root = Path(__file__).parent
    critical_dirs = [
        "src",
        "src/common",
        "src/infrastructure",
        "src/services",
        "src/services/api_gateway",
        "src/services/rl_engine",
        "tests",
        "requirements",
        "docker"
    ]

    all_exist = True
    for dir_path in critical_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print_success(f"{dir_path}/")
        else:
            print_error(f"{dir_path}/ NOT FOUND")
            all_exist = False

    return all_exist

def check_dependencies():
    """Check if critical dependencies can be imported"""
    print_section("Checking Python Dependencies")

    # Add src to path for imports
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root / "src"))

    critical_deps = [
        ("fastapi", "FastAPI"),
        ("pydantic", "Pydantic"),
        ("motor", "Motor (MongoDB async driver)"),
        ("redis", "Redis"),
        ("httpx", "HTTPX"),
        ("uvicorn", "Uvicorn"),
    ]

    all_ok = True
    for module, name in critical_deps:
        try:
            __import__(module)
            print_success(f"{name}")
        except ImportError as e:
            print_error(f"{name} - {e}")
            all_ok = False

    return all_ok

def check_module_imports():
    """Verify critical modules can be imported without errors"""
    print_section("Checking Module Imports (Syntax & Circular Dependencies)")

    # Add src to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root / "src"))

    critical_modules = [
        ("common.logging", "Common Logging"),
        ("common.exceptions", "Common Exceptions"),
        ("common.constants", "Common Constants"),
        ("common.models", "Common Models"),
        ("common.event_bus", "Event Bus"),
        ("infrastructure.database", "Database Infrastructure"),
        ("infrastructure.cache", "Cache Infrastructure"),
        ("services.api_gateway.domain.models", "API Gateway Domain"),
        ("services.rl_engine.domain.models", "RL Engine Domain"),
        ("services.rl_engine.domain.q_learning", "Q-Learning Engine"),
    ]

    all_ok = True
    for module_name, display_name in critical_modules:
        try:
            module = __import__(module_name, fromlist=[''])
            print_success(f"{display_name} ({module_name})")
        except ImportError as e:
            print_error(f"{display_name} - ImportError: {e}")
            all_ok = False
        except SyntaxError as e:
            print_error(f"{display_name} - SyntaxError: {e}")
            all_ok = False
        except Exception as e:
            print_warning(f"{display_name} - Warning: {e}")

    return all_ok

def check_infrastructure():
    """Check if MongoDB and Redis are accessible"""
    print_section("Checking Infrastructure Services")

    # MongoDB
    try:
        import pymongo
        client = pymongo.MongoClient(
            "mongodb://localhost:27017/",
            serverSelectionTimeoutMS=2000
        )
        client.server_info()
        print_success("MongoDB is running (localhost:27017)")
        mongodb_ok = True
    except Exception as e:
        print_warning(f"MongoDB not accessible: {e}")
        print_warning("Start MongoDB with: docker-compose up -d mongodb")
        mongodb_ok = False

    # Redis
    try:
        import redis as redis_module
        r = redis_module.Redis(host='localhost', port=6379, socket_timeout=2)
        r.ping()
        print_success("Redis is running (localhost:6379)")
        redis_ok = True
    except Exception as e:
        print_warning(f"Redis not accessible: {e}")
        print_warning("Start Redis with: docker-compose up -d redis")
        redis_ok = False

    return mongodb_ok and redis_ok

def check_environment_files():
    """Check for .env files"""
    print_section("Checking Environment Configuration")

    project_root = Path(__file__).parent

    env_file = project_root / ".env"
    if env_file.exists():
        print_success(".env file found")
        return True
    else:
        print_warning(".env file not found (optional)")
        print_warning("Create .env for custom configuration")
        return True  # Not critical

def check_dockerfiles():
    """Verify all Dockerfiles exist"""
    print_section("Checking Docker Configuration")

    project_root = Path(__file__).parent
    docker_dir = project_root / "docker"

    if not docker_dir.exists():
        print_error("docker/ directory not found")
        return False

    dockerfiles = [
        "Dockerfile.api-gateway",
        "Dockerfile.rl-engine",
        "Dockerfile.ecosystem-platform",
        "Dockerfile.creative-studio",
        "Dockerfile.future-casting",
        "Dockerfile.immune-system",
        "Dockerfile.proactive-conversation"
    ]

    all_exist = True
    for dockerfile in dockerfiles:
        full_path = docker_dir / dockerfile
        if full_path.exists():
            print_success(f"{dockerfile}")
        else:
            print_error(f"{dockerfile} NOT FOUND")
            all_exist = False

    # Check docker-compose.yml
    compose_file = project_root / "docker-compose.yml"
    if compose_file.exists():
        print_success("docker-compose.yml")
    else:
        print_error("docker-compose.yml NOT FOUND")
        all_exist = False

    return all_exist

def verify_api_gateway_config():
    """Verify API Gateway can be configured"""
    print_section("Verifying API Gateway Configuration")

    try:
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from services.api_gateway.infrastructure.config import get_settings

        settings = get_settings()
        print_success(f"Service: {settings.service_name}")
        print_success(f"Port: {settings.service_port}")
        print_success(f"Environment: {settings.environment}")
        return True
    except Exception as e:
        print_error(f"API Gateway config error: {e}")
        return False

def verify_rl_engine_config():
    """Verify RL Engine can be configured"""
    print_section("Verifying RL Engine Configuration")

    try:
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from services.rl_engine.infrastructure.config import get_settings

        settings = get_settings()
        print_success(f"Service: {settings.service_name}")
        print_success(f"Port: {settings.service_port}")
        print_success(f"Learning Rate: {settings.learning_rate}")
        print_success(f"Discount Factor: {settings.discount_factor}")
        print_success(f"Exploration Rate: {settings.exploration_rate}")
        return True
    except Exception as e:
        print_error(f"RL Engine config error: {e}")
        return False

def main():
    """Run all verification checks"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("APEX SYSTEM - INSTALLATION VERIFICATION")
    print("=" * 60)
    print(f"{Colors.ENDC}\n")

    checks = [
        ("Python Version", check_python_version),
        ("Project Structure", check_project_structure),
        ("Python Dependencies", check_dependencies),
        ("Module Imports", check_module_imports),
        ("Infrastructure Services", check_infrastructure),
        ("Environment Files", check_environment_files),
        ("Docker Configuration", check_dockerfiles),
        ("API Gateway Config", verify_api_gateway_config),
        ("RL Engine Config", verify_rl_engine_config),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Unexpected error in {name}: {e}")
            results.append((name, False))

    # Summary
    print_section("Verification Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        if result:
            print_success(f"{name}")
        else:
            print_error(f"{name}")

    print(f"\n{Colors.BOLD}Results: {passed}/{total} checks passed{Colors.ENDC}\n")

    if passed == total:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL CHECKS PASSED{Colors.ENDC}")
        print(f"{Colors.GREEN}System is ready to start!{Colors.ENDC}")
        print(f"{Colors.GREEN}Run: docker-compose up -d{Colors.ENDC}\n")
        return 0
    else:
        failed = total - passed
        print(f"{Colors.RED}{Colors.BOLD}✗ {failed} CHECK(S) FAILED{Colors.ENDC}")
        print(f"{Colors.RED}Please fix the errors above before starting.{Colors.ENDC}\n")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
