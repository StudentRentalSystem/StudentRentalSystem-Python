from src.frontend.users_database import user_collection
from datetime import datetime

class UserService:
    def get_or_create_user(self, email, name):
        """
        Retrieve a user by email, or create a new one if they don't exist.
        """
        user = user_collection.find_one({"email": email})
        if not user:
            user = {
                "email": email,
                "name": name,
                "collections": [],
                "searchHistory": {}
            }
            user_collection.insert_one(user)
        return user

    def add_collection(self, email, post_id):
        """
        Add a post ID to the user's collection.
        """
        user = user_collection.find_one({"email": email})
        if user and post_id not in user.get("collections", []):
            user_collection.update_one(
                {"email": email},
                {"$push": {"collections": post_id}}
            )
            return True
        return False

    def remove_collection(self, email, post_id):
        """
        Remove a post ID from the user's collection.
        """
        user_collection.update_one(
            {"email": email},
            {"$pull": {"collections": post_id}}
        )
        return True

    def get_collections(self, email):
        """
        Get the list of collected post IDs for a user.
        """
        user = user_collection.find_one({"email": email})
        return user.get("collections", []) if user else []

    def add_history(self, email, keyword):
        """
        Record a search keyword with a timestamp.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Storing history in a map/dict structure as per original schema
        key = f"searchHistory.{timestamp}"
        user_collection.update_one(
            {"email": email},
            {"$set": {key: keyword}}
        )

    def get_history(self, email):
        """
        Retrieve search history sorted by timestamp (newest first).
        """
        user = user_collection.find_one({"email": email})
        if not user or "searchHistory" not in user:
            return {}
        
        history = user["searchHistory"]
        if history is None:
            return {}
        # Sort items by key (timestamp) in descending order
        return dict(sorted(history.items(), key=lambda item: item[0], reverse=True))

    def clean_history(self, email):
        user_collection.update_one(
            {'email': email},
            {'$set': {'searchHistory': {}}}
        )