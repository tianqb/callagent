"""
Configuration settings for the CallAgent project.
"""

# Database configuration
DATABASE_PATH = "call_agent.db"

# Memory configuration
SHORT_TERM_MEMORY_TTL = 3600  # 1 hour in seconds

# Agent configuration
DEFAULT_AGENT_SETTINGS = {
    "temperature": 0.7,
    "max_tokens": 1000,
}

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FILE = "call_agent.log"
