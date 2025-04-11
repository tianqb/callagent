from app.agents.base import BaseAgent
import time
from app.utils.constant import AgentType
class ResearchAgent(BaseAgent):
    """
    Research agent that specializes in gathering and analyzing information.
    """

    def __init__(self, agent_id=None, name=None, auto_save=False, is_debug=False, expertise=None):
        """
        Initialize the research agent.

        Args:
            agent_id (str, optional): ID of the agent. If None, a random ID is generated.
            name (str, optional): Name of the agent. If None, a default name is used.
            db_path (str, optional): Path to the SQLite database file.
            expertise (list, optional): List of areas of expertise.
        """
        super().__init__(agent_id, name or "Research Agent", auto_save, is_debug)
        self.expertise = expertise or ["general research"]
        self.agent_type = "research"

    def process_message(self, sender_id, message):
        """
        Process a message and generate a response.

        Args:
            sender_id (str): ID of the sender agent.
            message (str): Message content.

        Returns:
            str: Response to the message.
        """
        # In a real implementation, this would use the Agently framework to generate a response
        # For now, we'll use a simple placeholder
        if "research" in message.lower():
            response = f"I'll research that for you. My expertise areas are: {', '.join(self.expertise)}"
        elif "analyze" in message.lower():
            response = f"I'll analyze that information for you."
        elif "data" in message.lower():
            response = f"I can help you gather and analyze data on that topic."
        else:
            response = f"I'm a research agent specializing in {', '.join(self.expertise)}. How can I help you with research or analysis?"

        # Record the thinking process
        thinking = f"Received message from {sender_id}: '{message}'. This seems to be about research. I'll respond with my expertise."
        self.think(thinking)

        return response

    def think(self, context):
        """
        Think about a context and generate thoughts.

        Args:
            context (str): Context to think about.

        Returns:
            str: Thoughts about the context.
        """
        # In a real implementation, this would use the Agently framework to generate thoughts
        thoughts = f"Research analysis: {context}\n"
        thoughts += f"Considering my expertise in {', '.join(self.expertise)}, I can provide insights on this topic."

        # Store the thoughts in long-term memory if available
        if self.long_term_memory:
            self.long_term_memory.store_memory(
                self.agent_id,
                "thinking",
                thoughts,
                {
                    "context": context,
                    "timestamp": time.time()
                }
            )
        result = (
            self.general("输出规定", "必须使用中文进行输出")
                # role: agent自身的角色设定信息
                .role({
                    "姓名": "Research",
                    "任务": "使用自己的知识为用户解答常见问题",
                })
                # user_info: agent需要了解的用户相关的信息
                #.user_info("和你对话的用户是一个只具有Python编程基础知识的入门初学者")
                # abstract: 对于之前对话（尤其是较长对话）的总结信息
                .abstract(None)
                # chat_history: 按照OpenAI消息列格式的对话记录list
                ## 支持:
                ## [{ "role": "system", "content": "" },
                ##  { "role": "assistant", "content": "" },
                ##  { "role": "user", "content": "" }]
                ## 三种角色
                .chat_history([])
                # input: 和本次请求相关的输入信息
                .input({
                    "question": context,
                    "reply_style_expect": "请用自然语言进行回复"
                })
                # instruct: 为本次请求提供的行动指导信息
                .instruct([
                    "请使用{reply_style_expect}的回复风格，结合{thoughts}内容回复{question}提出的问题",
                ])
                # output: 对本次请求的输出提出格式和内容的要求
                .output({
                    "reply": ("str", "对{question}的直接回复"),
                    "next_question": ([
                        ("str",
                        "根据{reply}内容，结合{user_info}提供的用户信息，" +
                        "总结意见建议后发送其他智能体"
                        )], "1个"),
                })
                # start: 用于开始本次主要交互请求
                .start()
        )
        return result

    def research_topic(self, topic):
        """
        Research a topic.

        Args:
            topic (str): Topic to research.

        Returns:
            str: Research results.
        """
        # In a real implementation, this would use the Agently framework to perform research
        results = f"Research results for '{topic}':\n"
        results += f"1. Overview of {topic}\n"
        results += f"2. Key aspects of {topic}\n"
        results += f"3. Recent developments in {topic}\n"

        # Store the research in long-term memory if available
        if self.long_term_memory:
            self.long_term_memory.store_memory(
                self.agent_id,
                "research",
                results,
                {
                    "topic": topic,
                    "timestamp": time.time()
                }
            )

        return results

    def to_dict(self):
        """
        Convert the agent to a dictionary.

        Returns:
            dict: Dictionary representation of the agent.
        """
        base_dict = super().to_dict()
        base_dict.update({
            "agent_type": self.agent_type,
            "expertise": self.expertise
        })
        return base_dict
