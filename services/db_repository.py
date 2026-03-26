import logging
import uuid
from datetime import datetime, timezone
from typing import List
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from config import Config
from models import Annotation
from models.user import User
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)

ANNOTATIONS_COLLECTION = "translation_annotations"
USERS_COLLECTION = "users"
ERROR_LEVELS_COLLECTION = "error_levels"

DEFAULT_ERROR_LEVELS = [
    {"name": "minor", "color": "#007bff", "order": 1},
    {"name": "major", "color": "#a13927", "order": 2}
]


class MongoDBRepository:

    _instance = None
    _client = None
    _db = None
    _annotations_collection = None
    _users_collection = None
    _error_levels_collection = None

    def __new__(cls):
        if cls._instance is None:
            instance = super(MongoDBRepository, cls).__new__(cls)
            instance._initialize()
            cls._instance = instance
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

            self._annotations_collection = self._db[ANNOTATIONS_COLLECTION]
            self._users_collection = self._db[USERS_COLLECTION]
            self._error_levels_collection = self._db[ERROR_LEVELS_COLLECTION]

            self._users_collection.create_index("username", unique=True)
            self._error_levels_collection.create_index("name", unique=True)
            self._error_levels_collection.create_index("order")

            # Seed default error levels if collection is empty
            self._seed_default_error_levels()

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

    def insert_annotation(self, original_text: str, translated_text: str, annotations: List[Annotation], stars: int, feedback: str, input_language: str, output_language: str, email: str = None):
        try:
            private_id = str(uuid.uuid4())
            document = {
                "private_id": private_id,
                "original_text": original_text,
                "translated_text": translated_text,
                "annotations": [ann.to_dict() for ann in annotations],
                "stars": stars,
                "feedback": feedback,
                "created_at": datetime.now(timezone.utc),
                "input_language": input_language,
                "output_language": output_language,
                "email": email
            }

            result = self._annotations_collection.insert_one(document)
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
        try:
            return self._annotations_collection.find_one({"_id": ObjectId(document_id)})
        except Exception as e:
            logger.error(f"Failed to retrieve annotation: {e}")
            raise

    def get_all_annotations(self, limit: int = 100, skip: int = 0):

        try:
            cursor = self._annotations_collection.find().skip(skip).limit(limit).sort("created_at", -1)
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to retrieve annotations: {e}")
            raise

    def update_annotation(self, document_id: str, private_id: str,
                         original_text: str = None, translated_text: str = None,
                         annotations: List[Annotation] = None,
                         stars: int = None, feedback: str = None):
        try:
            update_fields = {}
            if original_text is not None:
                update_fields["original_text"] = original_text
            if translated_text is not None:
                update_fields["translated_text"] = translated_text
            if annotations is not None:
                update_fields["annotations"] = [ann.to_dict() for ann in annotations]
            if stars is not None:
                update_fields["stars"] = stars
            if feedback is not None:
                update_fields["feedback"] = feedback

            if not update_fields:
                logger.warning("No fields provided for update")
                return {"matched": False, "modified": False}

            query = {
                "_id": ObjectId(document_id),
                "private_id": private_id
            }

            result = self._annotations_collection.update_one(
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

    def create_user(self, username: str, password_hash: str, email: str = None):
        try:
            document = {
                "username": username,
                "password_hash": password_hash,
                "email": email,
                "created_at": datetime.now(timezone.utc)
            }

            result = self._users_collection.insert_one(document)
            logger.info(f"Created user with ID: {result.inserted_id}, username: {username}")
            return {
                "id": str(result.inserted_id),
                "username": username
            }

        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise

    # for Flask-Login
    def get_user_by_id(self, user_id: str):
        try:
            document = self._users_collection.find_one({"_id": ObjectId(user_id)})
            if document is None:
                return None
            
            return User(user_id=str(document["_id"]), username=document["username"])
        except Exception as e:
            logger.error(f"Failed to retrieve user by ID: {e}")
            return None

    # for app login
    def get_user_by_username(self, username: str):
        try:
            return self._users_collection.find_one({"username": username})
        except Exception as e:
            logger.error(f"Failed to retrieve user by username: {e}")
            return None

    # Error Levels Methods
    def _seed_default_error_levels(self):
        """Seed default error levels if the collection is empty"""
        try:
            if self._error_levels_collection.count_documents({}) == 0:
                self._error_levels_collection.insert_many(DEFAULT_ERROR_LEVELS)
                logger.info("Seeded default error levels")
        except Exception as e:
            logger.error(f"Failed to seed default error levels: {e}")

    def get_all_error_levels(self):
        """Get all error levels sorted by order"""
        try:
            cursor = self._error_levels_collection.find().sort("order", 1)
            levels = []
            for level in cursor:
                level["_id"] = str(level["_id"])
                levels.append(level)
            return levels
        except Exception as e:
            logger.error(f"Failed to retrieve error levels: {e}")
            raise

    def get_error_level_by_name(self, name: str):
        """Get a single error level by name"""
        try:
            level = self._error_levels_collection.find_one({"name": name})
            if level:
                level["_id"] = str(level["_id"])
            return level
        except Exception as e:
            logger.error(f"Failed to retrieve error level: {e}")
            raise

    def create_error_level(self, name: str, color: str, order: int):
        """Create a new error level"""
        try:
            document = {
                "name": name,
                "color": color,
                "order": order
            }
            result = self._error_levels_collection.insert_one(document)
            logger.info(f"Created error level: {name}")
            return {
                "id": str(result.inserted_id),
                "name": name,
                "color": color,
                "order": order
            }
        except Exception as e:
            logger.error(f"Failed to create error level: {e}")
            raise

    def update_error_level(self, level_id: str, name: str = None, color: str = None, order: int = None):
        """Update an existing error level"""
        try:
            update_fields = {}
            if name is not None:
                update_fields["name"] = name
            if color is not None:
                update_fields["color"] = color
            if order is not None:
                update_fields["order"] = order

            if not update_fields:
                return {"matched": False, "modified": False}

            result = self._error_levels_collection.update_one(
                {"_id": ObjectId(level_id)},
                {"$set": update_fields}
            )

            logger.info(f"Updated error level {level_id}: matched={result.matched_count}, modified={result.modified_count}")
            return {
                "matched": result.matched_count > 0,
                "modified": result.modified_count > 0
            }
        except Exception as e:
            logger.error(f"Failed to update error level: {e}")
            raise

    def delete_error_level(self, level_id: str):
        """Delete an error level"""
        try:
            result = self._error_levels_collection.delete_one({"_id": ObjectId(level_id)})
            logger.info(f"Deleted error level {level_id}: deleted={result.deleted_count}")
            return {"deleted": result.deleted_count > 0}
        except Exception as e:
            logger.error(f"Failed to delete error level: {e}")
            raise

    def get_error_level_names(self):
        """Get list of valid error level names"""
        try:
            levels = self.get_all_error_levels()
            return [level["name"] for level in levels]
        except Exception as e:
            logger.error(f"Failed to get error level names: {e}")
            return []


def get_db_repository():
    return MongoDBRepository()
