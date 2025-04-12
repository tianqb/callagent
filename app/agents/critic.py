from app.agents.base import BaseAgent
import time
from app.utils.constant import AgentType

class CriticAgent(BaseAgent):
    """
    Critic agent that specializes in evaluating and providing feedback.
    """

    def __init__(self, agent_id=None, name=None, auto_save=False, is_debug=False):
        """
        Initialize the critic agent.

        Args:
            agent_id (str, optional): ID of the agent. If None, a random ID is generated.
            name (str, optional): Name of the agent. If None, a default name is used.
            db_path (str, optional): Path to the SQLite database file.
        """
        super().__init__(agent_id, name or "Critic Agent", auto_save, is_debug)
        self.agent_type = AgentType.CRITIC
        self.evaluations = {}
        

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
        if "evaluate" in message.lower():
            response = f"I'll evaluate that for you and provide feedback."
        elif "review" in message.lower():
            response = f"I can review that and give you my assessment."
        elif "feedback" in message.lower():
            response = f"I'll provide detailed feedback on that."
        else:
            response = f"I'm a critic agent. I can evaluate plans, review results, and provide constructive feedback."

        # Record the thinking process
        thinking = f"Received message from {sender_id}: '{message}'. This seems to be about evaluation. I'll offer my critical analysis."
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
        thoughts = f"Critical analysis: {context}\n"
        thoughts += f"I need to consider strengths, weaknesses, and areas for improvement."

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

        return thoughts

    def evaluate(self, content, criteria=None):
        """
        Evaluate content based on criteria.

        Args:
            content (str): Content to evaluate.
            criteria (list, optional): List of criteria to evaluate against.

        Returns:
            str: Evaluation result.
        """
        # In a real implementation, this would use the Agently framework to generate an evaluation
        eval_id = f"eval_{int(time.time())}"
        #标准->[准确、完整、清晰]
        if criteria is None:
            criteria = ["accuracy", "completeness", "clarity"]
        
        evaluation = f"Evaluation of content:\n{content[:100]}...\n\n"
        evaluation += f"Criteria:\n"
        
        for criterion in criteria:
            # Generate a random score between 1 and 5
            score = 3  # Placeholder score
            evaluation += f"- {criterion.capitalize()}: {score}/5\n"
        
        evaluation += f"\nStrengths:\n"
        evaluation += f"1. The content is well-structured.\n"
        evaluation += f"2. Key points are addressed.\n"
        
        evaluation += f"\nAreas for improvement:\n"
        evaluation += f"1. Could provide more detailed examples.\n"
        evaluation += f"2. Consider alternative perspectives.\n"

        # Store the evaluation in the evaluations dictionary
        self.evaluations[eval_id] = {
            "content": content,
            "criteria": criteria,
            "evaluation": evaluation,
            "created_at": time.time()
        }

        # Store the evaluation in long-term memory if available
        if self.long_term_memory:
            self.long_term_memory.store_memory(
                self.agent_id,
                "evaluation",
                evaluation,
                {
                    "content_sample": content[:100],
                    "criteria": criteria,
                    "eval_id": eval_id,
                    "timestamp": time.time()
                }
            )

        return evaluation

    def get_evaluation(self, eval_id):
        """
        Get an evaluation by ID.

        Args:
            eval_id (str): ID of the evaluation.

        Returns:
            dict: Evaluation data, or None if not found.
        """
        return self.evaluations.get(eval_id)

    def to_dict(self):
        """
        Convert the agent to a dictionary.

        Returns:
            dict: Dictionary representation of the agent.
        """
        base_dict = super().to_dict()
        base_dict.update({
            "agent_type": self.agent_type,
            "evaluations_count": len(self.evaluations)
        })
        return base_dict