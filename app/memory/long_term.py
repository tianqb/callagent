"""
Long-term memory implementation for the CallAgent project.
Stores persistent data in SQLite database.
"""

import sqlite3
import json
import time
from ..database.db_manager import DatabaseManager


class LongTermMemory:
    """
    Long-term memory implementation that stores data in SQLite database.
    """

    def __init__(self, db_path):
        """
        Initialize the long-term memory.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_manager = DatabaseManager(db_path)
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """
        Initialize the database tables if they don't exist.
        """
        self.db_manager.init_db()

    def store_memory(self, agent_id, memory_type, content, metadata=None):
        """
        Store a memory in the database.

        Args:
            agent_id (str): ID of the agent.
            memory_type (str): Type of memory (thinking, planning, execution).
            content (str): Memory content.
            metadata (dict, optional): Additional metadata.

        Returns:
            int: ID of the inserted memory.
        """
        return self.db_manager.store_memory(agent_id, memory_type, content, metadata)

    def retrieve_memories(self, agent_id, memory_type=None, limit=10):
        """
        Retrieve memories from the database.

        Args:
            agent_id (str): ID of the agent.
            memory_type (str, optional): Type of memory to retrieve.
            limit (int, optional): Maximum number of memories to retrieve.

        Returns:
            list: Retrieved memories.
        """
        return self.db_manager.retrieve_memories(agent_id, memory_type, limit)

    def retrieve_memories_by_content(self, agent_id, search_term, memory_type=None, limit=10):
        """
        Retrieve memories from the database by content search.

        Args:
            agent_id (str): ID of the agent.
            search_term (str): Term to search for in memory content.
            memory_type (str, optional): Type of memory to retrieve.
            limit (int, optional): Maximum number of memories to retrieve.

        Returns:
            list: Retrieved memories.
        """
        query = "SELECT * FROM memories WHERE agent_id = ? AND content LIKE ?"
        params = [agent_id, f"%{search_term}%"]

        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        return self.db_manager.execute_query(query, tuple(params))

    def retrieve_memories_by_timeframe(self, agent_id, start_time, end_time=None, memory_type=None, limit=10):
        """
        Retrieve memories from the database within a specific timeframe.

        Args:
            agent_id (str): ID of the agent.
            start_time (float): Start timestamp.
            end_time (float, optional): End timestamp. If None, current time is used.
            memory_type (str, optional): Type of memory to retrieve.
            limit (int, optional): Maximum number of memories to retrieve.

        Returns:
            list: Retrieved memories.
        """
        if end_time is None:
            end_time = time.time()

        start_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))
        end_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))

        query = "SELECT * FROM memories WHERE agent_id = ? AND created_at BETWEEN ? AND ?"
        params = [agent_id, start_time_str, end_time_str]

        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        return self.db_manager.execute_query(query, tuple(params))

    def delete_memory(self, memory_id):
        """
        Delete a memory from the database.

        Args:
            memory_id (int): ID of the memory to delete.

        Returns:
            bool: True if the memory was deleted successfully.
        """
        query = "DELETE FROM memories WHERE id = ?"
        params = (memory_id,)
        result = self.db_manager.execute_update(query, params)
        return result > 0

    def clear_memories(self, agent_id=None, memory_type=None):
        """
        Clear memories from the database.

        Args:
            agent_id (str, optional): ID of the agent. If None, all agents' memories are cleared.
            memory_type (str, optional): Type of memory to clear. If None, all types are cleared.

        Returns:
            int: Number of memories cleared.
        """
        query = "DELETE FROM memories"
        params = []

        if agent_id or memory_type:
            query += " WHERE"

        if agent_id:
            query += " agent_id = ?"
            params.append(agent_id)

        if memory_type:
            if agent_id:
                query += " AND"
            query += " memory_type = ?"
            params.append(memory_type)

        result = self.db_manager.execute_update(query, tuple(params) if params else None)
        return result

    def get_memory_stats(self, agent_id=None):
        """
        Get statistics about stored memories.

        Args:
            agent_id (str, optional): ID of the agent. If None, stats for all agents are returned.

        Returns:
            dict: Memory statistics.
        """
        stats = {}

        # Total count
        query = "SELECT COUNT(*) FROM memories"
        params = None
        if agent_id:
            query += " WHERE agent_id = ?"
            params = (agent_id,)
        result = self.db_manager.execute_query(query, params)
        stats['total_count'] = result[0][0] if result else 0

        # Count by type
        query = "SELECT memory_type, COUNT(*) FROM memories"
        if agent_id:
            query += " WHERE agent_id = ?"
        query += " GROUP BY memory_type"
        result = self.db_manager.execute_query(query, params)
        stats['count_by_type'] = {row[0]: row[1] for row in result} if result else {}

        # Count by agent (if no specific agent)
        if not agent_id:
            query = "SELECT agent_id, COUNT(*) FROM memories GROUP BY agent_id"
            result = self.db_manager.execute_query(query)
            stats['count_by_agent'] = {row[0]: row[1] for row in result} if result else {}

        return stats
