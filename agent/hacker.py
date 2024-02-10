"""
This file should be broadly the same as the hacker notebook, however, my laptop seems to have
troubles running podman from a notebook. Apparently jupyter on my laptop wants to run code in containers.
"""

import os
import time

from agent import Agent
from tasker import TaskManager
from databases import Database
from c2communication import Report
from shelltool import ExecutionSandbox

# Just ensure that things are properly killed
os.system("podman kill rat-machine-sandbox")
os.system("podman rm rat-machine-sandbox")
time.sleep(1)


database = Database()
task_manager = TaskManager()
agent = Agent(tools=[ExecutionSandbox()], verbose=False)
report = Report(database.namespace)


i = 0
while True:
    report.run()
    print("------------All targets-------------")
    [print("- ", x) for x in task_manager.target_list.get_targets()]
    print("------------Next target-------------")
    # Get the next target and task
    target, task = task_manager.get_next()
    print(f"Target: {target}")
    print(task_manager.target_list.formatted_task_list(target, checkbox=True))


    print("-----------next task----------------")
    context = database.get_context(task)
    print(f"Context: {context}")
    print(f"Task: {task}")

    # The first task only tries to find the local IP range.
    # Its enough if we just return the final answer here,
    # which makes it easier for the range finder to set the
    # correct range.
    if i == 0:
        output = agent.run(task, context=context, return_full=True)
        task_manager.set_target_range(output)
        task_manager.update_target_blacklist(output)
        print("----------Target blacklist----------")
        print("range: ", task_manager.target_range)
        [print("- ", x) for x in task_manager.blacklisted_targets]


    else:
        # For other tasks, get full return for summarizer
        output = agent.run(task, context=context, return_full=True)
        # Target list does not need to be updated on the first command
        # as nothing it adds is useful
        task_manager.update_targetlist(output)

    database.update(output)
    task_manager.auto_mark_completed(target)
    i += 1
