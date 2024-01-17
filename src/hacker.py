"""
This file should be broadly the same as the hacker notebook, however, my laptop seems to have
troubles running podman from a notebook. Apparently jupyter on my laptop wants to run code in containers.
"""

import os
import time

from agent import Agent
from tasker import TaskManager
from databases import Database
from shelltool import ExecutionSandbox

# Just ensure that things are properly killed
os.system("podman kill rat-machine-sandbox")
os.system("podman rm rat-machine-sandbox")
time.sleep(1)


database = Database()
task_manager = TaskManager()
agent = Agent(tools=[ExecutionSandbox()], verbose=False)


hard_coded_tasks=True
while True:
    print("-----------full task-list-----------")
    for list_item in task_manager.task_list:
        mark = "[✓]" if list_item['completed'] else "[ ]"
        print(f"{mark} {list_item['task']}")


    task = task_manager.get_next()

    if task_manager.get_num_uncompleted() == 0:
        hard_coded_tasks=False
        task_manager.automatic_task_creator()
        continue

    context = database.get_context(task)

    print("-----------next task----------------")
    print(f"Context: {context}")
    print(f"Task: {task}")

    output = agent.run(task, context=context, return_full=True)
    database.update(output)
    task_manager.mark_next_completed()

    # In the beginning we need to wait for the database to update
    if hard_coded_tasks:
        print("Waiting for database...")
        time.sleep(30)
