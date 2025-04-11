"""
Base agent implementation for the CallAgent project.
"""

import uuid
import json
import time
from app.memory.short_term import ShortTermMemory
from app.memory.long_term import LongTermMemory
from app.config import SHORT_TERM_MEMORY_TTL,DATABASE_PATH


class BaseAgent(object):
    """
    Base agent class that provides common functionality for all agents.
    """

    def __init__(self, agent_id=None, name=None):
        """
        Initialize the base agent.

        Args:
            agent_id (str, optional): ID of the agent. If None, a random ID is generated.
            name (str, optional): Name of the agent. If None, a default name is used.
            db_path (str, optional): Path to the SQLite database file.
        """
        self.agent_id = agent_id or f"agent_{uuid.uuid4().hex[:8]}"
        self.name = name or f"Agent-{self.agent_id}"
        self.short_term_memory = ShortTermMemory(cleanup_interval = SHORT_TERM_MEMORY_TTL)
        self.long_term_memory = LongTermMemory()
        self.created_at = time.time()

    def send_message(self, recipient_id, message):
        """
        Send a message to another agent.
        This method should be overridden by the agent hub.

        Args:
            recipient_id (str): ID of the recipient agent.
            message (str): Message content.

        Returns:
            str: Response from the recipient agent.
        """
        # This is a placeholder. The actual implementation will be provided by the agent hub.
        return f"Message from {self.agent_id} to {recipient_id}: {message}"

    def receive_message(self, sender_id, message):
        """
        Receive a message from another agent.

        Args:
            sender_id (str): ID of the sender agent.
            message (str): Message content.

        Returns:
            str: Response to the message.
        """
        # Store the message in short-term memory
        conversation_key = f"conversation:{sender_id}:{int(time.time())}"
        self.short_term_memory.add(
            conversation_key,
            {
                "sender_id": sender_id,
                "message": message,
                "timestamp": time.time()
            },
            ttl=SHORT_TERM_MEMORY_TTL
        )

        # Process the message
        response = self.process_message(sender_id, message)

        # Store the response in short-term memory
        response_key = f"response:{sender_id}:{int(time.time())}"
        self.short_term_memory.add(
            response_key,
            {
                "recipient_id": sender_id,
                "message": response,
                "timestamp": time.time()
            },
            ttl=SHORT_TERM_MEMORY_TTL
        )

        # Store the conversation in long-term memory if available
        if self.long_term_memory:
            self.long_term_memory.store_memory(
                self.agent_id,
                "conversation",
                f"From {sender_id}: {message}\nResponse: {response}",
                {
                    "sender_id": sender_id,
                    "message": message,
                    "response": response,
                    "timestamp": time.time()
                }
            )

        return response

    def process_message(self, sender_id, message):
        """
        Process a message and generate a response.
        This method should be overridden by subclasses.

        Args:
            sender_id (str): ID of the sender agent.
            message (str): Message content.

        Returns:
            str: Response to the message.
        """
        # This is a placeholder. Subclasses should override this method.
        return f"Received message from {sender_id}: {message}"

    def think(self, context):
        """
        Think about a context and generate thoughts.
        This method should be overridden by subclasses.

        Args:
            context (str): Context to think about.

        Returns:
            str: Thoughts about the context.
        """
        # This is a placeholder. Subclasses should override this method.
        thoughts = f"Thinking about: {context}"

        # Store the thoughts in long-term memory if available
        if self.long_term_memory:
            self.long_term_memory.store_memory(
                self.agent_id,
                "thinking",
                thoughts,
                {
                    "context": context,
                    "timestamp": time.time()
                }
            )

        return thoughts

    def plan(self, task):
        """
        Plan how to accomplish a task.
        This method should be overridden by subclasses.

        Args:
            task (str): Task to plan for.

        Returns:
            str: Plan for accomplishing the task.
        """
        # This is a placeholder. Subclasses should override this method.
        plan = f"Plan for task: {task}"

        # Store the plan in long-term memory if available
        if self.long_term_memory:
            self.long_term_memory.store_memory(
                self.agent_id,
                "planning",
                plan,
                {
                    "task": task,
                    "timestamp": time.time()
                }
            )

        return plan

    def execute(self, plan):
        """
        Execute a plan.
        This method should be overridden by subclasses.

        Args:
            plan (str): Plan to execute.

        Returns:
            str: Result of executing the plan.
        """
        # This is a placeholder. Subclasses should override this method.
        result = f"Executed plan: {plan}"

        # Store the result in long-term memory if available
        if self.long_term_memory:
            self.long_term_memory.store_memory(
                self.agent_id,
                "execution",
                result,
                {
                    "plan": plan,
                    "timestamp": time.time()
                }
            )

        return result

    def get_conversation_history(self, agent_id=None, limit=10):
        """
        Get conversation history.

        Args:
            agent_id (str, optional): ID of the agent to get history with. If None, all conversations are returned.
            limit (int, optional): Maximum number of conversations to retrieve.

        Returns:
            list: Conversation history.
        """
        if not self.long_term_memory:
            return []

        # Get conversations from long-term memory
        if agent_id:
            query = '''
            SELECT * FROM memories 
            WHERE agent_id = ? AND memory_type = 'conversation' AND metadata LIKE ?
            ORDER BY created_at DESC LIMIT ?
            '''
            params = (self.agent_id, f'%"sender_id": "{agent_id}"%', limit)
        else:
            query = '''
            SELECT * FROM memories 
            WHERE agent_id = ? AND memory_type = 'conversation'
            ORDER BY created_at DESC LIMIT ?
            '''
            params = (self.agent_id, limit)

        return self.long_term_memory.db_manager.execute_query(query, params)

    def get_thinking_history(self, limit=10):
        """
        Get thinking history.

        Args:
            limit (int, optional): Maximum number of thinking entries to retrieve.

        Returns:
            list: Thinking history.
        """
        if not self.long_term_memory:
            return []

        return self.long_term_memory.retrieve_memories(
            self.agent_id,
            memory_type="thinking",
            limit=limit
        )

    def get_planning_history(self, limit=10):
        """
        Get planning history.

        Args:
            limit (int, optional): Maximum number of planning entries to retrieve.

        Returns:
            list: Planning history.
        """
        if not self.long_term_memory:
            return []

        return self.long_term_memory.retrieve_memories(
            self.agent_id,
            memory_type="planning",
            limit=limit
        )

    def get_execution_history(self, limit=10):
        """
        Get execution history.

        Args:
            limit (int, optional): Maximum number of execution entries to retrieve.

        Returns:
            list: Execution history.
        """
        if not self.long_term_memory:
            return []

        return self.long_term_memory.retrieve_memories(
            self.agent_id,
            memory_type="execution",
            limit=limit
        )

    def to_dict(self):
        """
        Convert the agent to a dictionary.

        Returns:
            dict: Dictionary representation of the agent.
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "created_at": self.created_at
        }

    def to_json(self):
        """
        Convert the agent to a JSON string.

        Returns:
            str: JSON representation of the agent.
        """
        return json.dumps(self.to_dict())

    def __str__(self):
        """
        Get a string representation of the agent.

        Returns:
            str: String representation of the agent.
        """
        return f"{self.name} ({self.agent_id})"
