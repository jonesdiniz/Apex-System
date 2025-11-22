"""
API Gateway - Infrastructure Repositories
MongoDB implementation of domain repositories
"""

from typing import Optional
from datetime import datetime, timedelta

from infrastructure.database import MongoDB
from ..domain.models import OAuthToken, OAuthState, OAuthPlatform
from common.logging import get_logger

logger = get_logger(__name__)


class MongoOAuthRepository:
    """
    MongoDB implementation of OAuth repository

    Replaces Google Cloud Firestore with MongoDB for local execution
    """

    def __init__(self, db: MongoDB):
        self.db = db
        self.tokens_collection = "oauth_tokens"
        self.states_collection = "oauth_states"

    # =========================================================================
    # TOKEN PERSISTENCE
    # =========================================================================

    async def save_token(self, token: OAuthToken) -> bool:
        """
        Save OAuth token to MongoDB

        Storage format:
        {
            "_id": "user_123:google",
            "platform": "google",
            "user_id": "user_123",
            "access_token": "ya29.xxx",
            "refresh_token": "1//xxx",
            "expires_at": ISODate("2025-11-23T10:00:00Z"),
            "scope": "...",
            "token_type": "Bearer",
            "created_at": ISODate("2025-11-22T09:00:00Z"),
            "updated_at": ISODate("2025-11-22T09:30:00Z")
        }
        """
        try:
            document_id = f"{token.user_id}:{token.platform.value}"

            token_doc = {
                "_id": document_id,
                "platform": token.platform.value,
                "user_id": token.user_id,
                "access_token": token.access_token,
                "refresh_token": token.refresh_token,
                "expires_at": token.expires_at,
                "scope": token.scope,
                "token_type": token.token_type,
                "created_at": token.created_at,
                "updated_at": datetime.utcnow()
            }

            # Upsert (insert or update)
            await self.db.update_one(
                collection=self.tokens_collection,
                query={"_id": document_id},
                update={"$set": token_doc},
                upsert=True
            )

            logger.info(
                f"OAuth token saved",
                extra={
                    "platform": token.platform.value,
                    "user_id": token.user_id
                }
            )

            return True

        except Exception as e:
            logger.error(
                f"Failed to save OAuth token",
                extra={"error": str(e)},
                exc_info=True
            )
            return False

    async def get_token(
        self,
        platform: OAuthPlatform,
        user_id: str
    ) -> Optional[OAuthToken]:
        """Get OAuth token from MongoDB"""
        try:
            document_id = f"{user_id}:{platform.value}"

            token_doc = await self.db.find_one(
                collection=self.tokens_collection,
                query={"_id": document_id}
            )

            if not token_doc:
                return None

            # Convert MongoDB document to domain model
            return OAuthToken(
                platform=OAuthPlatform(token_doc["platform"]),
                user_id=token_doc["user_id"],
                access_token=token_doc["access_token"],
                refresh_token=token_doc.get("refresh_token"),
                expires_at=token_doc.get("expires_at"),
                scope=token_doc.get("scope"),
                token_type=token_doc.get("token_type", "Bearer"),
                created_at=token_doc.get("created_at", datetime.utcnow())
            )

        except Exception as e:
            logger.error(
                f"Failed to get OAuth token",
                extra={
                    "platform": platform.value,
                    "user_id": user_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return None

    async def delete_token(
        self,
        platform: OAuthPlatform,
        user_id: str
    ) -> bool:
        """Delete OAuth token from MongoDB"""
        try:
            document_id = f"{user_id}:{platform.value}"

            deleted = await self.db.delete_one(
                collection=self.tokens_collection,
                query={"_id": document_id}
            )

            if deleted:
                logger.info(
                    f"OAuth token deleted",
                    extra={
                        "platform": platform.value,
                        "user_id": user_id
                    }
                )

            return deleted

        except Exception as e:
            logger.error(
                f"Failed to delete OAuth token",
                extra={"error": str(e)},
                exc_info=True
            )
            return False

    # =========================================================================
    # STATE PERSISTENCE
    # =========================================================================

    async def save_state(self, state: OAuthState) -> bool:
        """
        Save OAuth state to MongoDB

        States are temporary (10 min TTL) for CSRF protection
        """
        try:
            state_doc = {
                "_id": state.state_token,
                "platform": state.platform.value,
                "user_id": state.user_id,
                "code_verifier": state.code_verifier,  # For PKCE (Twitter)
                "redirect_uri": state.redirect_uri,
                "created_at": state.created_at,
                "expires_at": state.created_at + timedelta(minutes=10)
            }

            await self.db.update_one(
                collection=self.states_collection,
                query={"_id": state.state_token},
                update={"$set": state_doc},
                upsert=True
            )

            logger.debug(
                f"OAuth state saved",
                extra={
                    "state": state.state_token[:8],  # Log prefix only
                    "platform": state.platform.value
                }
            )

            return True

        except Exception as e:
            logger.error(
                f"Failed to save OAuth state",
                extra={"error": str(e)},
                exc_info=True
            )
            return False

    async def get_state(self, state_token: str) -> Optional[OAuthState]:
        """Get OAuth state from MongoDB"""
        try:
            state_doc = await self.db.find_one(
                collection=self.states_collection,
                query={"_id": state_token}
            )

            if not state_doc:
                return None

            # Check if expired
            if datetime.utcnow() > state_doc.get("expires_at", datetime.utcnow()):
                # Auto-cleanup expired state
                await self.delete_state(state_token)
                return None

            # Convert MongoDB document to domain model
            return OAuthState(
                state_token=state_doc["_id"],
                platform=OAuthPlatform(state_doc["platform"]),
                user_id=state_doc["user_id"],
                code_verifier=state_doc.get("code_verifier"),
                redirect_uri=state_doc.get("redirect_uri"),
                created_at=state_doc.get("created_at", datetime.utcnow())
            )

        except Exception as e:
            logger.error(
                f"Failed to get OAuth state",
                extra={"state": state_token[:8], "error": str(e)},
                exc_info=True
            )
            return None

    async def delete_state(self, state_token: str) -> bool:
        """Delete OAuth state from MongoDB"""
        try:
            deleted = await self.db.delete_one(
                collection=self.states_collection,
                query={"_id": state_token}
            )

            if deleted:
                logger.debug(
                    f"OAuth state deleted",
                    extra={"state": state_token[:8]}
                )

            return deleted

        except Exception as e:
            logger.error(
                f"Failed to delete OAuth state",
                extra={"error": str(e)},
                exc_info=True
            )
            return False

    async def cleanup_expired_states(self) -> int:
        """
        Cleanup expired OAuth states

        Returns:
            Number of states deleted
        """
        try:
            # Find and delete all expired states
            result = await self.db.get_collection(self.states_collection).delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })

            count = result.deleted_count

            if count > 0:
                logger.info(
                    f"Cleaned up expired OAuth states",
                    extra={"count": count}
                )

            return count

        except Exception as e:
            logger.error(
                f"Failed to cleanup expired states",
                extra={"error": str(e)},
                exc_info=True
            )
            return 0
