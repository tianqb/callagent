"""
Example usage of the AgentHub with admin functionality in the CallAgent project.
This example demonstrates how the AgentHub coordinates agents
and ensures high-quality output through iterative refinement.
"""
import os
import sys
import asyncio
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app.agents.agent_hub import AgentHub
from app.utils.logger import Logger


async def main():
    """
    Main entry point for the agent hub admin example.
    """
    # Set up the logger
    logger = Logger("AgentHubExample")
    logger.info("Starting AgentHub Example")
    
    # Create the agent hub
    agent_hub = AgentHub()
    logger.info("Created agent hub")
    
    # Initialize the team of agents
    managed_agents = await agent_hub.initialize_team()
    logger.info(f"Initialized team with {len(managed_agents)} agents")
    
    # Print the managed agents
    print("\n=== Managed Agents ===")
    for agent_type, agent in managed_agents.items():
        print(f"{agent_type}: {agent.name} ({agent.agent_id})")
    
    # Example 1: Simple task execution
    print("\n=== Example 1: Simple Task Execution ===")
    
    # Create and execute a task
    task_description = "Analyze recent trends in artificial intelligence and prepare a summary report."
    task_id = await agent_hub.create_task(task_description)
    print(f"Created task: {task_id}")
    
    # Execute the task
    print("\nExecuting task...")
    results = await agent_hub.execute_task(task_id)
    
    # Print the results from each agent
    print("\nTask Results:")
    for agent_type, result in results.items():
        print(f"\n{agent_type.upper()} RESULT:")
        print(result)
    
    # Get the quality score
    quality_score = agent_hub.tasks[task_id].get("quality_score", 0)
    print(f"\nQuality Score: {quality_score:.2f}")
    
    # Example 2: Task execution with quality improvement
    print("\n=== Example 2: Task Execution with Quality Improvement ===")
    
    # Create a more complex task
    task_description = "Design a machine learning system for predicting stock market trends."
    task_id = await agent_hub.create_task(task_description)
    print(f"Created task: {task_id}")
    
    # Execute the task with quality improvement
    print("\nExecuting task with quality improvement...")
    results = await agent_hub.improve_task_results(
        task_id, 
        min_quality_score=0.8,
        max_iterations=3
    )
    
    # Print the final results after improvement
    print("\nFinal Task Results after Improvement:")
    for agent_type, result in results.items():
        print(f"\n{agent_type.upper()} RESULT:")
        print(result)
    
    # Get the quality score and iterations
    quality_score = agent_hub.tasks[task_id].get("quality_score", 0)
    iterations = agent_hub.tasks[task_id].get("iterations", 0)
    print(f"\nFinal Quality Score: {quality_score:.2f} (after {iterations} iterations)")
    
    # Example 3: Examining discussions
    print("\n=== Example 3: Examining Agent Discussions ===")
    
    # Get all discussions
    discussions = agent_hub.discussions
    print(f"Number of discussions: {len(discussions)}")
    
    # Print details of the last discussion
    if discussions:
        last_discussion_id = list(discussions.keys())[-1]
        discussion = discussions[last_discussion_id]
        
        print(f"\nDiscussion ID: {last_discussion_id}")
        print(f"Task ID: {discussion['task_id']}")
        print(f"Started at: {discussion['started_at']}")
        print(f"Active: {discussion['active']}")
        
        print("\nDiscussion Messages:")
        for i, message in enumerate(discussion['messages']):
            sender = message['sender_id']
            recipient = message['recipient_id']
            content = message['message']
            
            # Truncate long messages for display
            if len(content) > 100:
                content = content[:100] + "..."
            
            print(f"{i+1}. {sender} -> {recipient}: {content}")
    
    logger.info("AgentHub Example finished")


if __name__ == "__main__":
    asyncio.run(main())
