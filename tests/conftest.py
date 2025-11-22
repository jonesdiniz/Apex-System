"""
Shared Test Fixtures
Pytest configuration and shared fixtures for all tests
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


# ============================================================================
# ASYNCIO EVENT LOOP
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# SHARED FIXTURES
# ============================================================================

@pytest.fixture
def sample_user_id():
    """Sample user ID for tests"""
    return "test_user_123"


@pytest.fixture
def sample_correlation_id():
    """Sample correlation ID for tests"""
    return "correlation_456"


# ============================================================================
# MARKERS
# ============================================================================

def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "asyncio: Async tests")
