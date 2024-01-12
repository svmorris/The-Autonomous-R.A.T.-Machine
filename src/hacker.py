"""
This file should be broadly the same as the hacker notebook, however, my laptop seems to have
troubles running podman from a notebook. Apparently jupyter on my laptop wants to run code in containers.
"""


import os
import sys
import time

from openai import OpenAI
from dotenv import load_dotenv

from agent import Agent
from tasker import TaskManager
from entityDB import EntityDatabase
from shelltool import ExecutionSandbox

load_dotenv()
client = OpenAI(api_key=(os.getenv("OPENAI_API_KEY")))


# Just ensure that things are properly killed
os.system("podman kill rat-machine-sandbox")
os.system("podman rm rat-machine-sandbox")
time.sleep(1)


task_manager = TaskManager(client)
database = EntityDatabase(client, "gpt-3.5-turbo")
agent = Agent(client, tools=[ExecutionSandbox()], verbose=False)



while True:
    task = task_manager.get_next()
    print('task: ',task , type(task))
    print(f"'{task}'")

    # ran out of tasks
    if task.strip() == "":
        break
        
    print("-----------full context-------------")
    print(database.database)
    print("------------------------------------")
        
    context = ""
    if database.database != "":
        context = database.get_context(task)


    print("--------------task------------------")
    print(f"Context: {context}")
    print(f"Task: {task}")
    print("------------------------------------")

    
    output = agent.run(task, context=context)
    database.update(output)
    task_manager.mark_next_completed()

    print("--------------output----------------")
    print(output)
    print("------------------------------------\n\n")
    print(database.database)