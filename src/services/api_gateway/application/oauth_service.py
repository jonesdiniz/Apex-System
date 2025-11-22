"""
API Gateway - OAuth Service
Application layer: OAuth 2.0 flow orchestration for 5 platforms
"""

import secrets
import hashlib
import base64
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import httpx

from ..domain.models import (
    OAuthToken,
    OAuthState,
    OAuthPlatform,
    InvalidTokenError,
    InvalidStateError
)
from common.logging import get_logger

logger = get_logger(__name__)


class OAuthService:
    """
    OAuth 2.0 Service - Application Layer

    Orchestrates OAuth flow for multiple platforms:
    - Google (Ads + Analytics)
    - LinkedIn (Ads)
    - Meta/Facebook (Business)
    - Twitter/X (API v2 with PKCE)
    - TikTok (Creator)

    This is platform-agnostic business logic. Platform-specific configs
    are in infrastructure layer.
    """

    def __init__(
        self,
        oauth_repository,  # Infrastructure: Repository for token persistence
        oauth_config_provider,  # Infrastructure: OAuth configs per platform
        event_bus=None  # Optional: Event bus for publishing auth events
    ):
        self.oauth_repository = oauth_repository
        self.oauth_config_provider = oauth_config_provider
        self.event_bus = event_bus

    # =========================================================================
    # AUTHORIZATION FLOW
    # =========================================================================

    async def initiate_authorization(
        self,
        platform: OAuthPlatform,
        user_id: str,
        redirect_uri: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Initiate OAuth 2.0 authorization flow

        Args:
            platform: OAuth platform (Google, Meta, etc)
            user_id: User identifier
            redirect_uri: Custom redirect URI (optional)

        Returns:
            Tuple of (authorization_url, state_token)

        Business Logic:
            1. Generate unique state token (CSRF protection)
            2. For Twitter: Generate PKCE code verifier/challenge
            3. Store state with expiration (10 min)
            4. Build authorization URL with platform-specific params
        """
        # Generate state token (CSRF protection)
        state_token = self._generate_state_token()

        # Get platform configuration
        config = await self.oauth_config_provider.get_config(platform)

        # Create OAuth state
        oauth_state = OAuthState(
            state_token=state_token,
            platform=platform,
            user_id=user_id,
            redirect_uri=redirect_uri or config.redirect_uri
        )

        # Twitter requires PKCE
        if platform == OAuthPlatform.TWITTER:
            code_verifier = self._generate_code_verifier()
            code_challenge = self._generate_code_challenge(code_verifier)
            oauth_state.code_verifier = code_verifier
        else:
            code_challenge = None

        # Store state (with 10 min expiration)
        await self.oauth_repository.save_state(oauth_state)

        # Build authorization URL
        auth_url = self._build_authorization_url(
            config=config,
            state_token=state_token,
            redirect_uri=oauth_state.redirect_uri,
            code_challenge=code_challenge
        )

        logger.info(
            f"OAuth authorization initiated",
            extra={
                "platform": platform.value,
                "user_id": user_id,
                "state": state_token[:8]  # Log prefix only
            }
        )

        return auth_url, state_token

    async def complete_authorization(
        self,
        platform: OAuthPlatform,
        authorization_code: str,
        state_token: str
    ) -> OAuthToken:
        """
        Complete OAuth 2.0 authorization flow

        Args:
            platform: OAuth platform
            authorization_code: Code from OAuth provider
            state_token: State token (CSRF validation)

        Returns:
            OAuthToken with access/refresh tokens

        Business Logic:
            1. Validate state token (prevent CSRF)
            2. Exchange code for access token
            3. Store token in repository
            4. Publish event (optional)
            5. Return token to caller

        Raises:
            InvalidStateError: If state is invalid/expired
            InvalidTokenError: If token exchange fails
        """
        # Validate state
        oauth_state = await self.oauth_repository.get_state(state_token)

        if not oauth_state:
            raise InvalidStateError(f"Invalid or expired state: {state_token}")

        if oauth_state.platform != platform:
            raise InvalidStateError(
                f"Platform mismatch: expected {oauth_state.platform}, got {platform}"
            )

        if not oauth_state.is_valid():
            await self.oauth_repository.delete_state(state_token)
            raise InvalidStateError(f"Expired state: {state_token}")

        # Get platform configuration
        config = await self.oauth_config_provider.get_config(platform)

        # Exchange code for token
        try:
            token_data = await self._exchange_code_for_token(
                config=config,
                authorization_code=authorization_code,
                redirect_uri=oauth_state.redirect_uri,
                code_verifier=oauth_state.code_verifier  # For Twitter PKCE
            )
        except Exception as e:
            logger.error(
                f"Token exchange failed",
                extra={"platform": platform.value, "error": str(e)}
            )
            raise InvalidTokenError(f"Failed to exchange code for token: {e}")

        # Create OAuth token
        expires_at = None
        if "expires_in" in token_data:
            expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])

        oauth_token = OAuthToken(
            platform=platform,
            user_id=oauth_state.user_id,
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            expires_at=expires_at,
            scope=token_data.get("scope"),
            token_type=token_data.get("token_type", "Bearer")
        )

        # Store token
        await self.oauth_repository.save_token(oauth_token)

        # Delete used state
        await self.oauth_repository.delete_state(state_token)

        # Publish event (optional)
        if self.event_bus:
            from common.event_bus import Event, EventPriority

            event = Event(
                event_type="oauth.token_obtained",
                source_service="api-gateway",
                data={
                    "platform": platform.value,
                    "user_id": oauth_state.user_id,
                    "scope": oauth_token.scope
                },
                priority=EventPriority.MEDIUM
            )
            await self.event_bus.publish(event)

        logger.info(
            f"OAuth authorization completed",
            extra={
                "platform": platform.value,
                "user_id": oauth_state.user_id
            }
        )

        return oauth_token

    # =========================================================================
    # TOKEN MANAGEMENT
    # =========================================================================

    async def get_token(
        self,
        platform: OAuthPlatform,
        user_id: str,
        auto_refresh: bool = True
    ) -> Optional[OAuthToken]:
        """
        Get OAuth token for user

        Args:
            platform: OAuth platform
            user_id: User identifier
            auto_refresh: Automatically refresh if needed

        Returns:
            OAuthToken or None if not found

        Business Logic:
            1. Retrieve token from repository
            2. Check if expired
            3. If expired and refresh token available: refresh
            4. Return valid token
        """
        token = await self.oauth_repository.get_token(platform, user_id)

        if not token:
            return None

        # Auto-refresh if needed
        if auto_refresh and token.should_refresh():
            try:
                token = await self.refresh_token(platform, user_id)
            except Exception as e:
                logger.error(
                    f"Auto-refresh failed",
                    extra={"platform": platform.value, "user_id": user_id, "error": str(e)}
                )
                # Return expired token (caller can decide what to do)

        return token

    async def refresh_token(
        self,
        platform: OAuthPlatform,
        user_id: str
    ) -> OAuthToken:
        """
        Refresh OAuth token

        Args:
            platform: OAuth platform
            user_id: User identifier

        Returns:
            New OAuthToken with refreshed access token

        Raises:
            InvalidTokenError: If refresh fails
        """
        # Get current token
        token = await self.oauth_repository.get_token(platform, user_id)

        if not token or not token.refresh_token:
            raise InvalidTokenError(f"No refresh token available for {platform.value}")

        # Get platform configuration
        config = await self.oauth_config_provider.get_config(platform)

        # Exchange refresh token for new access token
        try:
            token_data = await self._refresh_access_token(
                config=config,
                refresh_token=token.refresh_token
            )
        except Exception as e:
            logger.error(
                f"Token refresh failed",
                extra={"platform": platform.value, "user_id": user_id, "error": str(e)}
            )
            raise InvalidTokenError(f"Failed to refresh token: {e}")

        # Update token
        expires_at = None
        if "expires_in" in token_data:
            expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])

        refreshed_token = OAuthToken(
            platform=platform,
            user_id=user_id,
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", token.refresh_token),  # Keep old if not provided
            expires_at=expires_at,
            scope=token_data.get("scope", token.scope),
            token_type=token_data.get("token_type", "Bearer")
        )

        # Save refreshed token
        await self.oauth_repository.save_token(refreshed_token)

        logger.info(
            f"OAuth token refreshed",
            extra={"platform": platform.value, "user_id": user_id}
        )

        return refreshed_token

    async def revoke_token(
        self,
        platform: OAuthPlatform,
        user_id: str
    ) -> bool:
        """
        Revoke OAuth token

        Args:
            platform: OAuth platform
            user_id: User identifier

        Returns:
            True if revoked successfully
        """
        # Delete from repository
        deleted = await self.oauth_repository.delete_token(platform, user_id)

        if deleted:
            logger.info(
                f"OAuth token revoked",
                extra={"platform": platform.value, "user_id": user_id}
            )

        return deleted

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    def _generate_state_token(self) -> str:
        """Generate random state token (32 bytes)"""
        return secrets.token_urlsafe(32)

    def _generate_code_verifier(self) -> str:
        """Generate PKCE code verifier (Twitter)"""
        return secrets.token_urlsafe(32)

    def _generate_code_challenge(self, verifier: str) -> str:
        """Generate PKCE code challenge from verifier"""
        digest = hashlib.sha256(verifier.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')

    def _build_authorization_url(
        self,
        config,
        state_token: str,
        redirect_uri: str,
        code_challenge: Optional[str] = None
    ) -> str:
        """Build platform-specific authorization URL"""
        from urllib.parse import urlencode

        params = {
            "client_id": config.client_id,
            "redirect_uri": redirect_uri,
            "scope": config.scope,
            "response_type": "code",
            "state": state_token
        }

        # Platform-specific parameters
        if config.platform == OAuthPlatform.GOOGLE:
            params["access_type"] = "offline"
            params["prompt"] = "consent"

        elif config.platform == OAuthPlatform.TWITTER:
            if code_challenge:
                params["code_challenge"] = code_challenge
                params["code_challenge_method"] = "S256"

        query_string = urlencode(params)
        return f"{config.auth_url}?{query_string}"

    async def _exchange_code_for_token(
        self,
        config,
        authorization_code: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None
    ) -> Dict:
        """
        Exchange authorization code for access token

        Platform-specific implementation details are handled here.
        """
        token_data = {
            "code": authorization_code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "client_id": config.client_id,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # Twitter requires PKCE and Basic Auth
        if config.platform == OAuthPlatform.TWITTER:
            if code_verifier:
                token_data["code_verifier"] = code_verifier

            # Basic authentication for Twitter
            auth_string = f"{config.client_id}:{config.client_secret}"
            auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
            headers["Authorization"] = f"Basic {auth_b64}"
        else:
            # Other platforms use client_secret in body
            token_data["client_secret"] = config.client_secret

        # Make HTTP request
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                config.token_url,
                data=token_data,
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    async def _refresh_access_token(
        self,
        config,
        refresh_token: str
    ) -> Dict:
        """Refresh access token using refresh token"""
        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": config.client_id,
            "client_secret": config.client_secret
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                config.token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            return response.json()
