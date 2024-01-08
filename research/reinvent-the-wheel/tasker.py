"""
The purpose of this program is to be a sort of task manager for the agent.

Since the goal of this system is always the same, a lot of the
tasks will be hard-coded with the most optimal prompts. However,
some tasks will have to be added automatically both from a template
and in rare cases directly ai generated tasks.

The exposed TaskManager class should be able to do the following:
- Have a short, default todo list
- Analise agent output to decide on what new tasks need to be added
- Add templated new tasks to the todolist when devices and ports are discovered
- mark tasks as completed

Some other features that might be needed later:
- Automatically generate some new tasks and add them to the right place
- re-arrange and delete tasks
"""

import openai
from pprint import pprint

class TaskManager:
    def __init__(self, openai_instance, model="gpt-4"):
        self.model = model
        self.openai = openai_instance
        self.tasklist = [
                # {"task": "Commands you run are in a docker container. The host machine IP has the dns name `host_ip_address`. Since you will need this for further instructions, can you get the IP behind this dns?", "completed": False},
                {"task": "Find all devices connected to the host network (192.168.1.0/24)", "completed": False},
                # Most further tasks should be added automatically
                # as there should be a separate task for finding ports,
                # vulnerabilities and gaining access for each device
        ]


    def get_next(self) -> str:
        """ Get the next non-completed task """
        for task in self.tasklist:
            if task['completed'] is False:
                return task['task']
        return "" # TODO: Find some way to handle running out of tasks


    def add_task_next(self, new_task: str):
        """ Add a new task as the next task """
        new_tasklist = []
        for i, task in enumerate(self.tasklist):
            if task['completed'] is True:
                new_tasklist.append(task)
            else:
                new_tasklist.append({"task": new_task, "completed": False})
                new_tasklist.extend(self.tasklist[i:])
                self.tasklist = new_tasklist
                return

    def add_task_end(self, new_task: str):
        """ Add a new task to the end of the tasklist """
        self.tasklist.append({"task": new_task, "completed": False})

    def mark_next_completed(self):
        """ Mark the next task as completed """
        for i, task in enumerate(self.tasklist):
            if task['completed'] is False:
                self.tasklist[i]['completed'] = True
                return

    def mark_task_completed(self, completed_task: str):
        """ Mark a specific task completed based on the task string """
        for i, task in enumerate(self.tasklist):
            if task['task'] == completed_task:
                self.tasklist[i]['completed'] = True



if __name__ == "__main__":
    t = TaskManager(None)
    t.add_task_next("test")
    pprint(t.tasklist)
