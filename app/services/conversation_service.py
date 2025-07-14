"""
Conversation Service - Manages conversation history for the Kisan AI assistant

This service is responsible for:
1. Storing and retrieving conversation history
2. Managing conversation context for more coherent interactions
3. Cleaning and limiting conversation history size
"""

import shelve
import logging
import os
import json
import time
from pathlib import Path
import threading

# Set up logging
logger = logging.getLogger(__name__)

class ConversationService:
    """Service for managing conversation history with improved reliability"""
    
    def __init__(self, db_path=None):
        """Initialize the conversation service with configurable database path"""
        # Default database path
        if db_path:
            self.db_path = db_path
        else:
            # Create a conversations directory if it doesn't exist
            current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
            conversations_dir = current_dir.parent.parent / "conversations_db"
            os.makedirs(conversations_dir, exist_ok=True)
            self.db_path = str(conversations_dir / "conversations")
        
        # Thread lock for database access
        self._lock = threading.RLock()
        
        # Maximum conversation history length
        self.max_history_length = 20  # 10 exchanges (user + assistant)
        
        # Maximum conversation age in seconds (48 hours)
        self.max_conversation_age = 172800
        
        logger.info(f"Conversation service initialized with database: {self.db_path}")
        
        # Perform initial cleanup of old conversations
        self.cleanup_old_conversations()
    
    def get_conversation_history(self, user_id):
        """
        Get conversation history for a user
        
        Args:
            user_id (str): Unique identifier for the user
            
        Returns:
            list: Conversation history messages
        """
        with self._lock:
            try:
                with shelve.open(self.db_path) as shelf:
                    # Get the conversation record
                    conversation = shelf.get(user_id, {})
                    
                    # If we have a timestamp, check age
                    if 'timestamp' in conversation:
                        age = time.time() - conversation['timestamp']
                        # If too old, return empty and remove
                        if age > self.max_conversation_age:
                            if user_id in shelf:
                                del shelf[user_id]
                            return []
                    
                    # Return the messages
                    return conversation.get('messages', [])
            except Exception as e:
                logger.error(f"Error getting conversation history for {user_id}: {str(e)}")
                return []
    
    def save_conversation_history(self, user_id, history):
        """
        Save conversation history for a user
        
        Args:
            user_id (str): Unique identifier for the user
            history (list): Conversation history messages
        """
        with self._lock:
            try:
                # Validate and clean the history
                if not isinstance(history, list):
                    logger.warning(f"Invalid history type for {user_id}: {type(history)}")
                    return False
                
                # Truncate history if too long
                if len(history) > self.max_history_length:
                    history = history[-self.max_history_length:]
                
                with shelve.open(self.db_path, writeback=True) as shelf:
                    # Update the conversation record
                    shelf[user_id] = {
                        'messages': history,
                        'timestamp': time.time()
                    }
                    
                return True
            except Exception as e:
                logger.error(f"Error saving conversation history for {user_id}: {str(e)}")
                return False
    
    def add_message_to_history(self, user_id, role, content):
        """
        Add a single message to the conversation history
        
        Args:
            user_id (str): Unique identifier for the user
            role (str): 'user' or 'assistant'
            content (str): Message content
            
        Returns:
            bool: Success or failure
        """
        history = self.get_conversation_history(user_id)
        history.append({"role": role, "parts": [content]})
        return self.save_conversation_history(user_id, history)
    
    def clear_conversation_history(self, user_id):
        """
        Clear conversation history for a user
        
        Args:
            user_id (str): Unique identifier for the user
            
        Returns:
            bool: Success or failure
        """
        with self._lock:
            try:
                with shelve.open(self.db_path, writeback=True) as shelf:
                    if user_id in shelf:
                        del shelf[user_id]
                        logger.info(f"Cleared conversation history for {user_id}")
                        return True
                    return False
            except Exception as e:
                logger.error(f"Error clearing conversation history for {user_id}: {str(e)}")
                return False
    
    def conversation_exists(self, user_id):
        """
        Check if conversation exists for a user
        
        Args:
            user_id (str): Unique identifier for the user
            
        Returns:
            bool: True if conversation exists
        """
        with self._lock:
            try:
                with shelve.open(self.db_path) as shelf:
                    return user_id in shelf
            except Exception as e:
                logger.error(f"Error checking conversation existence for {user_id}: {str(e)}")
                return False
    
    def cleanup_old_conversations(self):
        """
        Remove conversations older than max_conversation_age
        
        Returns:
            int: Number of conversations removed
        """
        count = 0
        with self._lock:
            try:
                with shelve.open(self.db_path, writeback=True) as shelf:
                    current_time = time.time()
                    user_ids_to_remove = []
                    
                    # Find old conversations
                    for user_id, conversation in shelf.items():
                        if 'timestamp' in conversation:
                            age = current_time - conversation['timestamp']
                            if age > self.max_conversation_age:
                                user_ids_to_remove.append(user_id)
                    
                    # Remove them
                    for user_id in user_ids_to_remove:
                        del shelf[user_id]
                        count += 1
                    
                    if count > 0:
                        logger.info(f"Cleaned up {count} old conversations")
                    
                    return count
            except Exception as e:
                logger.error(f"Error cleaning up old conversations: {str(e)}")
                return 0


# Create a singleton instance
conversation_service = ConversationService()
