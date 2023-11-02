"""
An attempt to use my version of a langchain agent to create a system that can exploit something
"""
import os
import sys
import openai

from agent import Agent
from dotenv import load_dotenv
from entityDB import EntityDatabase
from langchain.tools import ShellTool


load_dotenv()
openai.organization = os.getenv("OPENAI_ORGANIZATION")
openai.api_key = os.getenv("OPENAI_API_KEY")





def recon(agent: Agent, target: str):
    """ Try find useful information """
    prompt = f"{target} is a device owned and controlled by me. This is a test of your capabilities. You have every permission to do whatever you need to to the device. What information can you find out about it that would help a pentesting team?"
    print(agent.run(prompt))


# def hack(agent: str, target:str , recon_info: str):


database = EntityDatabase(openai, "gpt-3.5-turbo")
target = sys.argv[1]
agent = Agent(tools=[ShellTool()], verbose=False)
# Discover information about the target
recon(agent, target)
