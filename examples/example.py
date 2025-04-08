"""
Example usage of the CallAgent project.
"""

import time
from app.config import DATABASE_PATH
from app.database.db_manager import DatabaseManager
from app.communication.agent_hub import AgentHub
from app.agents.agent_factory import AgentFactory
from app.planning.task_planner import TaskPlanner
from app.planning.plan_executor import PlanExecutor
from app.utils.logger import Logger


def main():
    """
    Main entry point for the example.
    """
    # Set up the logger
    logger = Logger("CallAgentExample")
    logger.info("Starting CallAgent Example")
    
    # Set up the database
    db_path = DATABASE_PATH
    db_manager = DatabaseManager(db_path)
    db_manager.init_db()
    logger.info(f"Database set up at {db_path}")
    
    # Create agents
    agent_factory = AgentFactory(db_path)
    
    # Create a research agent
    research_agent = agent_factory.create_research_agent(
        name="Research Agent",
        expertise=["artificial intelligence", "machine learning", "data analysis"]
    )
    logger.info(f"Created research agent: {research_agent.agent_id}")
    
    # Create a planning agent
    planning_agent = agent_factory.create_planning_agent(
        name="Planning Agent"
    )
    logger.info(f"Created planning agent: {planning_agent.agent_id}")
    
    # Create an execution agent
    execution_agent = agent_factory.create_execution_agent(
        name="Execution Agent",
        skills=["coding", "data processing", "report generation"]
    )
    logger.info(f"Created execution agent: {execution_agent.agent_id}")
    
    # Create a critic agent
    critic_agent = agent_factory.create_critic_agent(
        name="Critic Agent"
    )
    logger.info(f"Created critic agent: {critic_agent.agent_id}")
    
    # Set up the agent hub
    agent_hub = AgentHub(db_path)
    
    # Register agents with the hub
    agent_hub.register_agent(research_agent)
    agent_hub.register_agent(planning_agent)
    agent_hub.register_agent(execution_agent)
    agent_hub.register_agent(critic_agent)
    logger.info("Registered agents with the hub")
    
    # Override the send_message method of each agent to use the agent hub
    def create_send_message_wrapper(agent_id):
        def send_message_wrapper(recipient_id, message):
            return agent_hub.send_message(agent_id, recipient_id, message)
        return send_message_wrapper
    
    research_agent.send_message = create_send_message_wrapper(research_agent.agent_id)
    planning_agent.send_message = create_send_message_wrapper(planning_agent.agent_id)
    execution_agent.send_message = create_send_message_wrapper(execution_agent.agent_id)
    critic_agent.send_message = create_send_message_wrapper(critic_agent.agent_id)
    
    # Set up the task planner
    task_planner = TaskPlanner(agent_hub, db_path)
    logger.info("Task planner set up")
    
    # Set up the plan executor
    plan_executor = PlanExecutor(agent_hub, db_path)
    logger.info("Plan executor set up")
    
    # Example 1: Direct agent communication
    print("\n=== Example 1: Direct Agent Communication ===")
    
    # Research agent sends a message to the planning agent
    message = "I've gathered data on recent AI advancements. What should we do with this information?"
    print(f"Research Agent -> Planning Agent: {message}")
    
    response = research_agent.send_message(planning_agent.agent_id, message)
    print(f"Planning Agent -> Research Agent: {response}")
    
    # Planning agent sends a message to the execution agent
    message = "We need to implement a data analysis pipeline for the AI research data."
    print(f"Planning Agent -> Execution Agent: {message}")
    
    response = planning_agent.send_message(execution_agent.agent_id, message)
    print(f"Execution Agent -> Planning Agent: {response}")
    
    # Execution agent sends a message to the critic agent
    message = "I've implemented the data analysis pipeline. Can you review it?"
    print(f"Execution Agent -> Critic Agent: {message}")
    
    response = execution_agent.send_message(critic_agent.agent_id, message)
    print(f"Critic Agent -> Execution Agent: {response}")
    
    # Example 2: Task planning and execution
    print("\n=== Example 2: Task Planning and Execution ===")
    
    # Create a task
    task_description = "Analyze recent trends in artificial intelligence and prepare a summary report."
    task_id = task_planner.create_task(task_description)
    print(f"Created task: {task_id}")
    
    # Decompose the task into subtasks
    subtasks = [
        "Gather data on recent AI advancements",
        "Analyze the data to identify trends",
        "Prepare a summary report of the findings",
        "Review and finalize the report"
    ]
    subtask_ids = task_planner.decompose_task(task_id, subtasks)
    print(f"Decomposed task into {len(subtask_ids)} subtasks")
    
    # Assign subtasks to agents
    task_planner.assign_subtask(task_id, 0, research_agent.agent_id)
    task_planner.assign_subtask(task_id, 1, research_agent.agent_id)
    task_planner.assign_subtask(task_id, 2, execution_agent.agent_id)
    task_planner.assign_subtask(task_id, 3, critic_agent.agent_id)
    print("Assigned subtasks to agents")
    
    # Execute the first subtask
    print("\nExecuting subtask 1:")
    result = task_planner.execute_subtask(task_id, 0)
    print(f"Result: {result}")
    
    # Execute the second subtask
    print("\nExecuting subtask 2:")
    result = task_planner.execute_subtask(task_id, 1)
    print(f"Result: {result}")
    
    # Execute the third subtask
    print("\nExecuting subtask 3:")
    result = task_planner.execute_subtask(task_id, 2)
    print(f"Result: {result}")
    
    # Execute the fourth subtask
    print("\nExecuting subtask 4:")
    result = task_planner.execute_subtask(task_id, 3)
    print(f"Result: {result}")
    
    # Example 3: Collaborative plan execution
    print("\n=== Example 3: Collaborative Plan Execution ===")
    
    # Create a plan
    plan_id = f"plan_{int(time.time())}"
    steps = [
        "Research the latest advancements in natural language processing",
        "Analyze the impact of these advancements on the field of AI",
        "Implement a prototype demonstrating one of these advancements",
        "Evaluate the performance of the prototype",
        "Prepare a report on the findings"
    ]
    
    # Assign steps to agents
    agent_assignments = {
        0: research_agent.agent_id,  # Research step
        1: research_agent.agent_id,  # Analysis step
        2: execution_agent.agent_id, # Implementation step
        3: critic_agent.agent_id,    # Evaluation step
        4: execution_agent.agent_id  # Report step
    }
    
    print(f"Created plan with {len(steps)} steps")
    print("Assigned steps to agents")
    
    # Execute the collaborative plan
    print("\nExecuting collaborative plan:")
    results = plan_executor.execute_collaborative_plan(plan_id, steps, agent_assignments)
    
    for i, result in enumerate(results):
        print(f"\nStep {i+1} result:")
        print(result)
    
    # Get conversation history
    print("\n=== Conversation History ===")
    
    history = agent_hub.get_conversation_history(limit=10)
    for entry in history:
        print(f"{entry[1]} -> {entry[2]}: {entry[3]}")
    
    logger.info("CallAgent Example finished")


if __name__ == "__main__":
    main()
