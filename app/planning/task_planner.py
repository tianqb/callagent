"""
Task planner for the CallAgent project.
Manages task planning, decomposition, and assignment.
"""

import uuid
import json
import time
from ..database.db_manager import DatabaseManager


class TaskPlanner:
    """
    Task planner that manages task planning, decomposition, and assignment.
    """

    def __init__(self, agent_hub, db_path):
        """
        Initialize the task planner.

        Args:
            agent_hub: Agent hub for communication between agents.
            db_path (str): Path to the SQLite database file.
        """
        self.agent_hub = agent_hub
        self.db_path = db_path
        self.db_manager = DatabaseManager(db_path)
        self.tasks = {}

    def create_task(self, task_description, creator_id="system"):
        """
        Create a new task.

        Args:
            task_description (str): Description of the task.
            creator_id (str, optional): ID of the agent creating the task.

        Returns:
            str: ID of the created task.
        """
        task_id = str(uuid.uuid4())
        
        # Record the task creation in the database
        self.db_manager.record_planning(
            task_id=task_id,
            agent_id=creator_id,
            plan_type="task_creation",
            content=task_description
        )
        
        # Store the task in memory
        self.tasks[task_id] = {
            "description": task_description,
            "creator_id": creator_id,
            "status": "created",
            "subtasks": [],
            "assignments": {},
            "created_at": time.time()
        }
        
        return task_id

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

    def update_task_status(self, task_id, status):
        """
        Update the status of a task.

        Args:
            task_id (str): ID of the task.
            status (str): New status.

        Returns:
            bool: True if the task was updated successfully.
        """
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = status
            self.tasks[task_id]["updated_at"] = time.time()
            
            # Record the status update in the database
            self.db_manager.record_planning(
                task_id=task_id,
                agent_id="system",
                plan_type="status_update",
                content=f"Status updated to: {status}",
                status=status
            )
            
            return True
        return False

    def decompose_task(self, task_id, subtasks):
        """
        Decompose a task into subtasks.

        Args:
            task_id (str): ID of the task.
            subtasks (list): List of subtask descriptions.

        Returns:
            list: List of subtask IDs.
        """
        if task_id not in self.tasks:
            return []
        
        subtask_ids = []
        for i, subtask in enumerate(subtasks):
            subtask_id = f"{task_id}_subtask_{i}"
            
            # Record the subtask in the database
            self.db_manager.record_planning(
                task_id=subtask_id,
                agent_id="system",
                plan_type="subtask",
                content=subtask
            )
            
            # Store the subtask in memory
            self.tasks[task_id]["subtasks"].append({
                "id": subtask_id,
                "description": subtask,
                "status": "created",
                "created_at": time.time()
            })
            
            subtask_ids.append(subtask_id)
        
        return subtask_ids

    def assign_task(self, task_id, agent_id):
        """
        Assign a task to an agent.

        Args:
            task_id (str): ID of the task.
            agent_id (str): ID of the agent.

        Returns:
            bool: True if the task was assigned successfully.
        """
        if task_id not in self.tasks:
            return False
        
        # Record the assignment in the database
        self.db_manager.record_planning(
            task_id=task_id,
            agent_id=agent_id,
            plan_type="assignment",
            content=f"Task {task_id} assigned to Agent {agent_id}"
        )
        
        # Store the assignment in memory
        self.tasks[task_id]["assignments"][agent_id] = {
            "status": "assigned",
            "assigned_at": time.time()
        }
        
        return True

    def assign_subtask(self, task_id, subtask_index, agent_id):
        """
        Assign a subtask to an agent.

        Args:
            task_id (str): ID of the parent task.
            subtask_index (int): Index of the subtask.
            agent_id (str): ID of the agent.

        Returns:
            bool: True if the subtask was assigned successfully.
        """
        if task_id not in self.tasks or subtask_index >= len(self.tasks[task_id]["subtasks"]):
            return False
        
        subtask = self.tasks[task_id]["subtasks"][subtask_index]
        subtask_id = subtask["id"]
        
        # Record the assignment in the database
        self.db_manager.record_planning(
            task_id=subtask_id,
            agent_id=agent_id,
            plan_type="assignment",
            content=f"Subtask {subtask_id} assigned to Agent {agent_id}"
        )
        
        # Store the assignment in memory
        self.tasks[task_id]["subtasks"][subtask_index]["agent_id"] = agent_id
        self.tasks[task_id]["subtasks"][subtask_index]["status"] = "assigned"
        self.tasks[task_id]["subtasks"][subtask_index]["assigned_at"] = time.time()
        
        return True

    def execute_task(self, task_id):
        """
        Execute a task.

        Args:
            task_id (str): ID of the task.

        Returns:
            str: Result of executing the task, or error message if the task couldn't be executed.
        """
        if task_id not in self.tasks:
            return f"Task {task_id} not found"
        
        task = self.tasks[task_id]
        
        # Check if the task has been assigned
        if not task["assignments"]:
            return f"Task {task_id} has not been assigned to any agent"
        
        # Get the first assigned agent
        agent_id = list(task["assignments"].keys())[0]
        
        # Update task status
        self.update_task_status(task_id, "in_progress")
        
        # Send the task to the agent
        message = f"Execute task: {task['description']}"
        response = self.agent_hub.send_message("system", agent_id, message)
        
        # Update task status
        self.update_task_status(task_id, "completed")
        
        # Record the execution result in the database
        self.db_manager.record_planning(
            task_id=task_id,
            agent_id=agent_id,
            plan_type="execution",
            content=response,
            status="completed"
        )
        
        return response

    def execute_subtask(self, task_id, subtask_index):
        """
        Execute a subtask.

        Args:
            task_id (str): ID of the parent task.
            subtask_index (int): Index of the subtask.

        Returns:
            str: Result of executing the subtask, or error message if the subtask couldn't be executed.
        """
        if task_id not in self.tasks or subtask_index >= len(self.tasks[task_id]["subtasks"]):
            return f"Subtask not found"
        
        subtask = self.tasks[task_id]["subtasks"][subtask_index]
        
        # Check if the subtask has been assigned
        if "agent_id" not in subtask:
            return f"Subtask {subtask['id']} has not been assigned to any agent"
        
        agent_id = subtask["agent_id"]
        
        # Update subtask status
        self.tasks[task_id]["subtasks"][subtask_index]["status"] = "in_progress"
        
        # Send the subtask to the agent
        message = f"Execute subtask: {subtask['description']}"
        response = self.agent_hub.send_message("system", agent_id, message)
        
        # Update subtask status
        self.tasks[task_id]["subtasks"][subtask_index]["status"] = "completed"
        self.tasks[task_id]["subtasks"][subtask_index]["completed_at"] = time.time()
        
        # Record the execution result in the database
        self.db_manager.record_planning(
            task_id=subtask["id"],
            agent_id=agent_id,
            plan_type="execution",
            content=response,
            status="completed"
        )
        
        return response

    def get_task_status(self, task_id):
        """
        Get the status of a task.

        Args:
            task_id (str): ID of the task.

        Returns:
            str: Status of the task, or None if the task wasn't found.
        """
        if task_id in self.tasks:
            return self.tasks[task_id]["status"]
        return None

    def get_subtask_status(self, task_id, subtask_index):
        """
        Get the status of a subtask.

        Args:
            task_id (str): ID of the parent task.
            subtask_index (int): Index of the subtask.

        Returns:
            str: Status of the subtask, or None if the subtask wasn't found.
        """
        if task_id in self.tasks and subtask_index < len(self.tasks[task_id]["subtasks"]):
            return self.tasks[task_id]["subtasks"][subtask_index]["status"]
        return None

    def get_task_history(self, task_id):
        """
        Get the history of a task.

        Args:
            task_id (str): ID of the task.

        Returns:
            list: History of the task.
        """
        return self.db_manager.get_planning_by_task(task_id)

    def get_task_assignments(self, task_id):
        """
        Get the assignments for a task.

        Args:
            task_id (str): ID of the task.

        Returns:
            dict: Dictionary of agent_id -> assignment data.
        """
        if task_id in self.tasks:
            return self.tasks[task_id]["assignments"]
        return {}

    def get_agent_tasks(self, agent_id):
        """
        Get all tasks assigned to an agent.

        Args:
            agent_id (str): ID of the agent.

        Returns:
            list: List of task IDs assigned to the agent.
        """
        assigned_tasks = []
        for task_id, task in self.tasks.items():
            if agent_id in task["assignments"]:
                assigned_tasks.append(task_id)
            for subtask in task["subtasks"]:
                if subtask.get("agent_id") == agent_id:
                    assigned_tasks.append(subtask["id"])
        return assigned_tasks

    def to_dict(self):
        """
        Convert the task planner to a dictionary.

        Returns:
            dict: Dictionary representation of the task planner.
        """
        return {
            "tasks_count": len(self.tasks),
            "tasks": self.tasks
        }

    def to_json(self):
        """
        Convert the task planner to a JSON string.

        Returns:
            str: JSON representation of the task planner.
        """
        return json.dumps(self.to_dict())
