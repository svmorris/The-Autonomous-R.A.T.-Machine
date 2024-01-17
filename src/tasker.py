"""
The purpose of this program is to be a sort of task manager for the agent.

The database has a list of target IP addresses which we will
cycle through one by one. On each cycle, the task manager will get a general
picture of the information we know about the target, and come up with a new tasks
that the agent needs to execute.

These tasks will then be added to a task list, which the agent goes through one-by-one.
New tasks, (for now) will only be added when the task list is empty as new information
might change what the task would be. However, in the future the plan is to run multiple
agents at once to speed up the workings of the program. In this case the task manager
will create new tasks for each device in parallel.

In stage one of the task manager, all tasks are created with the purpose of
discovering more information about each target. Stage 2, will most likely be about
exploiting the targets.


The task manager will keep track of all completed and non-completed tasks.
"""
import os
from openai import OpenAI
from databases import Database
from dotenv import load_dotenv

from prompts import NEW_OBJECTIVE_CREATOR_STAGE0
from prompts import TASK_SPLITTER

load_dotenv()



class TaskManager:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Some tasks can be hard-coded as they will be the same on each run.
        # These tasks serve as the starting point for the system and as an
        # example for new tasks
        self.task_list = [
                {"task": "Use `ip a` to find me your ip address and the local IP range.", "completed": False},
                {"task": "Use nmap to find all connected on the above mentioned range", "completed": False},
        ]
        self.db = Database()

    def get_next(self) -> str:
        """ Get the next non-completed task """
        for task in self.task_list:
            if task['completed'] is False:
                return task['task']
        return "" # TODO: Find some way to handle running out of tasks


    def add_task_next(self, new_task: str):
        """ Add a new task as the next task """
        new_task_list = []
        for i, task in enumerate(self.task_list):
            if task['completed'] is True:
                new_task_list.append(task)
            else:
                new_task_list.append({"task": new_task, "completed": False})
                new_task_list.extend(self.task_list[i:])
                self.task_list = new_task_list
                return

    def add_task_end(self, new_task: str):
        """ Add a new task to the end of the task_list """
        self.task_list.append({"task": new_task, "completed": False})

    def mark_next_completed(self):
        """ Mark the next task as completed """
        for i, task in enumerate(self.task_list):
            if task['completed'] is False:
                self.task_list[i]['completed'] = True
                return

    def mark_task_completed(self, completed_task: str):
        """ Mark a specific task completed based on the task string """
        for i, task in enumerate(self.task_list):
            if task['task'] == completed_task:
                self.task_list[i]['completed'] = True



    def get_num_uncompleted(self) -> int:
        """ Get the number of un-finished tasks. """
        count = 0
        for task in self.task_list:
            if not task['completed']:
                count += 1
        return count


    def get_tasks_as_string(self) -> str:
        """ Get the tasks as a bullet point list to use in prompts """

        tasks_str = ""
        for task in self.task_list:
            tasks_str += f"\t- {task['task']}"

        return tasks_str


    def new_objective_creator(self, target: str, target_info: str) -> str:
        """
            The task creator always tries to make general tasks
            that aren't easy to follow for a simple agent.

            This objective creator creates those tasks, which
            will be later split up by the task creator.
        """


        prompt = NEW_OBJECTIVE_CREATOR_STAGE0.format(
            target=target,
            target_info=target_info,
            tasks=self.get_tasks_as_string()
        )

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )

        text_output = response.choices[0].message.content
        for line in text_output.split("\n"):
            if line.strip().startswith("-"):
                return line.strip(" ").strip("-").strip(" ")
            return line.strip()
        return text_output


    def objective_splitter(self, objective: str, target_info: str) -> list:
        """ Split a larger task into many smaller ones. """

        prompt = TASK_SPLITTER.format(
            objective=objective,
            target_info=target_info
        )

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )

        # Add the new tasks
        tasks = []
        text_output = response.choices[0].message.content
        for line in text_output.split("\n"):
            if line.strip().startswith("-"):
                tasks.append(line.strip(" ").strip("-").strip(" "))

        return tasks


    def automatic_task_creator(self):
        """ Add new tasks to the task_list """

        # Only create new tasks if there are none left
        # Its simpler to just call this function all the time
        # and decide here if new need to be added bc we never
        # know how many tasks were created.
        if self.get_num_uncompleted() > 0:
            return

        target = self.db.get_next_target()
        target_info = self.db.get_context(target)
        print("-----------starting agent-----------")
        print('target: ',target)
        print('target_info: ',target_info)

        new_objective = self.new_objective_creator(target, target_info)
        tasks = self.objective_splitter(new_objective, target_info)

        # Adding them to the end one by one so that they are added in
        # the right order
        for task in tasks:
            self.add_task_end({"task": task, "completed": False})






