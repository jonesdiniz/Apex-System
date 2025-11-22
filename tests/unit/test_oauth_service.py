"""
Unit Tests - OAuth Service
Tests for API Gateway OAuth 2.0 flow
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
import httpx

import sys
sys.path.insert(0, '/home/user/Apex-System/src')
sys.path.insert(0, '/home/user/Apex-System/src/services/api_gateway')

from services.api_gateway.domain.models import (
    OAuthToken,
    OAuthState,
    OAuthPlatform,
    InvalidStateError,
    TokenExpiredError
)
from services.api_gateway.application.oauth_service import OAuthService


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_oauth_repository():
    """Mock OAuth repository"""
    repository = AsyncMock()
    repository.save_token = AsyncMock(return_value=True)
    repository.get_token = AsyncMock(return_value=None)
    repository.save_state = AsyncMock(return_value=True)
    repository.get_state = AsyncMock(return_value=None)
    repository.delete_state = AsyncMock(return_value=True)
    return repository


@pytest.fixture
def mock_oauth_config_provider():
    """Mock OAuth config provider"""
    from services.api_gateway.infrastructure.oauth_providers import OAuthProviderConfig

    provider = AsyncMock()

    # Google config
    google_config = OAuthProviderConfig(
        platform=OAuthPlatform.GOOGLE,
        client_id="test_google_client_id",
        client_secret="test_google_client_secret",
        auth_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        revoke_url="https://oauth2.googleapis.com/revoke",
        scope="https://www.googleapis.com/auth/adwords",
        redirect_uri="http://localhost:8000/auth/google/callback"
    )

    # Twitter config (with PKCE)
    twitter_config = OAuthProviderConfig(
        platform=OAuthPlatform.TWITTER,
        client_id="test_twitter_client_id",
        client_secret="test_twitter_client_secret",
        auth_url="https://twitter.com/i/oauth2/authorize",
        token_url="https://api.twitter.com/2/oauth2/token",
        scope="tweet.read users.read",
        redirect_uri="http://localhost:8000/auth/twitter/callback",
        requires_pkce=True
    )

    async def get_config(platform):
        if platform == OAuthPlatform.GOOGLE:
            return google_config
        elif platform == OAuthPlatform.TWITTER:
            return twitter_config
        raise ValueError(f"Unknown platform: {platform}")

    provider.get_config = get_config
    return provider


@pytest.fixture
def mock_event_bus():
    """Mock event bus"""
    event_bus = AsyncMock()
    event_bus.publish = AsyncMock(return_value=True)
    return event_bus


@pytest.fixture
def oauth_service(mock_oauth_repository, mock_oauth_config_provider, mock_event_bus):
    """OAuth service instance with mocks"""
    return OAuthService(
        oauth_repository=mock_oauth_repository,
        oauth_config_provider=mock_oauth_config_provider,
        event_bus=mock_event_bus
    )


# ============================================================================
# TEST: INITIATE AUTHORIZATION
# ============================================================================

@pytest.mark.asyncio
async def test_initiate_authorization_google(oauth_service, mock_oauth_repository):
    """Test initiating OAuth authorization for Google"""
    # Execute
    auth_url, state_token = await oauth_service.initiate_authorization(
        platform=OAuthPlatform.GOOGLE,
        user_id="test_user_123"
    )

    # Verify
    assert auth_url is not None
    assert state_token is not None
    assert "accounts.google.com" in auth_url
    assert "state=" in auth_url
    assert "client_id=" in auth_url
    assert "redirect_uri=" in auth_url
    assert "scope=" in auth_url

    # Verify state was saved
    mock_oauth_repository.save_state.assert_called_once()
    saved_state = mock_oauth_repository.save_state.call_args[0][0]
    assert saved_state.state_token == state_token
    assert saved_state.platform == OAuthPlatform.GOOGLE
    assert saved_state.user_id == "test_user_123"


@pytest.mark.asyncio
async def test_initiate_authorization_twitter_with_pkce(oauth_service, mock_oauth_repository):
    """Test initiating OAuth authorization for Twitter with PKCE"""
    # Execute
    auth_url, state_token = await oauth_service.initiate_authorization(
        platform=OAuthPlatform.TWITTER,
        user_id="test_user_456"
    )

    # Verify
    assert auth_url is not None
    assert state_token is not None
    assert "twitter.com" in auth_url
    assert "code_challenge=" in auth_url  # PKCE
    assert "code_challenge_method=S256" in auth_url

    # Verify state was saved with code_verifier
    mock_oauth_repository.save_state.assert_called_once()
    saved_state = mock_oauth_repository.save_state.call_args[0][0]
    assert saved_state.code_verifier is not None  # PKCE verifier
    assert len(saved_state.code_verifier) == 128


# ============================================================================
# TEST: COMPLETE AUTHORIZATION
# ============================================================================

@pytest.mark.asyncio
async def test_complete_authorization_success(oauth_service, mock_oauth_repository):
    """Test completing OAuth authorization successfully"""
    # Setup - valid state
    valid_state = OAuthState(
        state_token="test_state_123",
        platform=OAuthPlatform.GOOGLE,
        user_id="test_user_123",
        redirect_uri="http://localhost:8000/auth/google/callback",
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    mock_oauth_repository.get_state.return_value = valid_state

    # Mock HTTP request for token exchange
    mock_response = Mock()
    mock_response.json.return_value = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_in": 3600,
        "token_type": "Bearer"
    }

    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        # Execute
        token = await oauth_service.complete_authorization(
            platform=OAuthPlatform.GOOGLE,
            authorization_code="test_auth_code",
            state_token="test_state_123"
        )

    # Verify token
    assert token is not None
    assert token.platform == OAuthPlatform.GOOGLE
    assert token.user_id == "test_user_123"
    assert token.access_token == "test_access_token"
    assert token.refresh_token == "test_refresh_token"
    assert token.expires_at is not None

    # Verify token was saved
    mock_oauth_repository.save_token.assert_called_once()

    # Verify state was deleted
    mock_oauth_repository.delete_state.assert_called_once_with("test_state_123")


@pytest.mark.asyncio
async def test_complete_authorization_invalid_state(oauth_service, mock_oauth_repository):
    """Test completing OAuth authorization with invalid state"""
    # Setup - no state found
    mock_oauth_repository.get_state.return_value = None

    # Execute and verify exception
    with pytest.raises(InvalidStateError):
        await oauth_service.complete_authorization(
            platform=OAuthPlatform.GOOGLE,
            authorization_code="test_auth_code",
            state_token="invalid_state"
        )


@pytest.mark.asyncio
async def test_complete_authorization_expired_state(oauth_service, mock_oauth_repository):
    """Test completing OAuth authorization with expired state"""
    # Setup - expired state
    expired_state = OAuthState(
        state_token="test_state_123",
        platform=OAuthPlatform.GOOGLE,
        user_id="test_user_123",
        redirect_uri="http://localhost:8000/auth/google/callback",
        expires_at=datetime.utcnow() - timedelta(minutes=5)  # Expired
    )
    mock_oauth_repository.get_state.return_value = expired_state

    # Execute and verify exception
    with pytest.raises(InvalidStateError):
        await oauth_service.complete_authorization(
            platform=OAuthPlatform.GOOGLE,
            authorization_code="test_auth_code",
            state_token="test_state_123"
        )


@pytest.mark.asyncio
async def test_complete_authorization_with_pkce(oauth_service, mock_oauth_repository):
    """Test completing OAuth authorization with PKCE (Twitter)"""
    # Setup - valid state with code_verifier
    valid_state = OAuthState(
        state_token="test_state_456",
        platform=OAuthPlatform.TWITTER,
        user_id="test_user_456",
        redirect_uri="http://localhost:8000/auth/twitter/callback",
        code_verifier="x" * 128,  # PKCE verifier
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    mock_oauth_repository.get_state.return_value = valid_state

    # Mock HTTP request
    mock_response = Mock()
    mock_response.json.return_value = {
        "access_token": "test_twitter_access_token",
        "refresh_token": "test_twitter_refresh_token",
        "expires_in": 7200,
        "token_type": "Bearer"
    }

    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.post = AsyncMock(return_value=mock_response)

        # Execute
        token = await oauth_service.complete_authorization(
            platform=OAuthPlatform.TWITTER,
            authorization_code="test_auth_code",
            state_token="test_state_456"
        )

        # Verify PKCE code_verifier was sent in token request
        call_args = mock_instance.post.call_args
        request_data = call_args[1]['data']
        assert 'code_verifier' in request_data
        assert request_data['code_verifier'] == "x" * 128


# ============================================================================
# TEST: GET TOKEN
# ============================================================================

@pytest.mark.asyncio
async def test_get_token_exists_and_valid(oauth_service, mock_oauth_repository):
    """Test getting an existing valid token"""
    # Setup - valid token
    valid_token = OAuthToken(
        platform=OAuthPlatform.GOOGLE,
        user_id="test_user_123",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    mock_oauth_repository.get_token.return_value = valid_token

    # Execute
    token = await oauth_service.get_token(
        platform=OAuthPlatform.GOOGLE,
        user_id="test_user_123",
        auto_refresh=False
    )

    # Verify
    assert token == valid_token
    assert not token.is_expired()


@pytest.mark.asyncio
async def test_get_token_not_found(oauth_service, mock_oauth_repository):
    """Test getting token that doesn't exist"""
    # Setup
    mock_oauth_repository.get_token.return_value = None

    # Execute
    token = await oauth_service.get_token(
        platform=OAuthPlatform.GOOGLE,
        user_id="test_user_123"
    )

    # Verify
    assert token is None


@pytest.mark.asyncio
async def test_get_token_auto_refresh_when_expiring(oauth_service, mock_oauth_repository):
    """Test auto-refresh when token is expiring soon"""
    # Setup - token expiring in 3 minutes
    expiring_token = OAuthToken(
        platform=OAuthPlatform.GOOGLE,
        user_id="test_user_123",
        access_token="old_access_token",
        refresh_token="test_refresh_token",
        expires_at=datetime.utcnow() + timedelta(minutes=3)
    )
    mock_oauth_repository.get_token.return_value = expiring_token

    # Mock refresh response
    mock_response = Mock()
    mock_response.json.return_value = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "expires_in": 3600,
        "token_type": "Bearer"
    }

    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        # Execute with auto_refresh=True
        token = await oauth_service.get_token(
            platform=OAuthPlatform.GOOGLE,
            user_id="test_user_123",
            auto_refresh=True
        )

    # Verify token was refreshed
    assert token.access_token == "new_access_token"

    # Verify new token was saved
    assert mock_oauth_repository.save_token.call_count >= 1


# ============================================================================
# TEST: REFRESH TOKEN
# ============================================================================

@pytest.mark.asyncio
async def test_refresh_token_success(oauth_service, mock_oauth_repository):
    """Test refreshing token successfully"""
    # Setup - existing token
    existing_token = OAuthToken(
        platform=OAuthPlatform.GOOGLE,
        user_id="test_user_123",
        access_token="old_access_token",
        refresh_token="test_refresh_token",
        expires_at=datetime.utcnow() + timedelta(minutes=3)
    )
    mock_oauth_repository.get_token.return_value = existing_token

    # Mock refresh response
    mock_response = Mock()
    mock_response.json.return_value = {
        "access_token": "new_access_token",
        "refresh_token": "new_refresh_token",
        "expires_in": 3600,
        "token_type": "Bearer"
    }

    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        # Execute
        new_token = await oauth_service.refresh_token(
            platform=OAuthPlatform.GOOGLE,
            user_id="test_user_123"
        )

    # Verify
    assert new_token.access_token == "new_access_token"
    assert new_token.refresh_token == "new_refresh_token"

    # Verify token was saved
    mock_oauth_repository.save_token.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_token_no_refresh_token(oauth_service, mock_oauth_repository):
    """Test refreshing token when no refresh token exists"""
    # Setup - token without refresh_token
    token_without_refresh = OAuthToken(
        platform=OAuthPlatform.GOOGLE,
        user_id="test_user_123",
        access_token="test_access_token",
        refresh_token=None,  # No refresh token
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    mock_oauth_repository.get_token.return_value = token_without_refresh

    # Execute and verify exception
    with pytest.raises(Exception):  # Should raise error
        await oauth_service.refresh_token(
            platform=OAuthPlatform.GOOGLE,
            user_id="test_user_123"
        )


# ============================================================================
# TEST: REVOKE TOKEN
# ============================================================================

@pytest.mark.asyncio
async def test_revoke_token_success(oauth_service, mock_oauth_repository):
    """Test revoking token successfully"""
    # Setup - existing token
    existing_token = OAuthToken(
        platform=OAuthPlatform.GOOGLE,
        user_id="test_user_123",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    mock_oauth_repository.get_token.return_value = existing_token

    # Mock revoke response
    mock_response = Mock()
    mock_response.status_code = 200

    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        # Execute
        result = await oauth_service.revoke_token(
            platform=OAuthPlatform.GOOGLE,
            user_id="test_user_123"
        )

    # Verify
    assert result is True

    # Verify token was deleted
    mock_oauth_repository.delete_token.assert_called_once()


# ============================================================================
# TEST: EVENT PUBLISHING
# ============================================================================

@pytest.mark.asyncio
async def test_complete_authorization_publishes_event(oauth_service, mock_oauth_repository, mock_event_bus):
    """Test that completing authorization publishes an event"""
    # Setup
    valid_state = OAuthState(
        state_token="test_state_123",
        platform=OAuthPlatform.GOOGLE,
        user_id="test_user_123",
        redirect_uri="http://localhost:8000/auth/google/callback",
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    mock_oauth_repository.get_state.return_value = valid_state

    # Mock token response
    mock_response = Mock()
    mock_response.json.return_value = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_in": 3600,
        "token_type": "Bearer"
    }

    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        # Execute
        await oauth_service.complete_authorization(
            platform=OAuthPlatform.GOOGLE,
            authorization_code="test_auth_code",
            state_token="test_state_123"
        )

    # Verify event was published
    mock_event_bus.publish.assert_called_once()
    event = mock_event_bus.publish.call_args[0][0]
    assert event.event_type == "oauth.token_obtained"
    assert event.data["platform"] == "google"
    assert event.data["user_id"] == "test_user_123"


# ============================================================================
# TEST: DOMAIN MODELS
# ============================================================================

def test_oauth_token_is_expired():
    """Test OAuthToken.is_expired()"""
    # Valid token
    valid_token = OAuthToken(
        platform=OAuthPlatform.GOOGLE,
        user_id="test_user",
        access_token="token",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    assert not valid_token.is_expired()

    # Expired token
    expired_token = OAuthToken(
        platform=OAuthPlatform.GOOGLE,
        user_id="test_user",
        access_token="token",
        expires_at=datetime.utcnow() - timedelta(hours=1)
    )
    assert expired_token.is_expired()

    # Token without expiration
    no_expiry_token = OAuthToken(
        platform=OAuthPlatform.GOOGLE,
        user_id="test_user",
        access_token="token",
        expires_at=None
    )
    assert not no_expiry_token.is_expired()


def test_oauth_token_should_refresh():
    """Test OAuthToken.should_refresh()"""
    # Token expiring in 3 minutes (should refresh with 5-min buffer)
    expiring_token = OAuthToken(
        platform=OAuthPlatform.GOOGLE,
        user_id="test_user",
        access_token="token",
        refresh_token="refresh",
        expires_at=datetime.utcnow() + timedelta(minutes=3)
    )
    assert expiring_token.should_refresh(buffer_minutes=5)

    # Token expiring in 10 minutes (should NOT refresh with 5-min buffer)
    valid_token = OAuthToken(
        platform=OAuthPlatform.GOOGLE,
        user_id="test_user",
        access_token="token",
        refresh_token="refresh",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    assert not valid_token.should_refresh(buffer_minutes=5)

    # Token without refresh_token (cannot refresh)
    no_refresh_token = OAuthToken(
        platform=OAuthPlatform.GOOGLE,
        user_id="test_user",
        access_token="token",
        refresh_token=None,
        expires_at=datetime.utcnow() + timedelta(minutes=3)
    )
    assert not no_refresh_token.should_refresh()


def test_oauth_state_is_valid():
    """Test OAuthState.is_valid()"""
    # Valid state
    valid_state = OAuthState(
        state_token="token",
        platform=OAuthPlatform.GOOGLE,
        user_id="user",
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    assert valid_state.is_valid()

    # Expired state
    expired_state = OAuthState(
        state_token="token",
        platform=OAuthPlatform.GOOGLE,
        user_id="user",
        expires_at=datetime.utcnow() - timedelta(minutes=5)
    )
    assert not expired_state.is_valid()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
