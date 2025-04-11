from enum import Enum
from typing import Any, List, Literal, Optional, Union


class AgentState(str, Enum):
    """Agent execution states"""

    IDLE = "IDLE"       #空闲
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    ERROR = "ERROR"
    

class Role(str, Enum):
    """Message role options"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


ROLE_VALUES = tuple(role.value for role in Role)
ROLE_TYPE = Literal[ROLE_VALUES]  # type: ignore


class ToolChoice(str, Enum):
    """Tool choice options"""

    NONE = "none"
    AUTO = "auto"
    REQUIRED = "required"


TOOL_CHOICE_VALUES = tuple(choice.value for choice in ToolChoice)
TOOL_CHOICE_TYPE = Literal[TOOL_CHOICE_VALUES]  # type: ignore

class AgentType(str, Enum):
    """Agent Type options"""

    BASE = "base"           #基础能力
    #ADMIN = "admin"         #管理者
    RESEARCH = "research"   #探索
    PLANNING = "planning"   #规划
    EXECUTION = "execution" #执行
    CRITIC = "critic"       #评价
    
AGENT_TYPE_VALUES  = tuple(agent_type.value for agent_type in AgentType if agent_type.value !='base')
AGENT_TYPE_TYPE = Literal[AGENT_TYPE_VALUES]  # type: ignore
    