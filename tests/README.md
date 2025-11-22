# 🧪 APEX System - Tests

Comprehensive test suite for APEX System with unit and integration tests.

---

## 📊 Test Coverage

### **Unit Tests**
- ✅ **OAuth Service** (`test_oauth_service.py`) - 20+ tests
  - Initiate authorization (Google, Twitter with PKCE)
  - Complete authorization (success, invalid state, expired state)
  - Get token (valid, auto-refresh)
  - Refresh token
  - Revoke token
  - Event publishing
  - Domain models (OAuthToken, OAuthState)

- ✅ **Q-Learning Algorithm** (`test_q_learning.py`) - 25+ tests
  - Add experience (valid, invalid reward/context/action)
  - Process experiences (Q-Learning formula)
  - Generate action (Epsilon-Greedy, heuristics)
  - Dual buffer (auto-process, overflow, cleanup)
  - Q-Table operations
  - Strategy management
  - Learning metrics
  - Load/save strategies

### **Integration Tests**
- ✅ **Event Bus** (`test_event_bus.py`) - 15+ tests
  - Event creation and serialization
  - Publish/subscribe
  - Event handling
  - Correlation ID propagation
  - RL Engine event handlers integration
  - Campaign performance events
  - Strategy feedback events
  - Reward calculation

---

## 🚀 Running Tests

### **Install Dependencies**
```bash
pip install pytest pytest-asyncio pytest-cov
```

### **Run All Tests**
```bash
pytest
```

### **Run Unit Tests Only**
```bash
pytest tests/unit/
```

### **Run Integration Tests Only**
```bash
pytest tests/integration/
```

### **Run Specific Test File**
```bash
# OAuth tests
pytest tests/unit/test_oauth_service.py

# Q-Learning tests
pytest tests/unit/test_q_learning.py

# Event Bus tests
pytest tests/integration/test_event_bus.py
```

### **Run with Coverage**
```bash
pytest --cov=src --cov-report=html
```

### **Run with Verbose Output**
```bash
pytest -v
```

### **Run Specific Test**
```bash
pytest tests/unit/test_oauth_service.py::test_initiate_authorization_google -v
```

---

## 📁 Test Structure

```
tests/
├── __init__.py
├── conftest.py                          # Shared fixtures
├── README.md                            # This file
├── unit/
│   ├── __init__.py
│   ├── test_oauth_service.py            # OAuth Service tests (500+ lines)
│   └── test_q_learning.py               # Q-Learning tests (600+ lines)
└── integration/
    ├── __init__.py
    └── test_event_bus.py                # Event Bus tests (400+ lines)
```

---

## 🧪 Test Examples

### **OAuth Service Test**
```python
@pytest.mark.asyncio
async def test_complete_authorization_success(oauth_service, mock_oauth_repository):
    """Test completing OAuth authorization successfully"""
    # Setup
    valid_state = OAuthState(
        state_token="test_state_123",
        platform=OAuthPlatform.GOOGLE,
        user_id="test_user_123",
        redirect_uri="http://localhost:8000/auth/google/callback",
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    mock_oauth_repository.get_state.return_value = valid_state

    # Execute
    token = await oauth_service.complete_authorization(
        platform=OAuthPlatform.GOOGLE,
        authorization_code="test_auth_code",
        state_token="test_state_123"
    )

    # Verify
    assert token.platform == OAuthPlatform.GOOGLE
    assert token.access_token is not None
```

### **Q-Learning Test**
```python
def test_process_experiences_q_learning_formula(q_learning_engine):
    """Test Q-Learning formula"""
    # Add experiences
    q_learning_engine.add_experience(
        context="MAXIMIZE_ROAS",
        action="focus_high_value_audiences",
        reward=0.8
    )

    # Process
    result = q_learning_engine.process_experiences()

    # Verify Q-values calculated
    assert "MAXIMIZE_ROAS" in q_learning_engine.q_table.table
    assert result["strategies_created"] == 1
```

### **Event Bus Test**
```python
@pytest.mark.asyncio
async def test_rl_engine_event_handler_integration():
    """Test RL Engine learns from traffic events"""
    # Create traffic event
    traffic_event = Event(
        event_type="traffic.request_completed",
        source_service="traffic-manager",
        data={
            "context": "MAXIMIZE_ROAS",
            "action": "focus_high_value_audiences",
            "success": True,
            "metrics": {"roas": 3.2, "ctr": 2.8, "conversions": 35}
        }
    )

    # Handle event
    await event_handlers.handle_traffic_request_completed(traffic_event)

    # Verify RL Engine learned
    assert len(rl_engine.dual_buffer.active_buffer) == 1
```

---

## 📈 Coverage Report

After running tests with coverage, open the HTML report:
```bash
open htmlcov/index.html
```

---

## ✅ Test Statistics

```
Total Tests: 60+
├── Unit Tests: 45+
│   ├── OAuth Service: 20 tests
│   └── Q-Learning: 25 tests
└── Integration Tests: 15+
    └── Event Bus: 15 tests

Test Lines: ~1,500 lines
Coverage Target: >80%
```

---

## 🎯 Testing Best Practices

### **1. Use Fixtures**
```python
@pytest.fixture
def oauth_service(mock_oauth_repository, mock_event_bus):
    return OAuthService(
        oauth_repository=mock_oauth_repository,
        event_bus=mock_event_bus
    )
```

### **2. Mock External Dependencies**
```python
@pytest.fixture
def mock_oauth_repository():
    repository = AsyncMock()
    repository.save_token = AsyncMock(return_value=True)
    return repository
```

### **3. Test Edge Cases**
```python
def test_add_experience_invalid_reward(q_learning_engine):
    """Test with invalid reward"""
    with pytest.raises(InvalidRewardException):
        q_learning_engine.add_experience(
            context="TEST",
            action="test_action",
            reward=1.5  # Invalid: > 1.0
        )
```

### **4. Use Descriptive Names**
```python
# Good
def test_complete_authorization_with_expired_state_raises_error()

# Bad
def test_auth()
```

### **5. Test One Thing**
Each test should verify one specific behavior.

---

## 🐛 Debugging Tests

### **Run with Print Statements**
```bash
pytest -s tests/unit/test_oauth_service.py
```

### **Run with PDB Debugger**
```bash
pytest --pdb tests/unit/test_oauth_service.py
```

### **Stop on First Failure**
```bash
pytest -x
```

---

## 📝 Writing New Tests

### **Template for Unit Test**
```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_my_feature(my_fixture):
    """Test description"""
    # Setup
    # ... prepare test data

    # Execute
    result = await my_function()

    # Verify
    assert result is not None
    assert result.property == expected_value
```

### **Template for Integration Test**
```python
import pytest

@pytest.mark.asyncio
@pytest.mark.integration
async def test_integration_scenario():
    """Test full workflow"""
    # Setup components
    # Execute workflow
    # Verify end-to-end behavior
```

---

## 🎉 Continuous Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements/test.txt
    pytest --cov=src --cov-report=xml
```

---

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
