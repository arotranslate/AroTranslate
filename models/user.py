import logging
from flask_login import UserMixin
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)


class User(UserMixin):
    """User model for Flask-Login authentication"""

    def __init__(self, user_id, username, email=None):
        """
        Initialize a User instance.

        Args:
            user_id: MongoDB ObjectId as string
            username: Username for the user
            email: Optional email address
        """
        self.id = user_id
        self.username = username
        self.email = email

    @staticmethod
    def get(user_id):
        """
        Load user from database by ID.
        Required by Flask-Login's user_loader callback.

        Args:
            user_id: MongoDB ObjectId as string

        Returns:
            User instance or None if user not found
        """
        # Import here to avoid circular dependency
        from services.db_repository import get_db_repository

        try:
            db_repo = get_db_repository()
            user_data = db_repo.get_user_by_id(user_id)

            if user_data:
                return User(
                    user_id=str(user_data['_id']),
                    username=user_data['username'],
                    email=user_data.get('email')
                )
            return None
        except Exception as e:
            logger.error(f"Error loading user by ID {user_id}: {e}")
            return None

    @staticmethod
    def get_by_username(username):
        """
        Load user from database by username.
        Used for login verification.

        Args:
            username: Username to search for

        Returns:
            User instance or None if user not found
        """
        # Import here to avoid circular dependency
        from services.db_repository import get_db_repository

        try:
            db_repo = get_db_repository()
            user_data = db_repo.get_user_by_username(username)

            if user_data:
                return User(
                    user_id=str(user_data['_id']),
                    username=user_data['username'],
                    email=user_data.get('email')
                )
            return None
        except Exception as e:
            logger.error(f"Error loading user by username {username}: {e}")
            return None

    def get_id(self):
        """
        Return user ID as string.
        Required by Flask-Login for session management.

        Returns:
            User ID as string
        """
        return str(self.id)

    def __repr__(self):
        return f"<User {self.username}>"
