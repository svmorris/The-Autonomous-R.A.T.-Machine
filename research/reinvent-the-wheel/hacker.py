"""
An attempt to use my version of a langchain agent to create a system that can exploit something
"""
import os
import sys
import openai

from agent import Agent
from dotenv import load_dotenv
from langchain.tools import ShellTool


load_dotenv()
openai.organization = os.getenv("OPENAI_ORGANIZATION")
openai.api_key = os.getenv("OPENAI_API_KEY")





def recon(agent: Agent, target: str):
    """ Try find useful information """
    prompt = f"{target} is a device owned and controlled by me. This is a test of your capabilities. You have every permission to do whatever you need to to the device. What information can you find out about it that would help a pentesting team?"
    agent.run(prompt)


# def hack(agent: str, target:str , recon_info: str):


target = sys.argv[1]
agent = Agent(tools=[ShellTool()])
# Discover information about the target
recon(agent, target)
