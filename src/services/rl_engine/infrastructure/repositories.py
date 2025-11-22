"""
RL Engine - Infrastructure Layer - Repositories
MongoDB persistence replacing Google Cloud Firestore
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from infrastructure.database import MongoDB


logger = logging.getLogger(__name__)


class MongoRLRepository:
    """
    MongoDB Repository for RL Engine

    Replaces Google Cloud Firestore with MongoDB for local execution
    Stores: strategies, Q-tables, experiences
    """

    def __init__(self, db: MongoDB):
        """
        Initialize MongoDB repository

        Args:
            db: MongoDB client instance
        """
        self.db = db
        self.strategies_collection = "rl_strategies"
        self.q_tables_collection = "rl_q_tables"
        self.experiences_collection = "rl_experiences"
        self.history_collection = "rl_experience_history"

    async def save_strategies(self, strategies: Dict[str, Any]) -> bool:
        """
        Save learned strategies to MongoDB

        Args:
            strategies: Dict of context -> strategy data

        Returns:
            Success status
        """
        try:
            # Clear existing strategies
            await self.db.delete_many(
                collection=self.strategies_collection,
                query={}
            )

            # Insert all strategies
            if strategies:
                documents = []
                for context, strategy_data in strategies.items():
                    doc = {
                        "_id": context,
                        "context": context,
                        **strategy_data,
                        "saved_at": datetime.utcnow()
                    }
                    documents.append(doc)

                await self.db.insert_many(
                    collection=self.strategies_collection,
                    documents=documents
                )

            logger.info(f"Saved {len(strategies)} strategies to MongoDB")
            return True

        except Exception as e:
            logger.error(f"Error saving strategies to MongoDB: {e}", exc_info=True)
            return False

    async def load_strategies(self) -> Dict[str, Any]:
        """
        Load learned strategies from MongoDB

        Returns:
            Dict of context -> strategy data
        """
        try:
            documents = await self.db.find(
                collection=self.strategies_collection,
                query={}
            )

            strategies = {}
            for doc in documents:
                context = doc.pop("_id")
                doc.pop("saved_at", None)  # Remove metadata
                strategies[context] = doc

            logger.info(f"Loaded {len(strategies)} strategies from MongoDB")
            return strategies

        except Exception as e:
            logger.error(f"Error loading strategies from MongoDB: {e}", exc_info=True)
            return {}

    async def save_q_table(self, context: str, q_values: Dict[str, float]) -> bool:
        """
        Save Q-table values for a context

        Args:
            context: Strategic context
            q_values: Dict of action -> Q-value

        Returns:
            Success status
        """
        try:
            document = {
                "_id": context,
                "context": context,
                "q_values": q_values,
                "updated_at": datetime.utcnow()
            }

            await self.db.update_one(
                collection=self.q_tables_collection,
                query={"_id": context},
                update={"$set": document},
                upsert=True
            )

            logger.debug(f"Saved Q-table for context: {context}")
            return True

        except Exception as e:
            logger.error(f"Error saving Q-table: {e}", exc_info=True)
            return False

    async def load_q_table(self) -> Dict[str, Dict[str, float]]:
        """
        Load complete Q-table from MongoDB

        Returns:
            Dict of context -> action -> Q-value
        """
        try:
            documents = await self.db.find(
                collection=self.q_tables_collection,
                query={}
            )

            q_table = {}
            for doc in documents:
                context = doc["context"]
                q_values = doc.get("q_values", {})
                q_table[context] = q_values

            logger.info(f"Loaded Q-table with {len(q_table)} contexts from MongoDB")
            return q_table

        except Exception as e:
            logger.error(f"Error loading Q-table from MongoDB: {e}", exc_info=True)
            return {}

    async def save_experience(self, experience_data: Dict[str, Any]) -> bool:
        """
        Save a single experience to MongoDB (active buffer)

        Args:
            experience_data: Experience data

        Returns:
            Success status
        """
        try:
            document = {
                "_id": experience_data["id"],
                **experience_data,
                "saved_at": datetime.utcnow()
            }

            await self.db.insert_one(
                collection=self.experiences_collection,
                document=document
            )

            logger.debug(f"Saved experience: {experience_data['id']}")
            return True

        except Exception as e:
            logger.error(f"Error saving experience: {e}", exc_info=True)
            return False

    async def load_experiences(self) -> List[Dict[str, Any]]:
        """
        Load all active experiences from MongoDB

        Returns:
            List of experiences
        """
        try:
            documents = await self.db.find(
                collection=self.experiences_collection,
                query={}
            )

            experiences = []
            for doc in documents:
                doc.pop("saved_at", None)
                experiences.append(doc)

            logger.info(f"Loaded {len(experiences)} experiences from MongoDB")
            return experiences

        except Exception as e:
            logger.error(f"Error loading experiences: {e}", exc_info=True)
            return []

    async def delete_experience(self, experience_id: str) -> bool:
        """
        Delete an experience from active buffer

        Args:
            experience_id: Experience ID

        Returns:
            Success status
        """
        try:
            await self.db.delete_one(
                collection=self.experiences_collection,
                query={"_id": experience_id}
            )

            logger.debug(f"Deleted experience: {experience_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting experience: {e}", exc_info=True)
            return False

    async def save_to_history(self, experiences: List[Dict[str, Any]]) -> bool:
        """
        Save processed experiences to history collection

        Args:
            experiences: List of processed experiences

        Returns:
            Success status
        """
        try:
            if not experiences:
                return True

            documents = []
            for exp in experiences:
                doc = {
                    **exp,
                    "moved_to_history_at": datetime.utcnow()
                }
                documents.append(doc)

            await self.db.insert_many(
                collection=self.history_collection,
                documents=documents
            )

            logger.info(f"Saved {len(experiences)} experiences to history")
            return True

        except Exception as e:
            logger.error(f"Error saving to history: {e}", exc_info=True)
            return False

    async def load_history(
        self,
        limit: Optional[int] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Load experience history from MongoDB

        Args:
            limit: Maximum number of experiences to load
            since: Load experiences since this timestamp

        Returns:
            List of historical experiences
        """
        try:
            query = {}
            if since:
                query["timestamp"] = {"$gte": since}

            documents = await self.db.find(
                collection=self.history_collection,
                query=query,
                limit=limit,
                sort=[("timestamp", -1)]  # Most recent first
            )

            history = []
            for doc in documents:
                doc.pop("moved_to_history_at", None)
                history.append(doc)

            logger.info(f"Loaded {len(history)} experiences from history")
            return history

        except Exception as e:
            logger.error(f"Error loading history: {e}", exc_info=True)
            return []

    async def cleanup_old_history(self, before: datetime) -> int:
        """
        Delete old experiences from history

        Args:
            before: Delete experiences older than this timestamp

        Returns:
            Number of deleted experiences
        """
        try:
            result = await self.db.delete_many(
                collection=self.history_collection,
                query={"timestamp": {"$lt": before}}
            )

            deleted_count = result.get("deleted_count", 0)
            logger.info(f"Cleaned up {deleted_count} old experiences from history")
            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up history: {e}", exc_info=True)
            return 0

    async def get_strategy_by_context(self, context: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific strategy by context

        Args:
            context: Strategic context

        Returns:
            Strategy data or None
        """
        try:
            document = await self.db.find_one(
                collection=self.strategies_collection,
                query={"_id": context}
            )

            if document:
                document.pop("saved_at", None)
                return document

            return None

        except Exception as e:
            logger.error(f"Error getting strategy: {e}", exc_info=True)
            return None

    async def count_experiences(self) -> int:
        """
        Count active experiences

        Returns:
            Number of experiences
        """
        try:
            count = await self.db.count(
                collection=self.experiences_collection,
                query={}
            )
            return count

        except Exception as e:
            logger.error(f"Error counting experiences: {e}", exc_info=True)
            return 0

    async def count_history(self) -> int:
        """
        Count historical experiences

        Returns:
            Number of historical experiences
        """
        try:
            count = await self.db.count(
                collection=self.history_collection,
                query={}
            )
            return count

        except Exception as e:
            logger.error(f"Error counting history: {e}", exc_info=True)
            return 0

    async def health_check(self) -> bool:
        """
        Check if MongoDB connection is healthy

        Returns:
            Health status
        """
        try:
            await self.db.find_one(
                collection=self.strategies_collection,
                query={}
            )
            return True

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
