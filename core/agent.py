from dotenv import load_dotenv
import os

import langchain
from langchain.agents import create_agent

class OrderAgent:
    def __init__(self):
        # This is where you will eventually initialize LLMs, Memory, and Tools
        print("Initializing Agent...")
        load_dotenv()  # Load environment variables from a .env file
        os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
        
        self.agent = create_agent(
            model="llama-2-70b-chat",
            tools=[],
            system_prompt="You're an order-taking agent for a restaurant. Help customers place their orders clearly and concisely.",
        )

    def get_response(self, user_text):
        """
        Input: user_text (str)
        Output: response (str)
        """
        response = self.agent.invoke({"messages": [{"role": "user", "content": user_text}]})
        return response["messages"][-1]["content"]
