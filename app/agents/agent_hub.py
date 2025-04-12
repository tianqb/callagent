"""
Agent Hub implementation for the CallAgent project.
Manages agent creation, registration, and communication between agents.
"""

import uuid
import json
import time
import asyncio
import importlib
from typing import Dict, List, Optional, Any, Tuple
from app.database.db_manager import DatabaseManager
from app.agents.base import BaseAgent
from app.utils.constant import AgentType, AgentState, AGENT_TYPE_VALUES
from app.planning.task_planner import TaskPlanner
from app.planning.plan_executor import PlanExecutor


class AgentHub:
    """
    Agent Hub manages agent creation, registration, and communication between agents.
    This class combines the functionality of the previous AgentFactory, ConversationManager,
    and AdminAgent.
    """

    def __init__(self):
        """
        Initialize the Agent Hub.
        """
        self.agents = {}
        self.db_manager = DatabaseManager()
        
        # Admin functionality
        self.managed_agents = {}
        self.tasks = {}
        self.quality_assessments = {}
        self.discussions = {}

    #
    # Agent Factory Methods
    #

    def create_agent(self, agent_type, agent_id=None, name=None, auto_save=False, is_debug=False, **kwargs):
        """
        Create an agent of the specified type.

        Args:
            agent_type (str): Type of agent to create ('base', 'research', 'planning', 'execution', 'critic', 'admin').
            agent_id (str, optional): ID of the agent. If None, a random ID is generated.
            name (str, optional): Name of the agent. If None, a default name is used.
            auto_save (bool, optional): Whether to automatically save agent state.
            is_debug (bool, optional): Whether to enable debug mode.
            **kwargs: Additional arguments to pass to the agent constructor.

        Returns:
            BaseAgent: The created agent.

        Raises:
            ValueError: If the agent type is not supported.
        """
        if agent_id is None:
            agent_id = f"agent_{uuid.uuid4().hex[:8]}"

        # Use dynamic imports to avoid circular dependencies
        if agent_type == AgentType.BASE:
            agent = BaseAgent(agent_id=agent_id, name=name, auto_save=auto_save, is_debug=is_debug, **kwargs)
        else:
            # Dynamically import the agent class based on agent_type
            try:
                module_name = f"app.agents.{agent_type.lower()}"
                class_name = f"{agent_type.capitalize()}Agent"
                
                # Import the module dynamically
                module = importlib.import_module(module_name)
                
                # Get the agent class from the module
                agent_class = getattr(module, class_name)
                
                # Create an instance of the agent class
                agent = agent_class(agent_id=agent_id, name=name, auto_save=auto_save, is_debug=is_debug, **kwargs)
            except (ImportError, AttributeError) as e:
                raise ValueError(f"Unsupported agent type: {agent_type}. Error: {str(e)}")

        # Automatically register the agent with the hub
        self.register_agent(agent)
        return agent

    def create_team(self, team_name, agent_types=None):
        """
        Create a team of agents.

        Args:
            team_name (str): Name of the team.
            agent_types (list, optional): List of agent types to create. If None, a default team is created.

        Returns:
            dict: Dictionary of agent_id -> agent for the created team.
        """
        if agent_types is None:
            agent_types = AGENT_TYPE_VALUES

        team = {}
        for i, agent_type in enumerate(agent_types):
            agent_name = f"{team_name} {agent_type.capitalize()} Agent"
            agent = self.create_agent(agent_type, name=agent_name)
            team[agent.agent_id] = agent

        return team

    def create_specialized_team(self, team_name, specializations):
        """
        Create a team of specialized agents.

        Args:
            team_name (str): Name of the team.
            specializations (dict): Dictionary of agent_type -> specialization_kwargs.

        Returns:
            dict: Dictionary of agent_id -> agent for the created team.
        """
        team = {}
        for agent_type, kwargs in specializations.items():
            agent_name = f"{team_name} {agent_type.capitalize()} Agent"
            agent = self.create_agent(agent_type, name=agent_name, **kwargs)
            team[agent.agent_id] = agent

        return team

    def create_research_agent(self, name=None, auto_save=False, is_debug=False, expertise=None):
        """
        Create a research agent.

        Args:
            name (str, optional): Name of the agent. If None, a default name is used.
            auto_save (bool, optional): Whether to automatically save agent state.
            is_debug (bool, optional): Whether to enable debug mode.
            expertise (list, optional): List of areas of expertise.

        Returns:
            ResearchAgent: The created agent.
        """
        return self.create_agent(AgentType.RESEARCH, name=name, auto_save=auto_save, is_debug=is_debug, expertise=expertise)

    def create_planning_agent(self, name=None, auto_save=False, is_debug=False):
        """
        Create a planning agent.

        Args:
            name (str, optional): Name of the agent. If None, a default name is used.
            auto_save (bool, optional): Whether to automatically save agent state.
            is_debug (bool, optional): Whether to enable debug mode.

        Returns:
            PlanningAgent: The created agent.
        """
        return self.create_agent(AgentType.PLANNING, name=name, auto_save=auto_save, is_debug=is_debug)

    def create_execution_agent(self, name=None, auto_save=False, is_debug=False, skills=None):
        """
        Create an execution agent.

        Args:
            name (str, optional): Name of the agent. If None, a default name is used.
            auto_save (bool, optional): Whether to automatically save agent state.
            is_debug (bool, optional): Whether to enable debug mode.
            skills (list, optional): List of skills.

        Returns:
            ExecutionAgent: The created agent.
        """
        return self.create_agent(AgentType.EXECUTION, name=name, auto_save=auto_save, is_debug=is_debug, skills=skills)

    def create_critic_agent(self, name=None, auto_save=False, is_debug=False):
        """
        Create a critic agent.

        Args:
            name (str, optional): Name of the agent. If None, a default name is used.
            auto_save (bool, optional): Whether to automatically save agent state.
            is_debug (bool, optional): Whether to enable debug mode.

        Returns:
            CriticAgent: The created agent.
        """
        return self.create_agent(AgentType.CRITIC, name=name, auto_save=auto_save, is_debug=is_debug)
    
    def create_admin_agent(self, name=None, auto_save=False, is_debug=False):
        """
        Create an admin agent.

        Args:
            name (str, optional): Name of the agent. If None, a default name is used.
            auto_save (bool, optional): Whether to automatically save agent state.
            is_debug (bool, optional): Whether to enable debug mode.

        Returns:
            AdminAgent: The created agent.
        """
        return self.create_agent(AgentType.ADMIN, name=name, auto_save=auto_save, is_debug=is_debug)

    #
    # Agent Hub Methods
    #

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

    def delete_agent(self, agent_id):
        """
        Delete an agent.

        Args:
            agent_id (str): ID of the agent to delete.

        Returns:
            bool: True if the agent was deleted, False if it wasn't found.
        """
        return self.unregister_agent(agent_id)

    #
    # Conversation Manager Methods
    #

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

    def send_message(self, sender_id, recipient_id, message):
        """
        Send a message from one agent to another and record it.

        Args:
            sender_id (str): ID of the sending agent.
            recipient_id (str): ID of the receiving agent.
            message (str): Message content.

        Returns:
            str: Response from the recipient agent, or error message if the agent is not found.
        """
        # Record the conversation
        self.record_conversation(sender_id, recipient_id, message)

        # Forward the message to the recipient
        if recipient_id in self.agents:
            recipient = self.agents[recipient_id]
            if hasattr(recipient, 'receive_message') and callable(recipient.receive_message):
                response = recipient.receive_message(sender_id, message)
                # Record the response
                self.record_conversation(recipient_id, sender_id, response)
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
                self.record_conversation(sender_id, agent_id, message)

                # Send the message
                if hasattr(agent, 'receive_message') and callable(agent.receive_message):
                    response = agent.receive_message(sender_id, message)
                    # Record the response
                    self.record_conversation(agent_id, sender_id, response)
                    responses[agent_id] = response

        return responses

    def get_conversation_history(self, agent_id=None, limit=20):
        """
        Get conversation history for an agent.

        Args:
            agent_id (str, optional): ID of the agent.
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

    #
    # Group Management Methods
    #

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
                self.record_conversation(
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
                    self.record_conversation(
                        member_id, 
                        sender_id, 
                        f"[Group: {group_data['name']}] {response}"
                    )
                    responses[member_id] = response
        
        return responses

    #
    # Admin Agent Methods
    #

    def get_agent_by_type(self, agent_type):
        """
        Get a managed agent by type.
        
        Args:
            agent_type (str): Type of agent to get.
            
        Returns:
            BaseAgent: The requested agent, or None if not found.
        """
        return self.managed_agents.get(agent_type)

    async def initialize_team(self, admin_id=None, auto_save=False, is_debug=False):
        """
        Initialize a team of agents for collaboration.
        
        Args:
            admin_id (str, optional): ID of the admin agent. If None, a new admin agent is created.
            auto_save (bool, optional): Whether to automatically save agent state.
            is_debug (bool, optional): Whether to enable debug mode.
            
        Returns:
            dict: Dictionary of agent_id -> agent for the created team.
        """
        # Create research agent
        research_agent = self.create_agent(
            AgentType.RESEARCH, 
            name="Research Agent",
            auto_save=auto_save,
            is_debug=is_debug
        )
        
        # Create planning agent
        planning_agent = self.create_agent(
            AgentType.PLANNING, 
            name="Planning Agent",
            auto_save=auto_save,
            is_debug=is_debug
        )
        
        # Create execution agent
        execution_agent = self.create_agent(
            AgentType.EXECUTION, 
            name="Execution Agent",
            auto_save=auto_save,
            is_debug=is_debug
        )
        
        # Create critic agent
        critic_agent = self.create_agent(
            AgentType.CRITIC, 
            name="Critic Agent",
            auto_save=auto_save,
            is_debug=is_debug
        )
        
        # Store managed agents
        self.managed_agents = {
            AgentType.RESEARCH: research_agent,
            AgentType.PLANNING: planning_agent,
            AgentType.EXECUTION: execution_agent,
            AgentType.CRITIC: critic_agent
        }
        
        # Initialize task planner and executor
        self.task_planner = TaskPlanner(self)
        self.plan_executor = PlanExecutor(self)
        
        return self.managed_agents
    
    async def create_task(self, task_description, creator_id=None):
        """
        Create a new task and coordinate its execution.
        
        Args:
            task_description (str): Description of the task.
            creator_id (str, optional): ID of the task creator.
            
        Returns:
            str: Task ID.
        """
        # Create a task ID
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        # Store task information
        self.tasks[task_id] = {
            "description": task_description,
            "state": AgentState.IDLE,
            "created_at": time.time(),
            "results": {},
            "quality_score": None,
            "iterations": 0
        }
        
        # Record the task in the task planner
        self.task_planner.create_task(task_description, creator_id=creator_id)
        
        return task_id
    
    async def execute_task(self, task_id, admin_id=None):
        """
        Execute a task using the team of agents.
        
        Args:
            task_id (str): ID of the task to execute.
            admin_id (str, optional): ID of the admin agent.
            
        Returns:
            dict: Results from each agent.
        """
        if task_id not in self.tasks:
            return {"error": f"Task {task_id} not found"}
        
        # Update task state
        self.tasks[task_id]["state"] = AgentState.RUNNING
        self.tasks[task_id]["iterations"] += 1
        
        # Get task description
        task_description = self.tasks[task_id]["description"]
        
        # Execute research, planning, execution, and critique in parallel
        research_task = self.execute_research(task_id, task_description, admin_id)
        planning_task = self.execute_planning(task_id, task_description, admin_id)
        execution_task = self.execute_execution(task_id, task_description, admin_id)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(research_task, planning_task, execution_task)
        
        # Store results
        research_result, planning_result, execution_result = results
        self.tasks[task_id]["results"] = {
            AgentType.RESEARCH: research_result,
            AgentType.PLANNING: planning_result,
            AgentType.EXECUTION: execution_result
        }
        
        # Evaluate results
        critique_result = await self.execute_critique(task_id, results, admin_id)
        self.tasks[task_id]["results"][AgentType.CRITIC] = critique_result
        
        # Determine if quality is satisfactory
        quality_score = self.evaluate_quality(task_id, critique_result)
        self.tasks[task_id]["quality_score"] = quality_score
        
        # Update task state
        self.tasks[task_id]["state"] = AgentState.FINISHED
        
        return self.tasks[task_id]["results"]
    
    async def execute_research(self, task_id, task_description, admin_id=None):
        """
        Execute research for a task.
        
        Args:
            task_id (str): ID of the task.
            task_description (str): Description of the task.
            admin_id (str, optional): ID of the admin agent.
            
        Returns:
            str: Research results.
        """
        research_agent = self.get_agent_by_type(AgentType.RESEARCH)
        if not research_agent:
            return "Research agent not available"
        
        # Send task to research agent
        message = f"Research task: {task_description}"
        response = self.send_message(admin_id or "system", research_agent.agent_id, message)
        
        # Store research in task planner
        self.task_planner.decompose_task(task_id, ["Research: " + task_description])
        
        return response
    
    async def execute_planning(self, task_id, task_description, admin_id=None):
        """
        Execute planning for a task.
        
        Args:
            task_id (str): ID of the task.
            task_description (str): Description of the task.
            admin_id (str, optional): ID of the admin agent.
            
        Returns:
            str: Planning results.
        """
        planning_agent = self.get_agent_by_type(AgentType.PLANNING)
        if not planning_agent:
            return "Planning agent not available"
        
        # Send task to planning agent
        message = f"Plan task: {task_description}"
        response = self.send_message(admin_id or "system", planning_agent.agent_id, message)
        
        # Store plan in task planner
        self.task_planner.decompose_task(task_id, ["Planning: " + task_description])
        
        return response
    
    async def execute_execution(self, task_id, task_description, admin_id=None):
        """
        Execute implementation for a task.
        
        Args:
            task_id (str): ID of the task.
            task_description (str): Description of the task.
            admin_id (str, optional): ID of the admin agent.
            
        Returns:
            str: Execution results.
        """
        execution_agent = self.get_agent_by_type(AgentType.EXECUTION)
        if not execution_agent:
            return "Execution agent not available"
        
        # Send task to execution agent
        message = f"Execute task: {task_description}"
        response = self.send_message(admin_id or "system", execution_agent.agent_id, message)
        
        # Store execution in task planner
        self.task_planner.decompose_task(task_id, ["Execution: " + task_description])
        
        return response
    
    async def execute_critique(self, task_id, results, admin_id=None):
        """
        Execute critique for task results.
        
        Args:
            task_id (str): ID of the task.
            results (tuple): Results from research, planning, and execution.
            admin_id (str, optional): ID of the admin agent.
            
        Returns:
            str: Critique results.
        """
        critic_agent = self.get_agent_by_type(AgentType.CRITIC)
        if not critic_agent:
            return "Critic agent not available"
        
        # Format results for critique
        research_result, planning_result, execution_result = results
        critique_request = (
            f"Critique the following task results:\n\n"
            f"Task ID: {task_id}\n"
            f"Research Results:\n{research_result}\n\n"
            f"Planning Results:\n{planning_result}\n\n"
            f"Execution Results:\n{execution_result}\n\n"
            f"Please evaluate the quality, completeness, and accuracy of these results."
        )
        
        # Send critique request to critic agent
        response = self.send_message(admin_id or "system", critic_agent.agent_id, critique_request)
        
        # Store critique in task planner
        self.task_planner.decompose_task(task_id, ["Critique of results"])
        
        return response
    
    def evaluate_quality(self, task_id, critique_result):
        """
        Evaluate the quality of task results based on critique.
        
        Args:
            task_id (str): ID of the task.
            critique_result (str): Critique from the critic agent.
            
        Returns:
            float: Quality score between 0 and 1.
        """
        # Simple heuristic: check for positive/negative keywords in critique
        positive_keywords = ["excellent", "good", "complete", "accurate", "thorough", "comprehensive"]
        negative_keywords = ["incomplete", "inaccurate", "poor", "missing", "inadequate", "insufficient"]
        
        # Count occurrences
        positive_count = sum(1 for keyword in positive_keywords if keyword in critique_result.lower())
        negative_count = sum(1 for keyword in negative_keywords if keyword in critique_result.lower())
        
        # Calculate score (simple heuristic)
        total = positive_count + negative_count
        if total == 0:
            score = 0.5  # Neutral if no keywords found
        else:
            score = positive_count / total
        
        # Store quality assessment
        self.quality_assessments[task_id] = {
            "score": score,
            "critique": critique_result,
            "timestamp": time.time()
        }
        
        return score
    
    async def improve_task_results(self, task_id, min_quality_score=0.7, max_iterations=3):
        """
        Improve task results through iterative refinement if quality is insufficient.
        
        Args:
            task_id (str): ID of the task.
            min_quality_score (float, optional): Minimum acceptable quality score.
            max_iterations (int, optional): Maximum number of improvement iterations.
            
        Returns:
            dict: Final results after improvement.
        """
        if task_id not in self.tasks:
            return {"error": f"Task {task_id} not found"}
        
        # Check if task has been executed
        if self.tasks[task_id]["state"] != AgentState.FINISHED:
            await self.execute_task(task_id)
        
        # Get current quality score
        quality_score = self.tasks[task_id].get("quality_score", 0)
        iterations = self.tasks[task_id].get("iterations", 1)
        
        # Continue improving until quality is satisfactory or max iterations reached
        while quality_score < min_quality_score and iterations < max_iterations:
            # Create a discussion to improve results
            discussion_id = await self.initiate_discussion(task_id)
            
            # Re-execute the task with insights from discussion
            await self.execute_task(task_id)
            
            # Update iteration count and quality score
            iterations = self.tasks[task_id].get("iterations", 1)
            quality_score = self.tasks[task_id].get("quality_score", 0)
        
        return self.tasks[task_id]["results"]
    
    async def initiate_discussion(self, task_id):
        """
        Initiate a discussion between agents to improve task results.
        
        Args:
            task_id (str): ID of the task.
            
        Returns:
            str: Discussion ID.
        """
        # Create a discussion ID
        discussion_id = f"discussion_{uuid.uuid4().hex[:8]}"
        
        # Get task results and critique
        results = self.tasks[task_id]["results"]
        critique = results.get(AgentType.CRITIC, "No critique available")
        
        # Format discussion prompt
        discussion_prompt = (
            f"We need to improve the results for task {task_id}. "
            f"The critique identified the following issues:\n\n{critique}\n\n"
            f"Let's discuss how to address these issues and improve the results."
        )
        
        # Store discussion information
        self.discussions[discussion_id] = {
            "task_id": task_id,
            "prompt": discussion_prompt,
            "messages": [],
            "started_at": time.time(),
            "active": True
        }
        
        # Start discussion with research agent
        research_agent = self.get_agent_by_type(AgentType.RESEARCH)
        initial_response = self.send_message(
            "system", 
            research_agent.agent_id, 
            discussion_prompt
        )
        
        # Record initial message
        self.discussions[discussion_id]["messages"].append({
            "sender_id": "system",
            "recipient_id": research_agent.agent_id,
            "message": discussion_prompt,
            "timestamp": time.time()
        })
        
        self.discussions[discussion_id]["messages"].append({
            "sender_id": research_agent.agent_id,
            "recipient_id": "system",
            "message": initial_response,
            "timestamp": time.time()
        })
        
        # Continue discussion with planning agent
        planning_agent = self.get_agent_by_type(AgentType.PLANNING)
        planning_prompt = f"Based on the research agent's response:\n\n{initial_response}\n\nHow would you improve the plan?"
        planning_response = self.send_message(
            "system", 
            planning_agent.agent_id, 
            planning_prompt
        )
        
        # Record planning message
        self.discussions[discussion_id]["messages"].append({
            "sender_id": "system",
            "recipient_id": planning_agent.agent_id,
            "message": planning_prompt,
            "timestamp": time.time()
        })
        
        self.discussions[discussion_id]["messages"].append({
            "sender_id": planning_agent.agent_id,
            "recipient_id": "system",
            "message": planning_response,
            "timestamp": time.time()
        })
        
        # Continue discussion with execution agent
        execution_agent = self.get_agent_by_type(AgentType.EXECUTION)
        execution_prompt = (
            f"Based on the research and planning responses:\n\n"
            f"Research: {initial_response}\n\n"
            f"Planning: {planning_response}\n\n"
            f"How would you improve the execution?"
        )
        execution_response = self.send_message(
            "system", 
            execution_agent.agent_id, 
            execution_prompt
        )
        
        # Record execution message
        self.discussions[discussion_id]["messages"].append({
            "sender_id": "system",
            "recipient_id": execution_agent.agent_id,
            "message": execution_prompt,
            "timestamp": time.time()
        })
        
        self.discussions[discussion_id]["messages"].append({
            "sender_id": execution_agent.agent_id,
            "recipient_id": "system",
            "message": execution_response,
            "timestamp": time.time()
        })
        
        # Conclude discussion
        self.discussions[discussion_id]["active"] = False
        self.discussions[discussion_id]["concluded_at"] = time.time()
        
        return discussion_id
    
    def get_discussion(self, discussion_id):
        """
        Get a discussion by ID.
        
        Args:
            discussion_id (str): ID of the discussion.
            
        Returns:
            dict: Discussion data, or None if not found.
        """
        return self.discussions.get(discussion_id)
    
    def get_task(self, task_id):
        """
        Get a task by ID.
        
        Args:
            task_id (str): ID of the task.
            
        Returns:
            dict: Task data, or None if not found.
        """
        return self.tasks.get(task_id)
    
    def get_all_tasks(self):
        """
        Get all tasks.
        
        Returns:
            dict: Dictionary of task_id -> task.
        """
        return self.tasks
