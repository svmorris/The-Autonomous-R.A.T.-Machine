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
- make plans?

"""

import os
import re
import time
import string
import warnings
from dotenv import load_dotenv

import openai
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from enum import Enum, auto

from prompts import P_SYSTEM
from langchain.chains import LLMChain
from langchain.tools import ShellTool
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

warnings.filterwarnings("ignore")

# For debugging some outputs
def string_to_hex(s):
    hex_output = ''
    for char in s:
        hex_output += hex(ord(char))[2:].zfill(2)  # Convert each character to hex
    return hex_output


class ScratchPad:
    def __init__(self, prompt: str = ""):
        self.context = prompt
        self.keywords = [
                r"^Thought:",
                r"^Action:",
                r"^Action Input:",
                r"^Observation:",
                r"^Finish:",
                r"^Final Answer:",
                ]
        self.states = [
                "THOUGHT",
                "ACTION",
                "ACTION INPUT",
                "OBSERVATION",
                "FINISH",
                "FINAL ANSWER"
                ]
        self.state = None
        self.previous_state = None

        self.action = ""
        self.action_input = ""

        self.finished = False

    @staticmethod
    def _strip_action(message: str) -> str:
        # remove everything that isn't spaces
        allowed = string.ascii_lowercase + "\x20"
        filtered_message = ""
        for c in message:
            if c in allowed:
                filtered_message += c

        # Strip any spaces off
        filtered_message = filtered_message.strip(" ")

        # remove everything but the first word
        # Need to make sure that gpt does not use a 2 word name for a tool
        filtered_message = filtered_message.split(" ")[0]

        return filtered_message

    def _clean_actions(self):
        """
            The purpose of this function is to ensure that the action
            and the action input are clean from any characters that
            would make it invalid like spaces and newlines.
        """
        self.action = self._strip_action(self.action)
        self.action_input = self.action_input.strip(" ").strip("\n").strip(" ")


    def get_action(self):
        """ Getter for action that cleans it up before returning """
        self._clean_actions()
        return self.action


    def get_action_input(self):
        """ Getter for action input that cleans it up before returning """
        self._clean_actions()
        return self.action_input


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
        """ Decide if an action needs to be done and the LLM should be stopped """

        # Make sure to clear out the action and input for the next ones
        if self.state == "THOUGHT":
            self.action = ""
            self.action_input = ""

        # This one is up top as it should run independent of
        # whether any of the other ones run
        if self.state == "FINAL ANSWER":
            self.finished = True


        # If both the previous and the current state is the summarise
        # then we have stopped printing the state keyword and are now
        # printing the action text
        if self.state == "ACTION" and self.previous_state == "ACTION":
            self.action += chunk


        elif self.state == "ACTION INPUT" and self.previous_state == "ACTION INPUT":
            # Since we let the state keyword print before recording the action,
            # we need to make sure that the action input state keyword is not
            # at the end of the action variable.
            if self.action.endswith("Action Input"):
                self.action = self.action[:len("Action Input")*-1]
            self.action_input += chunk


        # If the state is observation, then then we should stop
        # the agent to actually give it the observation
        elif self.state == "OBSERVATION":
            if self.action_input.endswith("Observation"):
                self.action_input = self.action_input[:len("Observation")*-1]
                # Returning false will tell the agent class to
                # stop letting the llm run and take over by executing
                # commands or such

            return False

        # The agent has printed its final answer, but for some reason has continued
        # talking. In this case we should just stop it.
        elif self.previous_state == "FINAL ANSWER" and self.state != "FINAL ANSWER":
            # Its unclear which direction it would continue in this case,
            # so lets try remove everything that remotely makes sense
            if self.action.endswith("Thought:"):
                self.action = self.action_input[:len("Thought:")]
            if self.action.endswith("Action:"):
                self.action = self.action_input[:len("Action:")]
            if self.action.endswith("Observation:"):
                self.action = self.action_input[:len("Observation:")]
            # Return false to tell the agent to stop
            return False

        return True


    def add_chunk(self, chunk: str) -> bool:
        """
            Add a chunk to the scratchpad.

            This function is used to record everything that the LLM
            has said as well as decide if the LLM needs to be stopped
            for the computer to take some action.

            Returns:
                - bool: False if the LLM should be stopped for some
                        other action to happen, otherwise True.
            
        """
        # Ignore any empty chunks that could sometimes happen
        if chunk is not None:
            print(chunk, flush=True, end="")
            self.context += chunk

            # Check if any state-change or action is needed.
            self._check_state()
            return self._action_parser(chunk)

        return True


    def add_observation(self, observation: str):
        """ Add the observation bit to the context """

        self.context += " "
        self.context += observation
        # print so the chunk print looks consistent
        print(" ", observation, flush=True)

        # Just make sure there is a newline at the end,
        # as not all commands do that
        if not self.context.endswith("\n"):
            self.context += "\n"


class Agent:
    def __init__(self, tools: list, system: str=""):
        self.tools = tools
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
        scratchpad = ScratchPad(prompt)

        while True:
            # Get LLM completion one token at a time.
            for chunk in openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": scratchpad.context}],
                stream=True,
            ):
                if chunk['choices'][0]["finish_reason"] == "stop":
                    if scratchpad.finished != True:
                        # LLM automatically found that it should stop after the action input
                        print()
                        scratchpad.add_chunk("\nObservation:")
                    break

                # Add each chunk to the scratchpad
                # The scratchpad processes the information and decides
                # if the bot needs to be stopped for some reason.
                if not scratchpad.add_chunk(chunk['choices'][0].get("delta", {}).get("content")):
                    break

            print("\n----------------model stopped--------------------")

            if scratchpad.finished == True:
                print()

                print("\n\n\--------------------- Final scratchpad ---------------------------")
                print(scratchpad.context)
                print("-------------------------------------------------------------------\n\n")
                return

            if scratchpad.get_action() not in [tool.name for tool in self.tools]:
                print(f"\n-----------------> '{scratchpad.get_action()}'")
                print(f"\n-----------------> '{string_to_hex(scratchpad.get_action())}'")
                observation = "Invalid action specified. Only the following tools can be used: "\
                                                         + str([tool.name for tool in self.tools])


            for tool in self.tools:
                if tool.name == scratchpad.get_action():
                    observation = tool.run(scratchpad.get_action_input() + " 2>&1")

            scratchpad.add_observation(observation)
            scratchpad.state = None


if __name__ == "__main__":
    load_dotenv()
    openai.organization = os.getenv("OPENAI_ORGANIZATION")
    openai.api_key = os.getenv("OPENAI_API_KEY")
    agent = Agent(tools=[ShellTool(verbose=False)])
    while True:
        agent.run(input("Task: "))



