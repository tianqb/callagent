"""
Conversation manager for the CallAgent project.
Manages conversations between agents.
"""

import json
import time
from ..database.db_manager import DatabaseManager


class ConversationManager:
    """
    Manages conversations between agents.
    """

    def __init__(self):
        """
        Initialize the conversation manager.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_manager = DatabaseManager()

    def record_conversation(self, sender_id, recipient_id, message):
        """
        Record a conversation in the database.

        Args:
            sender_id (str): ID of the sender.
            recipient_id (str): ID of the recipient.
            message (str): Message content.

        Returns:
            int: ID of the inserted conversation.
        """
        return self.db_manager.record_conversation(sender_id, recipient_id, message)

    def get_conversation_history(self, agent_id, limit=20):
        """
        Get conversation history for an agent.

        Args:
            agent_id (str): ID of the agent.
            limit (int, optional): Maximum number of conversations to retrieve.

        Returns:
            list: Conversation history.
        """
        return self.db_manager.get_conversation_history(agent_id, limit)

    def get_conversation_between(self, agent1_id, agent2_id, limit=20):
        """
        Get conversation history between two agents.

        Args:
            agent1_id (str): ID of the first agent.
            agent2_id (str): ID of the second agent.
            limit (int, optional): Maximum number of conversations to retrieve.

        Returns:
            list: Conversation history.
        """
        query = '''
        SELECT * FROM conversations 
        WHERE (sender_id = ? AND recipient_id = ?) OR (sender_id = ? AND recipient_id = ?)
        ORDER BY timestamp DESC LIMIT ?
        '''
        params = (agent1_id, agent2_id, agent2_id, agent1_id, limit)
        return self.db_manager.execute_query(query, params)

    def get_all_conversations(self, limit=100):
        """
        Get all conversations.

        Args:
            limit (int, optional): Maximum number of conversations to retrieve.

        Returns:
            list: All conversations.
        """
        query = "SELECT * FROM conversations ORDER BY timestamp DESC LIMIT ?"
        params = (limit,)
        return self.db_manager.execute_query(query, params)

    def search_conversations(self, search_term, limit=20):
        """
        Search conversations by content.

        Args:
            search_term (str): Term to search for in message content.
            limit (int, optional): Maximum number of conversations to retrieve.

        Returns:
            list: Matching conversations.
        """
        query = "SELECT * FROM conversations WHERE message LIKE ? ORDER BY timestamp DESC LIMIT ?"
        params = (f"%{search_term}%", limit)
        return self.db_manager.execute_query(query, params)

    def get_conversation_stats(self, agent_id=None):
        """
        Get statistics about conversations.

        Args:
            agent_id (str, optional): ID of the agent. If None, stats for all agents are returned.

        Returns:
            dict: Conversation statistics.
        """
        stats = {}

        # Total count
        query = "SELECT COUNT(*) FROM conversations"
        params = None
        if agent_id:
            query += " WHERE sender_id = ? OR recipient_id = ?"
            params = (agent_id, agent_id)
        result = self.db_manager.execute_query(query, params)
        stats['total_count'] = result[0][0] if result else 0

        # Count by sender
        query = "SELECT sender_id, COUNT(*) FROM conversations"
        if agent_id:
            query += " WHERE sender_id = ? OR recipient_id = ?"
        query += " GROUP BY sender_id"
        result = self.db_manager.execute_query(query, params)
        stats['count_by_sender'] = {row[0]: row[1] for row in result} if result else {}

        # Count by recipient
        query = "SELECT recipient_id, COUNT(*) FROM conversations"
        if agent_id:
            query += " WHERE sender_id = ? OR recipient_id = ?"
        query += " GROUP BY recipient_id"
        result = self.db_manager.execute_query(query, params)
        stats['count_by_recipient'] = {row[0]: row[1] for row in result} if result else {}

        # Count by hour of day
        query = "SELECT strftime('%H', timestamp) as hour, COUNT(*) FROM conversations"
        if agent_id:
            query += " WHERE sender_id = ? OR recipient_id = ?"
        query += " GROUP BY hour ORDER BY hour"
        result = self.db_manager.execute_query(query, params)
        stats['count_by_hour'] = {row[0]: row[1] for row in result} if result else {}

        return stats

    def export_conversations(self, agent_id=None, format='json'):
        """
        Export conversations to a specific format.

        Args:
            agent_id (str, optional): ID of the agent. If None, all conversations are exported.
            format (str, optional): Export format ('json' or 'text').

        Returns:
            str: Exported conversations.
        """
        # Get conversations
        if agent_id:
            conversations = self.get_conversation_history(agent_id, limit=1000)
        else:
            conversations = self.get_all_conversations(limit=1000)

        # Format conversations
        if format == 'json':
            # Convert to list of dicts for JSON serialization
            formatted_conversations = []
            for conv in conversations:
                formatted_conversations.append({
                    'id': conv[0],
                    'sender_id': conv[1],
                    'recipient_id': conv[2],
                    'message': conv[3],
                    'timestamp': conv[4]
                })
            return json.dumps(formatted_conversations, indent=2)
        elif format == 'text':
            # Format as text
            formatted_conversations = []
            for conv in conversations:
                formatted_conversations.append(
                    f"[{conv[4]}] {conv[1]} -> {conv[2]}: {conv[3]}"
                )
            return "\n".join(formatted_conversations)
        else:
            return f"Unsupported format: {format}"

    def delete_conversation(self, conversation_id):
        """
        Delete a conversation.

        Args:
            conversation_id (int): ID of the conversation to delete.

        Returns:
            bool: True if the conversation was deleted successfully.
        """
        query = "DELETE FROM conversations WHERE id = ?"
        params = (conversation_id,)
        result = self.db_manager.execute_update(query, params)
        return result > 0

    def clear_conversations(self, agent_id=None):
        """
        Clear conversations.

        Args:
            agent_id (str, optional): ID of the agent. If None, all conversations are cleared.

        Returns:
            int: Number of conversations cleared.
        """
        query = "DELETE FROM conversations"
        params = None
        if agent_id:
            query += " WHERE sender_id = ? OR recipient_id = ?"
            params = (agent_id, agent_id)
        result = self.db_manager.execute_update(query, params)
        return result
