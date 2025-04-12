"""
Configuration settings for the CallAgent project.
"""
import threading
import tomllib
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = get_project_root()
WORKSPACE_ROOT = PROJECT_ROOT / "workspace"

# Database configuration
DATABASE_PATH = PROJECT_ROOT / "resources/call_agent.db"

# Agent configuration
DEFAULT_AGENT_SETTINGS = {
    "temperature": 0.7,
    "max_tokens": 1000,
}

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FILE = PROJECT_ROOT / "logs/call_agent.log"

class Config:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._config = None
                    self._load_config()
                    self._initialized = True

    def _get_config_path(self) -> Path:
        root = PROJECT_ROOT
        config_path = root / "config" / "config.toml"
        if config_path.exists():
            return config_path
        raise FileNotFoundError("No configuration file found in config directory")

    def _load_config(self) -> dict:
        config_path = self._get_config_path()
        with config_path.open("rb") as f:
            self._config = tomllib.load(f)
        return self._config
      
    def get_config_value(self, section, key, default=None):
        """
        Get a configuration value from the specified section and key.
        
        Args:
            section (str): The section name in the TOML file
            key (str): The key name within the section
            default: The default value to return if the key is not found
            
        Returns:
            The value from the config, or the default if not found
        """
        if not self._config:
            self._load_config()
        
        section_data = self._config.get(section, {})
        return section_data.get(key, default)

config = Config()

# Load configuration values from TOML file
DEEPSEEK_MODEL = config.get_config_value("deepseek", "model")
DEEPSEEK_BASE_URL = config.get_config_value("deepseek", "base_url")
DEEPSEEK_API_KEY = config.get_config_value("deepseek", "api_key")
DEEPSEEK_TEMPERATURE = config.get_config_value("deepseek", "temperature")

# Memory configuration
MEMORY_SHORT_TERM_TTL = config.get_config_value("memory", "short_term_ttl", 3600)

# Sandbox configuration
SANDBOX_USE = config.get_config_value("sandbox", "use_sandbox")
SANDBOX_IMAGE = config.get_config_value("sandbox", "image")
SANDBOX_WORK_DIR = config.get_config_value("sandbox", "work_dir")
SANDBOX_MEMORY_LIMIT = config.get_config_value("sandbox", "memory_limit")
SANDBOX_CPU_LIMIT = config.get_config_value("sandbox", "cpu_limit")
SANDBOX_TIMEOUT = config.get_config_value("sandbox", "timeout")
SANDBOX_NETWORK_ENABLED = config.get_config_value("sandbox", "network_enabled")

# Search configuration
# Search engine for agent to use. Default is "Google", can be set to "Baidu" or "DuckDuckGo".
SEARCH_ENGINE = config.get_config_value("search", "engine")
# Fallback engine order. Default is ["DuckDuckGo", "Baidu"] - will try in this order after primary engine fails.
SEARCH_FALLBACK_ENGINES = config.get_config_value("search", "fallback_engines")
# Seconds to wait before retrying all engines again when they all fail due to rate limits. Default is 60.
SEARCH_RETRY_DELAY = config.get_config_value("search", "retry_delay")
# Maximum number of times to retry all engines when all fail. Default is 3.
SEARCH_MAX_RETRIES = config.get_config_value("search", "max_retries")
SEARCH_LANG = config.get_config_value("search", "lang")
SEARCH_COUNTRY = config.get_config_value("search", "country")
