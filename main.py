"""
Main entry point for the CallAgent project.
"""

import os
import sys
import argparse
import time
import json

from app.database.db_manager import DatabaseManager
from app.memory.short_term import ShortTermMemory
from app.memory.long_term import LongTermMemory
from app.communication.agent_hub import AgentHub
from app.communication.conversation import ConversationManager
from app.agents.agent_factory import AgentFactory
from app.planning.task_planner import TaskPlanner
from app.planning.plan_executor import PlanExecutor
from app.utils.logger import Logger
from app.utils.helpers import save_json, load_json, extract_task_steps


def setup_database():
    """
    Set up the database.

    Returns:
        DatabaseManager: Database manager.
    """
    db_manager = DatabaseManager()
    db_manager.init_db()
    return db_manager


def create_agents(db_path, agent_types=None):
    """
    Create agents.

    Args:
        db_path (str): Path to the SQLite database file.
        agent_types (list, optional): List of agent types to create.

    Returns:
        tuple: (AgentFactory, dict) - Agent factory and dictionary of agent_id -> agent.
    """
    agent_factory = AgentFactory()
    
    if agent_types is None:
        agent_types = ['research', 'planning', 'execution', 'critic']
    
    agents = {}
    for agent_type in agent_types:
        agent = agent_factory.create_agent(agent_type)
        agents[agent.agent_id] = agent
    
    return agent_factory, agents


def setup_agent_hub(agents):
    """
    Set up the agent hub.

    Args:
        db_path (str): Path to the SQLite database file.
        agents (dict): Dictionary of agent_id -> agent.

    Returns:
        AgentHub: Agent hub.
    """
    agent_hub = AgentHub()
    
    for agent_id, agent in agents.items():
        agent_hub.register_agent(agent)
        
        # Override the send_message method of the agent to use the agent hub
        def send_message_wrapper(recipient_id, message, sender_id=agent_id):
            return agent_hub.send_message(sender_id, recipient_id, message)
        
        agent.send_message = send_message_wrapper
    
    return agent_hub


def setup_task_planner(agent_hub):
    """
    Set up the task planner.

    Args:
        agent_hub (AgentHub): Agent hub.
        db_path (str): Path to the SQLite database file.

    Returns:
        TaskPlanner: Task planner.
    """
    return TaskPlanner(agent_hub)


def setup_plan_executor(agent_hub):
    """
    Set up the plan executor.

    Args:
        agent_hub (AgentHub): Agent hub.
        db_path (str): Path to the SQLite database file.

    Returns:
        PlanExecutor: Plan executor.
    """
    return PlanExecutor(agent_hub)


def setup_logger():
    """
    Set up the logger.

    Returns:
        Logger: Logger.
    """
    return Logger("CallAgent")


def parse_args():
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="CallAgent - Multi-agent communication system")
    
    parser.add_argument("--task", type=str, help="Task to execute")
    parser.add_argument("--agent-types", type=str, nargs="+", help="Agent types to create")
    parser.add_argument("--db-path", type=str, default=DATABASE_PATH, help="Path to the SQLite database file")
    parser.add_argument("--save-state", type=str, help="Path to save the state to")
    parser.add_argument("--load-state", type=str, help="Path to load the state from")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    return parser.parse_args()


def save_state(state, file_path):
    """
    Save the state to a file.

    Args:
        state (dict): State to save.
        file_path (str): Path to save the state to.

    Returns:
        bool: True if the state was saved successfully.
    """
    return save_json(state, file_path)


def load_state(file_path):
    """
    Load the state from a file.

    Args:
        file_path (str): Path to load the state from.

    Returns:
        dict: Loaded state, or None if the state couldn't be loaded.
    """
    return load_json(file_path)


def execute_task(task, agent_hub, task_planner, plan_executor, logger):
    """
    Execute a task.

    Args:
        task (str): Task to execute.
        agent_hub (AgentHub): Agent hub.
        task_planner (TaskPlanner): Task planner.
        plan_executor (PlanExecutor): Plan executor.
        logger (Logger): Logger.

    Returns:
        str: Result of executing the task.
    """
    logger.info(f"Executing task: {task}")
    
    # Get the planning agent
    planning_agent = None
    for agent_id, agent in agent_hub.agents.items():
        if hasattr(agent, 'agent_type') and agent.agent_type == 'planning':
            planning_agent = agent
            break
    
    if not planning_agent:
        logger.error("No planning agent found")
        return "No planning agent found"
    
    # Create a task
    task_id = task_planner.create_task(task, creator_id="system")
    logger.info(f"Created task: {task_id}")
    
    # Assign the task to the planning agent
    task_planner.assign_task(task_id, planning_agent.agent_id)
    logger.info(f"Assigned task to planning agent: {planning_agent.agent_id}")
    
    # Ask the planning agent to create a plan
    plan_message = f"Create a plan for the following task: {task}"
    plan_response = agent_hub.send_message("system", planning_agent.agent_id, plan_message)
    logger.info(f"Planning agent response: {plan_response}")
    
    # Extract steps from the plan
    steps = extract_task_steps(plan_response)
    logger.info(f"Extracted {len(steps)} steps from the plan")
    
    # Execute the plan
    result = plan_executor.execute_plan_steps(task_id, steps)
    logger.info(f"Executed plan with result: {result}")
    
    return result


def interactive_mode(agent_hub, task_planner, plan_executor, logger):
    """
    Run in interactive mode.

    Args:
        agent_hub (AgentHub): Agent hub.
        task_planner (TaskPlanner): Task planner.
        plan_executor (PlanExecutor): Plan executor.
        logger (Logger): Logger.
    """
    print("Welcome to CallAgent Interactive Mode")
    print("Type 'exit' to quit")
    print("Available commands:")
    print("  task <task> - Execute a task")
    print("  agents - List all agents")
    print("  send <sender_id> <recipient_id> <message> - Send a message from one agent to another")
    print("  history <agent_id> - Get conversation history for an agent")
    print("  help - Show this help message")
    
    while True:
        try:
            command = input("> ").strip()
            
            if command.lower() == 'exit':
                break
            elif command.lower() == 'help':
                print("Available commands:")
                print("  task <task> - Execute a task")
                print("  agents - List all agents")
                print("  send <sender_id> <recipient_id> <message> - Send a message from one agent to another")
                print("  history <agent_id> - Get conversation history for an agent")
                print("  help - Show this help message")
            elif command.lower() == 'agents':
                print("Available agents:")
                for agent_id, agent in agent_hub.agents.items():
                    agent_type = getattr(agent, 'agent_type', 'unknown')
                    print(f"  {agent_id} ({agent_type})")
            elif command.lower().startswith('task '):
                task = command[5:].strip()
                result = execute_task(task, agent_hub, task_planner, plan_executor, logger)
                print(f"Task result: {result}")
            elif command.lower().startswith('send '):
                parts = command[5:].strip().split(' ', 2)
                if len(parts) != 3:
                    print("Invalid command format. Use: send <sender_id> <recipient_id> <message>")
                else:
                    sender_id, recipient_id, message = parts
                    response = agent_hub.send_message(sender_id, recipient_id, message)
                    print(f"Response: {response}")
            elif command.lower().startswith('history '):
                agent_id = command[8:].strip()
                history = agent_hub.get_conversation_history(agent_id)
                print(f"Conversation history for agent {agent_id}:")
                for entry in history:
                    print(f"  {entry[1]} -> {entry[2]}: {entry[3]}")
            else:
                print(f"Unknown command: {command}")
        except Exception as e:
            print(f"Error: {str(e)}")


def main():
    """
    Main entry point.
    """
    args = parse_args()
    
    # Set up the logger
    logger = setup_logger()
    logger.info("Starting CallAgent")
    
    # Set up the database
    db_path = args.db_path
    db_manager = setup_database()
    logger.info(f"Database set up at {db_path}")
    
    # Create agents
    agent_factory, agents = create_agents(db_path, args.agent_types)
    logger.info(f"Created {len(agents)} agents")
    
    # Set up the agent hub
    agent_hub = setup_agent_hub(db_path, agents)
    logger.info("Agent hub set up")
    
    # Set up the task planner
    task_planner = setup_task_planner(agent_hub, db_path)
    logger.info("Task planner set up")
    
    # Set up the plan executor
    plan_executor = setup_plan_executor(agent_hub, db_path)
    logger.info("Plan executor set up")
    
    # Load state if specified
    if args.load_state:
        state = load_state(args.load_state)
        if state:
            logger.info(f"Loaded state from {args.load_state}")
        else:
            logger.error(f"Failed to load state from {args.load_state}")
    
    # Execute task if specified
    if args.task:
        result = execute_task(args.task, agent_hub, task_planner, plan_executor, logger)
        print(f"Task result: {result}")
    
    # Run in interactive mode if specified
    if args.interactive:
        interactive_mode(agent_hub, task_planner, plan_executor, logger)
    
    # Save state if specified
    if args.save_state:
        state = {
            "agents": {agent_id: agent.to_dict() for agent_id, agent in agents.items()},
            "tasks": task_planner.to_dict(),
            "executions": plan_executor.to_dict()
        }
        if save_state(state, args.save_state):
            logger.info(f"Saved state to {args.save_state}")
        else:
            logger.error(f"Failed to save state to {args.save_state}")
    
    logger.info("CallAgent finished")


if __name__ == "__main__":
    main()
