"""
Langchain is either not very configurable, or I
am not able to find the correct configurations.
In this case, I do what any wise programmer would do,
and re-invent the wheel. 

This code is supposed to create a langchain-like agent
with more leniancy in parsing, filtering of command outputs
and possibly re-running actions when a command fails.

Further I think its important to add a debugging mechanism
to manually accept commands before they are being run

Additional things that cross my mind:

- Maybe this llm also includes the entity memory stuff
- Also commands should run in a podman instance for added safety
- If a command output is too long, we could get an llm to summarise it

"""

import os
import re
import time
from dotenv import load_dotenv

import openai
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from enum import Enum, auto

from base_prompt import P_SYSTEM
from langchain.chains import LLMChain
from langchain.tools import ShellTool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate


class ScratchPad:
    def __init__(self):
        self.context = ""
        self.keywords = [
                r"^Thought:",
                r"^Action:",
                r"^Action Input:",
                r"^Observation:",
                r"^Finish:",
                ]
        self.states = [
                "THOUGHT",
                "ACTION",
                "ACTION INPUT",
                "OBSERVATION",
                "FINISH"
                ]
        self.state = None
        self.previous_state = None

        self.action = ""
        self.action_input = ""


    def _check_state(self):
        """ Checks the last line of the context in-case the state changed """
        lines = self.context.split("\n")

        # Find the last non-empty line
        if len(lines[-1]) > 0:
            for i,keyword in enumerate(self.keywords):
                match = re.findall(keyword, lines[-1])
                if match:
                    self.previous_state = self.state
                    self.state = self.states[i]

        if self.state != self.previous_state:
            print(f"({self.state})", flush=True, end="")


    def _action_parser(self, chunk: str) -> bool:
        #
        # chunk = chunk.strip().strip(":").strip().strip("\n").strip("Action").strip("Input").strip("Observation")
        #
        # if self.state == "ACTION":
        #     if self.previous_state != "ACTION":
        #         self.action = ""
        #     self.action += chunk
        #
        # if self.state == "ACTION INPUT":
        #     if self.previous_state != "ACTION INPUT":
        #         assert self.previous_state == "ACTION", "Previous state is not action in state action input"
        #         self.action_input = ""
        #
        #     self.action_input += chunk
        #
        # if self.state == "OBSERVATION" and self.previous_state == "ACTION INPUT":
        #     self._run_tool()
        #     return False

        return True



    def _run_tool(self):
        """ Run a tool """
        print(f"running tool: `{self.action}` with input: {self.action_input}]")


    def add_chunk(self, chunk: str) -> bool:
        print(chunk, flush=True, end="")
        if chunk is not None:
            self.context += chunk

        self._check_state()
        self._action_parser(chunk)





class Agent:
    def __init__(self, tools: list, system: str=""):
        self.tools = tools
        # self.llm = self._get_llm()
        self.p_system = self._get_system_prompt(system)


    def _get_system_prompt(self, user_system: str) -> str:
        """ Get and format the default system prompt """

        # Get all the tools formatted nice and readably
        tools_str = ""
        for tool in self.tools:
            tools_str += f"- {tool.name}: {tool.description}"

        # We allow users of the class to define their own system string.
        # If this is not set, then we set the default one
        if len(user_system) < 1:
            formatted_p_system = P_SYSTEM.format(tools=tools_str)
        else:
            return user_system

        return formatted_p_system


    def run(self, task: str):
        """ Run the agent to execute a specific task """
        prompt = f"{self.p_system}\nTask: {task}"

        scratchpad = ScratchPad()

        for chunk in openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        ):
            scratchpad.add_chunk(chunk['choices'][0].get("delta", {}).get("content"))

        print(scratchpad.context)



if __name__ == "__main__":
    load_dotenv()
    openai.organization = os.getenv("OPENAI_ORGANIZATION")
    openai.api_key = os.getenv("OPENAI_API_KEY")
    agent = Agent(tools=[ShellTool()])
    print(agent.run("Get my current IP address"))

