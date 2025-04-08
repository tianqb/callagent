"""
Agent Hub implementation for the CallAgent project.
Manages communication between agents.
"""

import uuid
import json
import time
from ..database.db_manager import DatabaseManager


class AgentHub:
    """
    Agent Hub manages communication between agents.
    """

    def __init__(self, db_path):
        """
        Initialize the Agent Hub.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.agents = {}
        self.db_path = db_path
        self.db_manager = DatabaseManager(db_path)

    def register_agent(self, agent):
        """
        Register an agent with the hub.

        Args:
            agent: Agent object to register.

        Returns:
            bool: True if the agent was registered successfully.
        """
        if hasattr(agent, 'agent_id') and agent.agent_id:
            self.agents[agent.agent_id] = agent
            return True
        return False

    def unregister_agent(self, agent_id):
        """
        Unregister an agent from the hub.

        Args:
            agent_id (str): ID of the agent to unregister.

        Returns:
            bool: True if the agent was unregistered successfully.
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False

    def get_agent(self, agent_id):
        """
        Get an agent by ID.

        Args:
            agent_id (str): ID of the agent to get.

        Returns:
            Agent: The agent object, or None if not found.
        """
        return self.agents.get(agent_id)

    def get_all_agents(self):
        """
        Get all registered agents.

        Returns:
            dict: Dictionary of agent_id -> agent.
        """
        return self.agents

    def send_message(self, sender_id, recipient_id, message):
        """
        Send a message from one agent to another.

        Args:
            sender_id (str): ID of the sending agent.
            recipient_id (str): ID of the receiving agent.
            message (str): Message content.

        Returns:
            str: Response from the recipient agent, or error message if the agent is not found.
        """
        # Record the conversation
        self.db_manager.record_conversation(sender_id, recipient_id, message)

        # Forward the message to the recipient
        if recipient_id in self.agents:
            recipient = self.agents[recipient_id]
            if hasattr(recipient, 'receive_message') and callable(recipient.receive_message):
                response = recipient.receive_message(sender_id, message)
                # Record the response
                self.db_manager.record_conversation(recipient_id, sender_id, response)
                return response
            else:
                return f"Agent {recipient_id} does not implement receive_message method"
        else:
            return f"Agent {recipient_id} not found"

    def broadcast_message(self, sender_id, message, exclude_ids=None):
        """
        Broadcast a message to all agents except the sender and any excluded agents.

        Args:
            sender_id (str): ID of the sending agent.
            message (str): Message content.
            exclude_ids (list, optional): List of agent IDs to exclude from the broadcast.

        Returns:
            dict: Dictionary of agent_id -> response.
        """
        if exclude_ids is None:
            exclude_ids = []

        if sender_id not in exclude_ids:
            exclude_ids.append(sender_id)

        responses = {}
        for agent_id, agent in self.agents.items():
            if agent_id not in exclude_ids:
                # Record the conversation
                self.db_manager.record_conversation(sender_id, agent_id, message)

                # Send the message
                if hasattr(agent, 'receive_message') and callable(agent.receive_message):
                    response = agent.receive_message(sender_id, message)
                    # Record the response
                    self.db_manager.record_conversation(agent_id, sender_id, response)
                    responses[agent_id] = response

        return responses

    def get_conversation_history(self, agent_id=None, limit=20):
        """
        Get conversation history.

        Args:
            agent_id (str, optional): ID of the agent to get history for. If None, all conversations are returned.
            limit (int, optional): Maximum number of conversations to retrieve.

        Returns:
            list: Conversation history.
        """
        if agent_id:
            return self.db_manager.get_conversation_history(agent_id, limit)
        else:
            query = "SELECT * FROM conversations ORDER BY timestamp DESC LIMIT ?"
            params = (limit,)
            return self.db_manager.execute_query(query, params)

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

    def create_group(self, group_name, agent_ids):
        """
        Create a group of agents.

        Args:
            group_name (str): Name of the group.
            agent_ids (list): List of agent IDs to include in the group.

        Returns:
            str: Group ID.
        """
        group_id = f"group_{uuid.uuid4().hex[:8]}"
        
        # Store group in short-term memory (could be moved to database for persistence)
        group_data = {
            "name": group_name,
            "members": agent_ids,
            "created_at": time.time()
        }
        
        # Use the first agent's short-term memory to store the group
        # This is a simple approach; a more robust solution would use a dedicated group manager
        if agent_ids and agent_ids[0] in self.agents:
            agent = self.agents[agent_ids[0]]
            if hasattr(agent, 'short_term_memory'):
                agent.short_term_memory.add(f"group:{group_id}", group_data)
                return group_id
        
        return None

    def send_group_message(self, sender_id, group_id, message):
        """
        Send a message to a group of agents.

        Args:
            sender_id (str): ID of the sending agent.
            group_id (str): ID of the group.
            message (str): Message content.

        Returns:
            dict: Dictionary of agent_id -> response.
        """
        # Find the group
        group_data = None
        for agent_id, agent in self.agents.items():
            if hasattr(agent, 'short_term_memory'):
                group_data = agent.short_term_memory.get(f"group:{group_id}")
                if group_data:
                    break
        
        if not group_data:
            return {"error": f"Group {group_id} not found"}
        
        # Send message to all group members
        responses = {}
        for member_id in group_data["members"]:
            if member_id != sender_id and member_id in self.agents:
                # Record the conversation
                self.db_manager.record_conversation(
                    sender_id, 
                    member_id, 
                    f"[Group: {group_data['name']}] {message}"
                )
                
                # Send the message
                agent = self.agents[member_id]
                if hasattr(agent, 'receive_message') and callable(agent.receive_message):
                    response = agent.receive_message(
                        sender_id, 
                        f"[Group: {group_data['name']}] {message}"
                    )
                    # Record the response
                    self.db_manager.record_conversation(
                        member_id, 
                        sender_id, 
                        f"[Group: {group_data['name']}] {response}"
                    )
                    responses[member_id] = response
        
        return responses
