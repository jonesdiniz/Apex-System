"""
API Gateway - OAuth Authentication Router
FastAPI endpoints for OAuth 2.0 flow
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse
from typing import Optional

from ...domain.models import OAuthPlatform, InvalidStateError, InvalidTokenError
from ...application.oauth_service import OAuthService
from ..dependencies import get_oauth_service
from common.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["OAuth 2.0"])


@router.get("/{platform}/authorize")
async def authorize(
    platform: str,
    user_id: str = Query(..., description="User identifier"),
    redirect_uri: Optional[str] = Query(None, description="Custom redirect URI"),
    oauth_service: OAuthService = Depends(get_oauth_service)
):
    """
    Initiate OAuth 2.0 authorization flow

    **Supported Platforms**:
    - `google` - Google Ads + Analytics
    - `linkedin` - LinkedIn Ads
    - `meta` - Meta/Facebook Business
    - `twitter` - Twitter/X API v2
    - `tiktok` - TikTok Creator

    **Flow**:
    1. Generate state token (CSRF protection)
    2. Redirect user to platform authorization page
    3. User approves access
    4. Platform redirects back to callback endpoint
    """
    try:
        # Validate platform
        try:
            oauth_platform = OAuthPlatform(platform.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported platform: {platform}. Supported: google, linkedin, meta, twitter, tiktok"
            )

        # Initiate authorization
        auth_url, state_token = await oauth_service.initiate_authorization(
            platform=oauth_platform,
            user_id=user_id,
            redirect_uri=redirect_uri
        )

        logger.info(
            f"OAuth authorization initiated",
            extra={
                "platform": platform,
                "user_id": user_id,
                "state": state_token[:8]
            }
        )

        # Redirect to platform authorization page
        return RedirectResponse(url=auth_url, status_code=302)

    except Exception as e:
        logger.error(
            f"Failed to initiate OAuth",
            extra={"platform": platform, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Authorization failed: {str(e)}")


@router.get("/{platform}/callback")
async def callback(
    platform: str,
    code: str = Query(..., description="Authorization code from OAuth provider"),
    state: str = Query(..., description="State token for CSRF validation"),
    oauth_service: OAuthService = Depends(get_oauth_service)
):
    """
    OAuth 2.0 callback endpoint

    Called by OAuth provider after user authorizes access.

    **Process**:
    1. Validate state token (CSRF protection)
    2. Exchange authorization code for access token
    3. Store tokens in database
    4. Redirect to frontend with success message
    """
    try:
        # Validate platform
        try:
            oauth_platform = OAuthPlatform(platform.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

        # Complete authorization
        try:
            token = await oauth_service.complete_authorization(
                platform=oauth_platform,
                authorization_code=code,
                state_token=state
            )
        except InvalidStateError as e:
            logger.warning(
                f"Invalid OAuth state",
                extra={"platform": platform, "state": state[:8], "error": str(e)}
            )
            raise HTTPException(status_code=400, detail="Invalid or expired authorization state")
        except InvalidTokenError as e:
            logger.error(
                f"Token exchange failed",
                extra={"platform": platform, "error": str(e)},
                exc_info=True
            )
            raise HTTPException(status_code=502, detail=f"Failed to obtain access token: {str(e)}")

        logger.info(
            f"OAuth authorization completed",
            extra={
                "platform": platform,
                "user_id": token.user_id
            }
        )

        # Redirect to frontend with success
        # In production, this would redirect to your frontend app
        frontend_url = f"http://localhost:3000/settings/credentials?platform={platform}&status=success"
        return RedirectResponse(url=frontend_url, status_code=302)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"OAuth callback failed",
            extra={"platform": platform, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Authorization callback failed: {str(e)}")


@router.get("/{platform}/token")
async def get_token(
    platform: str,
    user_id: str = Query(..., description="User identifier"),
    oauth_service: OAuthService = Depends(get_oauth_service)
):
    """
    Get OAuth token for user

    Returns the current access token, automatically refreshing if needed.
    """
    try:
        # Validate platform
        try:
            oauth_platform = OAuthPlatform(platform.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

        # Get token (with auto-refresh)
        token = await oauth_service.get_token(
            platform=oauth_platform,
            user_id=user_id,
            auto_refresh=True
        )

        if not token:
            raise HTTPException(
                status_code=404,
                detail=f"No token found for {platform}. Please authorize first."
            )

        if not token.is_valid():
            raise HTTPException(
                status_code=401,
                detail=f"Token expired and refresh failed. Please re-authorize."
            )

        # Return token info (DO NOT expose refresh_token in production)
        return {
            "platform": token.platform.value,
            "user_id": token.user_id,
            "access_token": token.access_token[:20] + "...",  # Truncated for security
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "scope": token.scope,
            "token_type": token.token_type,
            "is_valid": token.is_valid(),
            "should_refresh": token.should_refresh()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get token",
            extra={"platform": platform, "user_id": user_id, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to retrieve token: {str(e)}")


@router.post("/{platform}/refresh")
async def refresh_token(
    platform: str,
    user_id: str = Query(..., description="User identifier"),
    oauth_service: OAuthService = Depends(get_oauth_service)
):
    """
    Manually refresh OAuth token

    Useful for testing or forcing a token refresh.
    """
    try:
        # Validate platform
        try:
            oauth_platform = OAuthPlatform(platform.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

        # Refresh token
        try:
            token = await oauth_service.refresh_token(
                platform=oauth_platform,
                user_id=user_id
            )
        except InvalidTokenError as e:
            raise HTTPException(status_code=400, detail=str(e))

        logger.info(
            f"Token refreshed manually",
            extra={"platform": platform, "user_id": user_id}
        )

        return {
            "platform": token.platform.value,
            "user_id": token.user_id,
            "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            "refreshed_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to refresh token",
            extra={"platform": platform, "user_id": user_id, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to refresh token: {str(e)}")


@router.delete("/{platform}/revoke")
async def revoke_token(
    platform: str,
    user_id: str = Query(..., description="User identifier"),
    oauth_service: OAuthService = Depends(get_oauth_service)
):
    """
    Revoke OAuth token

    Deletes the stored token. User will need to re-authorize.
    """
    try:
        # Validate platform
        try:
            oauth_platform = OAuthPlatform(platform.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

        # Revoke token
        revoked = await oauth_service.revoke_token(
            platform=oauth_platform,
            user_id=user_id
        )

        if not revoked:
            raise HTTPException(status_code=404, detail="Token not found")

        logger.info(
            f"Token revoked",
            extra={"platform": platform, "user_id": user_id}
        )

        return {
            "platform": platform,
            "user_id": user_id,
            "status": "revoked",
            "revoked_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to revoke token",
            extra={"platform": platform, "user_id": user_id, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to revoke token: {str(e)}")
