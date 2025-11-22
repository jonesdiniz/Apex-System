"""
API Gateway - OAuth Provider Configurations
Platform-specific OAuth 2.0 configurations
"""

from dataclasses import dataclass
from typing import Dict
from ..domain.models import OAuthPlatform
from infrastructure.config import get_settings


@dataclass
class OAuthProviderConfig:
    """OAuth provider configuration"""
    platform: OAuthPlatform
    client_id: str
    client_secret: str
    auth_url: str
    token_url: str
    scope: str
    redirect_uri: str


class OAuthConfigProvider:
    """
    Provides OAuth configurations for all supported platforms

    Configuration is loaded from environment variables (local execution)
    """

    def __init__(self):
        self.settings = get_settings()
        self._configs: Dict[OAuthPlatform, OAuthProviderConfig] = {}
        self._initialize_configs()

    def _initialize_configs(self) -> None:
        """Initialize OAuth configurations for all platforms"""

        # Base URL for redirects
        base_url = getattr(self.settings, 'app_base_url', 'http://localhost:8000')

        # Google Ads + Analytics
        if hasattr(self.settings, 'google_client_id') and self.settings.google_client_id:
            self._configs[OAuthPlatform.GOOGLE] = OAuthProviderConfig(
                platform=OAuthPlatform.GOOGLE,
                client_id=self.settings.google_client_id,
                client_secret=self.settings.google_client_secret,
                auth_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                scope="https://www.googleapis.com/auth/adwords https://www.googleapis.com/auth/analytics.readonly",
                redirect_uri=f"{base_url}/auth/google/callback"
            )

        # LinkedIn Ads
        if hasattr(self.settings, 'linkedin_client_id') and self.settings.linkedin_client_id:
            self._configs[OAuthPlatform.LINKEDIN] = OAuthProviderConfig(
                platform=OAuthPlatform.LINKEDIN,
                client_id=self.settings.linkedin_client_id,
                client_secret=self.settings.linkedin_client_secret,
                auth_url="https://www.linkedin.com/oauth/v2/authorization",
                token_url="https://www.linkedin.com/oauth/v2/accessToken",
                scope="r_ads,r_ads_reporting,rw_ads",
                redirect_uri=f"{base_url}/auth/linkedin/callback"
            )

        # Meta/Facebook Business
        if hasattr(self.settings, 'meta_client_id') and self.settings.meta_client_id:
            self._configs[OAuthPlatform.META] = OAuthProviderConfig(
                platform=OAuthPlatform.META,
                client_id=self.settings.meta_client_id,
                client_secret=self.settings.meta_client_secret,
                auth_url="https://www.facebook.com/v18.0/dialog/oauth",
                token_url="https://graph.facebook.com/v18.0/oauth/access_token",
                scope="ads_management,ads_read,business_management",
                redirect_uri=f"{base_url}/auth/meta/callback"
            )

        # Twitter/X API v2 (PKCE)
        if hasattr(self.settings, 'twitter_client_id') and self.settings.twitter_client_id:
            self._configs[OAuthPlatform.TWITTER] = OAuthProviderConfig(
                platform=OAuthPlatform.TWITTER,
                client_id=self.settings.twitter_client_id,
                client_secret=self.settings.twitter_client_secret,
                auth_url="https://twitter.com/i/oauth2/authorize",
                token_url="https://api.twitter.com/2/oauth2/token",
                scope="tweet.read users.read offline.access",
                redirect_uri=f"{base_url}/auth/twitter/callback"
            )

        # TikTok Creator
        if hasattr(self.settings, 'tiktok_client_id') and self.settings.tiktok_client_id:
            self._configs[OAuthPlatform.TIKTOK] = OAuthProviderConfig(
                platform=OAuthPlatform.TIKTOK,
                client_id=self.settings.tiktok_client_id,
                client_secret=self.settings.tiktok_client_secret,
                auth_url="https://www.tiktok.com/auth/authorize/",
                token_url="https://open-api.tiktok.com/oauth/access_token/",
                scope="user.info.basic,video.list",
                redirect_uri=f"{base_url}/auth/tiktok/callback"
            )

    async def get_config(self, platform: OAuthPlatform) -> OAuthProviderConfig:
        """
        Get OAuth configuration for platform

        Args:
            platform: OAuth platform

        Returns:
            OAuthProviderConfig

        Raises:
            ValueError: If platform not configured
        """
        if platform not in self._configs:
            raise ValueError(
                f"OAuth not configured for {platform.value}. "
                f"Please set {platform.value.upper()}_CLIENT_ID and "
                f"{platform.value.upper()}_CLIENT_SECRET environment variables."
            )

        return self._configs[platform]

    def get_configured_platforms(self) -> list[OAuthPlatform]:
        """Get list of configured platforms"""
        return list(self._configs.keys())
