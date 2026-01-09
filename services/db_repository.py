import logging
import uuid
from datetime import datetime, timezone
from typing import List
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from config import Config
from models import Annotation
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

COLLECTION_NAME = "translation_annotations"


class MongoDBRepository:
    """MongoDB repository for storing translation annotations"""

    _instance = None
    _client = None
    _db = None
    _collection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBRepository, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        try:
            self._client = MongoClient(
                Config.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            self._client.admin.command('ping')
            self._db = self._client[Config.MONGODB_DATABASE]
            self._collection = self._db[COLLECTION_NAME]
            logger.info(f"Successfully connected to MongoDB database: {Config.MONGODB_DATABASE}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise

    @property
    def client(self):
        return self._client

    def insert_annotation(self, original_text: str, translated_text: str, annotations: List[Annotation]):
        """
        Insert a translation annotation record into the database.

        Args:
            original_text: The source text that was translated
            translated_text: The resulting translated text
            annotations: List of Annotation objects marking error spans

        Returns:
            dict: Dictionary containing 'id' (MongoDB document ID) and 'private_id' (UUID)
        """
        if self._collection is None:
            raise RuntimeError("Database not initialized")

        try:
            private_id = str(uuid.uuid4())
            document = {
                "private_id": private_id,
                "original_text": original_text,
                "translated_text": translated_text,
                "annotations": [ann.to_dict() for ann in annotations],
                "created_at": datetime.now(timezone.utc)
            }

            result = self._collection.insert_one(document)
            logger.info(f"Inserted annotation document with ID: {result.inserted_id}")
            return {
                "id": str(result.inserted_id),
                "private_id": private_id
            }

        except OperationFailure as e:
            logger.error(f"Failed to insert annotation: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error inserting annotation: {e}")
            raise

    def get_annotation_by_id(self, document_id: str):
        """
        Retrieve an annotation document by its ID.

        Args:
            document_id: The MongoDB document ID

        Returns:
            dict: The annotation document or None if not found
        """
        if self._collection is None:
            raise RuntimeError("Database not initialized")

        try:
            return self._collection.find_one({"_id": ObjectId(document_id)})
        except Exception as e:
            logger.error(f"Failed to retrieve annotation: {e}")
            raise

    def get_all_annotations(self, limit: int = 100, skip: int = 0):
        """
        Retrieve all annotation documents with pagination.

        Args:
            limit: Maximum number of documents to return
            skip: Number of documents to skip

        Returns:
            list: List of annotation documents
        """
        if self._collection is None:
            raise RuntimeError("Database not initialized")

        try:
            cursor = self._collection.find().skip(skip).limit(limit).sort("created_at", -1)
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to retrieve annotations: {e}")
            raise

    def update_annotation(self, document_id: str, private_id: str,
                         original_text: str = None, translated_text: str = None,
                         annotations: List[Annotation] = None):
        """
        Update an annotation document. Requires both document_id and private_id to match.

        Args:
            document_id: The MongoDB document ID
            private_id: The private UUID for authorization
            original_text: Optional new original text
            translated_text: Optional new translated text
            annotations: Optional new list of Annotation objects

        Returns:
            dict: Dictionary containing 'matched' (bool) and 'modified' (bool)
        """
        if self._collection is None:
            raise RuntimeError("Database not initialized")

        try:
            update_fields = {}
            if original_text is not None:
                update_fields["original_text"] = original_text
            if translated_text is not None:
                update_fields["translated_text"] = translated_text
            if annotations is not None:
                update_fields["annotations"] = [ann.to_dict() for ann in annotations]

            if not update_fields:
                logger.warning("No fields provided for update")
                return {"matched": False, "modified": False}

            query = {
                "_id": ObjectId(document_id),
                "private_id": private_id
            }

            result = self._collection.update_one(
                query,
                {"$set": update_fields}
            )

            logger.info(f"Update annotation {document_id}: matched={result.matched_count}, modified={result.modified_count}")

            return {
                "matched": result.matched_count > 0,
                "modified": result.modified_count > 0
            }

        except Exception as e:
            logger.error(f"Failed to update annotation: {e}")
            raise


def get_db_repository():
    """Get the singleton MongoDB repository instance"""
    return MongoDBRepository()
