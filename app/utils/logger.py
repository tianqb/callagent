"""
Logger for the CallAgent project.
Provides logging functionality.
"""

import logging
import os
import time
from datetime import datetime
from ..config import LOG_LEVEL, LOG_FILE


class Logger:
    """
    Logger class for the CallAgent project.
    """

    def __init__(self, name, log_level=None, log_file=None):
        """
        Initialize the logger.

        Args:
            name (str): Name of the logger.
            log_level (str, optional): Log level. If None, the default log level from config is used.
            log_file (str, optional): Path to the log file. If None, the default log file from config is used.
        """
        self.name = name
        self.log_level = log_level or LOG_LEVEL
        self.log_file = log_file or LOG_FILE
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self._get_log_level())
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self._get_log_level())
        console_handler.setFormatter(formatter)
        
        # Create file handler if log file is specified
        if self.log_file:
            # Create directory if it doesn't exist
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(self._get_log_level())
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Add handlers to logger
        self.logger.addHandler(console_handler)

    def _get_log_level(self):
        """
        Get the log level.

        Returns:
            int: Log level.
        """
        level = self.log_level.upper()
        if level == 'DEBUG':
            return logging.DEBUG
        elif level == 'INFO':
            return logging.INFO
        elif level == 'WARNING':
            return logging.WARNING
        elif level == 'ERROR':
            return logging.ERROR
        elif level == 'CRITICAL':
            return logging.CRITICAL
        else:
            return logging.INFO

    def debug(self, message):
        """
        Log a debug message.

        Args:
            message (str): Message to log.
        """
        self.logger.debug(message)

    def info(self, message):
        """
        Log an info message.

        Args:
            message (str): Message to log.
        """
        self.logger.info(message)

    def warning(self, message):
        """
        Log a warning message.

        Args:
            message (str): Message to log.
        """
        self.logger.warning(message)

    def error(self, message):
        """
        Log an error message.

        Args:
            message (str): Message to log.
        """
        self.logger.error(message)

    def critical(self, message):
        """
        Log a critical message.

        Args:
            message (str): Message to log.
        """
        self.logger.critical(message)

    def log_agent_message(self, sender_id, recipient_id, message):
        """
        Log an agent message.

        Args:
            sender_id (str): ID of the sender agent.
            recipient_id (str): ID of the recipient agent.
            message (str): Message content.
        """
        self.info(f"Agent message: {sender_id} -> {recipient_id}: {message}")

    def log_agent_thinking(self, agent_id, thinking):
        """
        Log agent thinking.

        Args:
            agent_id (str): ID of the agent.
            thinking (str): Thinking content.
        """
        self.debug(f"Agent thinking: {agent_id}: {thinking}")

    def log_agent_planning(self, agent_id, planning):
        """
        Log agent planning.

        Args:
            agent_id (str): ID of the agent.
            planning (str): Planning content.
        """
        self.debug(f"Agent planning: {agent_id}: {planning}")

    def log_agent_execution(self, agent_id, execution):
        """
        Log agent execution.

        Args:
            agent_id (str): ID of the agent.
            execution (str): Execution content.
        """
        self.debug(f"Agent execution: {agent_id}: {execution}")

    def log_task_creation(self, task_id, description, creator_id):
        """
        Log task creation.

        Args:
            task_id (str): ID of the task.
            description (str): Description of the task.
            creator_id (str): ID of the creator agent.
        """
        self.info(f"Task created: {task_id} by {creator_id}: {description}")

    def log_task_assignment(self, task_id, agent_id):
        """
        Log task assignment.

        Args:
            task_id (str): ID of the task.
            agent_id (str): ID of the agent.
        """
        self.info(f"Task assigned: {task_id} to {agent_id}")

    def log_task_execution(self, task_id, agent_id, result):
        """
        Log task execution.

        Args:
            task_id (str): ID of the task.
            agent_id (str): ID of the agent.
            result (str): Execution result.
        """
        self.info(f"Task executed: {task_id} by {agent_id}: {result[:100]}...")

    def log_memory_store(self, agent_id, memory_type, content):
        """
        Log memory storage.

        Args:
            agent_id (str): ID of the agent.
            memory_type (str): Type of memory.
            content (str): Memory content.
        """
        self.debug(f"Memory stored: {agent_id} - {memory_type}: {content[:100]}...")

    def log_memory_retrieve(self, agent_id, memory_type, count):
        """
        Log memory retrieval.

        Args:
            agent_id (str): ID of the agent.
            memory_type (str): Type of memory.
            count (int): Number of memories retrieved.
        """
        self.debug(f"Memory retrieved: {agent_id} - {memory_type}: {count} items")

    def log_exception(self, exception):
        """
        Log an exception.

        Args:
            exception (Exception): Exception to log.
        """
        self.error(f"Exception: {str(exception)}")

    def get_log_file_path(self):
        """
        Get the path to the log file.

        Returns:
            str: Path to the log file.
        """
        return self.log_file

    def create_session_log(self):
        """
        Create a session log file.

        Returns:
            str: Path to the session log file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_log_file = f"session_{timestamp}.log"
        
        # If log_file is specified, use its directory
        if self.log_file:
            log_dir = os.path.dirname(self.log_file)
            if log_dir:
                session_log_file = os.path.join(log_dir, session_log_file)
        
        # Create a new logger for the session
        session_logger = Logger(
            f"{self.name}_session_{timestamp}",
            self.log_level,
            session_log_file
        )
        
        session_logger.info(f"Session started at {timestamp}")
        return session_log_file
