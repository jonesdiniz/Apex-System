"""
APEX System - MongoDB Database Client
Replaces Google Cloud Firestore with local MongoDB
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import PyMongoError
from common.logging import get_logger
from common.exceptions import DatabaseError
from .config import get_settings

logger = get_logger(__name__)


class MongoDB:
    """
    MongoDB client wrapper with connection pooling

    Provides async interface to MongoDB, replacing Firestore functionality
    """

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self._connected = False
        self.settings = get_settings()

    async def connect(self) -> None:
        """Connect to MongoDB"""
        if self._connected:
            logger.warning("MongoDB already connected")
            return

        try:
            self.client = AsyncIOMotorClient(
                self.settings.mongodb_url,
                minPoolSize=self.settings.mongodb_min_pool_size,
                maxPoolSize=self.settings.mongodb_max_pool_size,
                serverSelectionTimeoutMS=5000,
            )

            # Test connection
            await self.client.admin.command('ping')

            self.db = self.client[self.settings.mongodb_database]
            self._connected = True

            logger.info(
                f"Connected to MongoDB",
                extra={
                    "database": self.settings.mongodb_database,
                    "url": self.settings.mongodb_url.split('@')[-1]  # Hide credentials
                }
            )

        except PyMongoError as e:
            logger.error(f"Failed to connect to MongoDB: {e}", exc_info=True)
            raise DatabaseError("connect", {"error": str(e)})

    async def disconnect(self) -> None:
        """Disconnect from MongoDB"""
        if not self._connected:
            return

        if self.client:
            self.client.close()
            self._connected = False
            logger.info("Disconnected from MongoDB")

    async def health_check(self) -> str:
        """
        Check MongoDB health

        Returns:
            Status string: "healthy", "unhealthy"
        """
        try:
            if not self._connected:
                return "disconnected"

            await self.client.admin.command('ping')
            return "healthy"

        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return "unhealthy"

    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        """
        Get a collection by name

        Args:
            name: Collection name

        Returns:
            Collection instance

        Raises:
            DatabaseError: If not connected
        """
        if not self._connected or not self.db:
            raise DatabaseError("get_collection", {"error": "Not connected to database"})

        return self.db[name]

    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """
        Insert a document

        Args:
            collection: Collection name
            document: Document to insert

        Returns:
            Inserted document ID

        Raises:
            DatabaseError: On insert failure
        """
        try:
            # Add timestamp if not present
            if "created_at" not in document:
                document["created_at"] = datetime.utcnow()

            result = await self.get_collection(collection).insert_one(document)
            return str(result.inserted_id)

        except PyMongoError as e:
            logger.error(f"Insert failed: {e}", exc_info=True)
            raise DatabaseError("insert_one", {"collection": collection, "error": str(e)})

    async def find_one(
        self,
        collection: str,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find a single document

        Args:
            collection: Collection name
            query: Query filter
            projection: Fields to return

        Returns:
            Document or None if not found
        """
        try:
            return await self.get_collection(collection).find_one(query, projection)

        except PyMongoError as e:
            logger.error(f"Find one failed: {e}", exc_info=True)
            raise DatabaseError("find_one", {"collection": collection, "error": str(e)})

    async def find_many(
        self,
        collection: str,
        query: Dict[str, Any] = None,
        projection: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        skip: int = 0,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents

        Args:
            collection: Collection name
            query: Query filter (default: all documents)
            projection: Fields to return
            limit: Maximum number of documents
            skip: Number of documents to skip
            sort: Sort order [(field, direction), ...]

        Returns:
            List of documents
        """
        try:
            query = query or {}
            cursor = self.get_collection(collection).find(query, projection)

            if sort:
                cursor = cursor.sort(sort)

            cursor = cursor.skip(skip).limit(limit)

            return await cursor.to_list(length=limit)

        except PyMongoError as e:
            logger.error(f"Find many failed: {e}", exc_info=True)
            raise DatabaseError("find_many", {"collection": collection, "error": str(e)})

    async def update_one(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ) -> bool:
        """
        Update a single document

        Args:
            collection: Collection name
            query: Query filter
            update: Update operations
            upsert: Create if not exists

        Returns:
            True if document was modified
        """
        try:
            # Add updated timestamp
            if "$set" in update:
                update["$set"]["updated_at"] = datetime.utcnow()
            else:
                update["$set"] = {"updated_at": datetime.utcnow()}

            result = await self.get_collection(collection).update_one(
                query, update, upsert=upsert
            )

            return result.modified_count > 0 or (upsert and result.upserted_id is not None)

        except PyMongoError as e:
            logger.error(f"Update one failed: {e}", exc_info=True)
            raise DatabaseError("update_one", {"collection": collection, "error": str(e)})

    async def delete_one(self, collection: str, query: Dict[str, Any]) -> bool:
        """
        Delete a single document

        Args:
            collection: Collection name
            query: Query filter

        Returns:
            True if document was deleted
        """
        try:
            result = await self.get_collection(collection).delete_one(query)
            return result.deleted_count > 0

        except PyMongoError as e:
            logger.error(f"Delete one failed: {e}", exc_info=True)
            raise DatabaseError("delete_one", {"collection": collection, "error": str(e)})

    async def count_documents(
        self,
        collection: str,
        query: Dict[str, Any] = None
    ) -> int:
        """
        Count documents matching query

        Args:
            collection: Collection name
            query: Query filter (default: all documents)

        Returns:
            Document count
        """
        try:
            query = query or {}
            return await self.get_collection(collection).count_documents(query)

        except PyMongoError as e:
            logger.error(f"Count failed: {e}", exc_info=True)
            raise DatabaseError("count_documents", {"collection": collection, "error": str(e)})


# Global database instance
_db_instance: Optional[MongoDB] = None


async def get_database() -> MongoDB:
    """
    Get or create global database instance

    Returns:
        MongoDB instance
    """
    global _db_instance

    if _db_instance is None:
        _db_instance = MongoDB()
        await _db_instance.connect()

    return _db_instance


async def close_database() -> None:
    """Close global database instance"""
    global _db_instance

    if _db_instance:
        await _db_instance.disconnect()
        _db_instance = None
