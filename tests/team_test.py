import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from app.agents.agent_factory import AgentFactory

agentFactory = AgentFactory()
agent = agentFactory.create_research_agent('research',is_debug=True)
rr= agent.think("你是谁")
print(rr)