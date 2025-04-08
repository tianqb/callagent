"""
Agent factory for the CallAgent project.
Creates and manages different types of agents.
"""

import uuid
from .base_agent import BaseAgent
from .specialized_agent import ResearchAgent, PlanningAgent, ExecutionAgent, CriticAgent
from ..config import DATABASE_PATH


class AgentFactory:
    """
    Factory class for creating and managing agents.
    """

    def __init__(self, db_path=None):
        """
        Initialize the agent factory.

        Args:
            db_path (str, optional): Path to the SQLite database file.
        """
        self.db_path = db_path or DATABASE_PATH
        self.agents = {}

    def create_agent(self, agent_type, agent_id=None, name=None, **kwargs):
        """
        Create an agent of the specified type.

        Args:
            agent_type (str): Type of agent to create ('base', 'research', 'planning', 'execution', 'critic').
            agent_id (str, optional): ID of the agent. If None, a random ID is generated.
            name (str, optional): Name of the agent. If None, a default name is used.
            **kwargs: Additional arguments to pass to the agent constructor.

        Returns:
            BaseAgent: The created agent.

        Raises:
            ValueError: If the agent type is not supported.
        """
        if agent_id is None:
            agent_id = f"agent_{uuid.uuid4().hex[:8]}"

        if agent_type == 'base':
            agent = BaseAgent(agent_id=agent_id, name=name, db_path=self.db_path, **kwargs)
        elif agent_type == 'research':
            agent = ResearchAgent(agent_id=agent_id, name=name, db_path=self.db_path, **kwargs)
        elif agent_type == 'planning':
            agent = PlanningAgent(agent_id=agent_id, name=name, db_path=self.db_path, **kwargs)
        elif agent_type == 'execution':
            agent = ExecutionAgent(agent_id=agent_id, name=name, db_path=self.db_path, **kwargs)
        elif agent_type == 'critic':
            agent = CriticAgent(agent_id=agent_id, name=name, db_path=self.db_path, **kwargs)
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")

        self.agents[agent_id] = agent
        return agent

    def get_agent(self, agent_id):
        """
        Get an agent by ID.

        Args:
            agent_id (str): ID of the agent to get.

        Returns:
            BaseAgent: The agent, or None if not found.
        """
        return self.agents.get(agent_id)

    def get_all_agents(self):
        """
        Get all agents.

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
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False

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
            agent_types = ['research', 'planning', 'execution', 'critic']

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

    def create_research_agent(self, name=None, expertise=None):
        """
        Create a research agent.

        Args:
            name (str, optional): Name of the agent. If None, a default name is used.
            expertise (list, optional): List of areas of expertise.

        Returns:
            ResearchAgent: The created agent.
        """
        return self.create_agent('research', name=name, expertise=expertise)

    def create_planning_agent(self, name=None):
        """
        Create a planning agent.

        Args:
            name (str, optional): Name of the agent. If None, a default name is used.

        Returns:
            PlanningAgent: The created agent.
        """
        return self.create_agent('planning', name=name)

    def create_execution_agent(self, name=None, skills=None):
        """
        Create an execution agent.

        Args:
            name (str, optional): Name of the agent. If None, a default name is used.
            skills (list, optional): List of skills.

        Returns:
            ExecutionAgent: The created agent.
        """
        return self.create_agent('execution', name=name, skills=skills)

    def create_critic_agent(self, name=None):
        """
        Create a critic agent.

        Args:
            name (str, optional): Name of the agent. If None, a default name is used.

        Returns:
            CriticAgent: The created agent.
        """
        return self.create_agent('critic', name=name)
