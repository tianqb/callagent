"""
Database manager for the CallAgent project.
Handles database connections, queries, and updates.
"""

import sqlite3
import json
import os
from pathlib import Path
from app.config import DATABASE_PATH

class DatabaseManager:
    """
    Manages SQLite database operations for the CallAgent project.
    """

    def __init__(self):
        """
        Initialize the database manager.

        Args:
            
        """

        # Create directory if it doesn't exist
        db_dir = os.path.dirname(DATABASE_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        self.db_path = DATABASE_PATH

    def init_db(self):
        """
        Initialize the database tables if they don't exist.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create memories table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT,
            memory_type TEXT,
            content TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create conversations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id TEXT,
            recipient_id TEXT,
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create planning table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS planning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT,
            agent_id TEXT,
            plan_type TEXT,
            content TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        conn.commit()
        conn.close()

    def execute_query(self, query, params=None):
        """
        Execute a query and return the results.

        Args:
            query (str): SQL query to execute.
            params (tuple, optional): Parameters for the query.

        Returns:
            list: Query results.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        results = cursor.fetchall()
        conn.close()
        return results

    def execute_update(self, query, params=None):
        """
        Execute an update query (INSERT, UPDATE, DELETE).

        Args:
            query (str): SQL query to execute.
            params (tuple, optional): Parameters for the query.

        Returns:
            int: Last row ID or number of affected rows.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

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
        query = '''
        INSERT INTO memories (agent_id, memory_type, content, metadata)
        VALUES (?, ?, ?, ?)
        '''
        params = (
            agent_id,
            memory_type,
            content,
            json.dumps(metadata) if metadata else None
        )
        return self.execute_update(query, params)

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
        query = "SELECT * FROM memories WHERE agent_id = ?"
        params = [agent_id]

        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        return self.execute_query(query, tuple(params))

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
        query = '''
        INSERT INTO conversations (sender_id, recipient_id, message)
        VALUES (?, ?, ?)
        '''
        params = (sender_id, recipient_id, message)
        return self.execute_update(query, params)

    def get_conversation_history(self, agent_id, limit=20):
        """
        Get conversation history for an agent.

        Args:
            agent_id (str): ID of the agent.
            limit (int, optional): Maximum number of conversations to retrieve.

        Returns:
            list: Conversation history.
        """
        query = '''
        SELECT * FROM conversations 
        WHERE sender_id = ? OR recipient_id = ?
        ORDER BY timestamp DESC LIMIT ?
        '''
        params = (agent_id, agent_id, limit)
        return self.execute_query(query, params)

    def record_planning(self, task_id, agent_id, plan_type, content, status="pending"):
        """
        Record a planning entry in the database.

        Args:
            task_id (str): ID of the task.
            agent_id (str): ID of the agent.
            plan_type (str): Type of plan (task_creation, subtask, assignment).
            content (str): Plan content.
            status (str, optional): Status of the plan.

        Returns:
            int: ID of the inserted planning entry.
        """
        query = '''
        INSERT INTO planning (task_id, agent_id, plan_type, content, status)
        VALUES (?, ?, ?, ?, ?)
        '''
        params = (task_id, agent_id, plan_type, content, status)
        return self.execute_update(query, params)

    def update_planning_status(self, planning_id, status):
        """
        Update the status of a planning entry.

        Args:
            planning_id (int): ID of the planning entry.
            status (str): New status.

        Returns:
            int: Number of affected rows.
        """
        query = '''
        UPDATE planning 
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        '''
        params = (status, planning_id)
        return self.execute_update(query, params)

    def get_planning_by_task(self, task_id):
        """
        Get planning entries for a task.

        Args:
            task_id (str): ID of the task.

        Returns:
            list: Planning entries.
        """
        query = '''
        SELECT * FROM planning WHERE task_id = ? ORDER BY created_at
        '''
        params = (task_id,)
        return self.execute_query(query, params)
