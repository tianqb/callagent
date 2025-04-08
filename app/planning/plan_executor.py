"""
Plan executor for the CallAgent project.
Executes plans created by the task planner.
"""

import json
import time
from ..database.db_manager import DatabaseManager


class PlanExecutor:
    """
    Plan executor that executes plans created by the task planner.
    """

    def __init__(self, agent_hub, db_path):
        """
        Initialize the plan executor.

        Args:
            agent_hub: Agent hub for communication between agents.
            db_path (str): Path to the SQLite database file.
        """
        self.agent_hub = agent_hub
        self.db_path = db_path
        self.db_manager = DatabaseManager(db_path)
        self.executions = {}

    def execute_plan(self, plan_id, plan_content, agent_id=None):
        """
        Execute a plan.

        Args:
            plan_id (str): ID of the plan.
            plan_content (str): Content of the plan.
            agent_id (str, optional): ID of the agent to execute the plan. If None, a suitable agent is selected.

        Returns:
            str: Result of executing the plan.
        """
        # Create an execution record
        execution_id = f"exec_{int(time.time())}"
        
        # If no agent is specified, find a suitable execution agent
        if agent_id is None:
            # Get all agents
            agents = self.agent_hub.get_all_agents()
            
            # Find an execution agent
            for aid, agent in agents.items():
                if hasattr(agent, 'agent_type') and agent.agent_type == 'execution':
                    agent_id = aid
                    break
            
            # If no execution agent is found, use the first available agent
            if agent_id is None and agents:
                agent_id = list(agents.keys())[0]
        
        # If still no agent is found, return an error
        if agent_id is None:
            return "No agent available to execute the plan"
        
        # Record the execution start in the database
        self.db_manager.record_planning(
            task_id=plan_id,
            agent_id=agent_id,
            plan_type="execution_start",
            content=f"Starting execution of plan: {plan_content[:100]}...",
            status="in_progress"
        )
        
        # Store the execution in memory
        self.executions[execution_id] = {
            "plan_id": plan_id,
            "agent_id": agent_id,
            "status": "in_progress",
            "started_at": time.time()
        }
        
        # Send the plan to the agent for execution
        message = f"Execute plan: {plan_content}"
        result = self.agent_hub.send_message("system", agent_id, message)
        
        # Record the execution result in the database
        self.db_manager.record_planning(
            task_id=plan_id,
            agent_id=agent_id,
            plan_type="execution_result",
            content=result,
            status="completed"
        )
        
        # Update the execution in memory
        self.executions[execution_id].update({
            "status": "completed",
            "result": result,
            "completed_at": time.time()
        })
        
        return result

    def execute_plan_steps(self, plan_id, steps, agent_id=None):
        """
        Execute a plan step by step.

        Args:
            plan_id (str): ID of the plan.
            steps (list): List of step descriptions.
            agent_id (str, optional): ID of the agent to execute the plan. If None, a suitable agent is selected.

        Returns:
            list: List of step execution results.
        """
        # Create an execution record
        execution_id = f"exec_{int(time.time())}"
        
        # If no agent is specified, find a suitable execution agent
        if agent_id is None:
            # Get all agents
            agents = self.agent_hub.get_all_agents()
            
            # Find an execution agent
            for aid, agent in agents.items():
                if hasattr(agent, 'agent_type') and agent.agent_type == 'execution':
                    agent_id = aid
                    break
            
            # If no execution agent is found, use the first available agent
            if agent_id is None and agents:
                agent_id = list(agents.keys())[0]
        
        # If still no agent is found, return an error
        if agent_id is None:
            return ["No agent available to execute the plan"]
        
        # Record the execution start in the database
        self.db_manager.record_planning(
            task_id=plan_id,
            agent_id=agent_id,
            plan_type="execution_start",
            content=f"Starting execution of plan with {len(steps)} steps",
            status="in_progress"
        )
        
        # Store the execution in memory
        self.executions[execution_id] = {
            "plan_id": plan_id,
            "agent_id": agent_id,
            "status": "in_progress",
            "steps": [],
            "started_at": time.time()
        }
        
        # Execute each step
        results = []
        for i, step in enumerate(steps):
            # Record the step start in the database
            step_id = f"{plan_id}_step_{i}"
            self.db_manager.record_planning(
                task_id=step_id,
                agent_id=agent_id,
                plan_type="step_start",
                content=f"Starting step {i+1}: {step}",
                status="in_progress"
            )
            
            # Send the step to the agent for execution
            message = f"Execute step {i+1} of {len(steps)}: {step}"
            result = self.agent_hub.send_message("system", agent_id, message)
            results.append(result)
            
            # Record the step result in the database
            self.db_manager.record_planning(
                task_id=step_id,
                agent_id=agent_id,
                plan_type="step_result",
                content=result,
                status="completed"
            )
            
            # Store the step result in memory
            self.executions[execution_id]["steps"].append({
                "step_id": step_id,
                "description": step,
                "result": result,
                "completed_at": time.time()
            })
        
        # Record the execution completion in the database
        self.db_manager.record_planning(
            task_id=plan_id,
            agent_id=agent_id,
            plan_type="execution_complete",
            content=f"Completed execution of plan with {len(steps)} steps",
            status="completed"
        )
        
        # Update the execution in memory
        self.executions[execution_id].update({
            "status": "completed",
            "completed_at": time.time()
        })
        
        return results

    def execute_collaborative_plan(self, plan_id, steps, agent_assignments):
        """
        Execute a plan collaboratively with multiple agents.

        Args:
            plan_id (str): ID of the plan.
            steps (list): List of step descriptions.
            agent_assignments (dict): Dictionary of step_index -> agent_id.

        Returns:
            list: List of step execution results.
        """
        # Create an execution record
        execution_id = f"exec_{int(time.time())}"
        
        # Record the execution start in the database
        self.db_manager.record_planning(
            task_id=plan_id,
            agent_id="system",
            plan_type="collaborative_execution_start",
            content=f"Starting collaborative execution of plan with {len(steps)} steps",
            status="in_progress"
        )
        
        # Store the execution in memory
        self.executions[execution_id] = {
            "plan_id": plan_id,
            "status": "in_progress",
            "steps": [],
            "started_at": time.time()
        }
        
        # Execute each step
        results = []
        for i, step in enumerate(steps):
            # Get the assigned agent for this step
            agent_id = agent_assignments.get(i)
            
            # If no agent is assigned for this step, skip it
            if agent_id is None:
                results.append(f"No agent assigned for step {i+1}")
                continue
            
            # Record the step start in the database
            step_id = f"{plan_id}_step_{i}"
            self.db_manager.record_planning(
                task_id=step_id,
                agent_id=agent_id,
                plan_type="step_start",
                content=f"Starting step {i+1}: {step}",
                status="in_progress"
            )
            
            # Send the step to the agent for execution
            message = f"Execute step {i+1} of {len(steps)}: {step}"
            result = self.agent_hub.send_message("system", agent_id, message)
            results.append(result)
            
            # Record the step result in the database
            self.db_manager.record_planning(
                task_id=step_id,
                agent_id=agent_id,
                plan_type="step_result",
                content=result,
                status="completed"
            )
            
            # Store the step result in memory
            self.executions[execution_id]["steps"].append({
                "step_id": step_id,
                "description": step,
                "agent_id": agent_id,
                "result": result,
                "completed_at": time.time()
            })
        
        # Record the execution completion in the database
        self.db_manager.record_planning(
            task_id=plan_id,
            agent_id="system",
            plan_type="collaborative_execution_complete",
            content=f"Completed collaborative execution of plan with {len(steps)} steps",
            status="completed"
        )
        
        # Update the execution in memory
        self.executions[execution_id].update({
            "status": "completed",
            "completed_at": time.time()
        })
        
        return results

    def get_execution(self, execution_id):
        """
        Get an execution by ID.

        Args:
            execution_id (str): ID of the execution.

        Returns:
            dict: Execution data, or None if not found.
        """
        return self.executions.get(execution_id)

    def get_all_executions(self):
        """
        Get all executions.

        Returns:
            dict: Dictionary of execution_id -> execution.
        """
        return self.executions

    def get_plan_executions(self, plan_id):
        """
        Get all executions for a plan.

        Args:
            plan_id (str): ID of the plan.

        Returns:
            list: List of executions for the plan.
        """
        return [
            execution for execution_id, execution in self.executions.items()
            if execution.get("plan_id") == plan_id
        ]

    def get_agent_executions(self, agent_id):
        """
        Get all executions by an agent.

        Args:
            agent_id (str): ID of the agent.

        Returns:
            list: List of executions by the agent.
        """
        return [
            execution for execution_id, execution in self.executions.items()
            if execution.get("agent_id") == agent_id
        ]

    def to_dict(self):
        """
        Convert the plan executor to a dictionary.

        Returns:
            dict: Dictionary representation of the plan executor.
        """
        return {
            "executions_count": len(self.executions),
            "executions": self.executions
        }

    def to_json(self):
        """
        Convert the plan executor to a JSON string.

        Returns:
            str: JSON representation of the plan executor.
        """
        return json.dumps(self.to_dict())
