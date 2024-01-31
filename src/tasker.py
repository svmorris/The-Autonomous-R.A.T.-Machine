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
import time
from debug import prints
from openai import OpenAI
from databases import Database
from dotenv import load_dotenv

from prompts import NEW_OBJECTIVE_CREATOR_STAGE0
from prompts import TASK_SPLITTER

load_dotenv()



class TaskManager:
    _instance = None
    def __new__(cls):
        """ Make class signleton """
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
        return cls._instance

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
            self.add_task_end(task)


class TargetList:
    """Class to handle the task list.

    Attributes:
        targets (list): A list of target dictionaries.
    """

    def __init__(self, targets: list):
        """Initialize the TargetList with a list of targets.

        Args:
            targets (list): A list of target dictionaries.
        """
        self.targets = targets
        self.timeout_seconds = os.getenv("TARGET_TIMEOUT", 30)

    def get_target_document(self, target_name: str) -> dict:
        """Retrieve a target document by its name. """
        for target in self.targets:
            if target['target'] == target_name:
                return target
        return {}

    def add_target(self, target_name: str, last_hit=0) -> None:
        """Add a new target to the list. """
        new_target = {"target": target_name, "last_hit": last_hit, "tasks": []}
        self.targets.append(new_target)

    def add_task(self, target_name: str, task_description: str) -> None:
        """Add a task to a specific target. """
        for target in self.targets:
            if target["target"] == target_name:
                new_task = {"task": task_description, "completed": False}
                target["tasks"].append(new_task)
                break

    def mark_task_completed(self, target_name: str, task_description: str) -> None:
        """Mark a specific task as completed. """
        for target in self.targets:
            if target["target"] == target_name:
                for task in target["tasks"]:
                    if task["task"] == task_description:
                        task["completed"] = True
                        break

        # target_document = self.get_target_document(target_name)
        # for task in target_document:
        #     if task['task'] == task_description

    def get_incomplete_tasks(self, target_name: str) -> list:
        """Get a list of incomplete tasks for a specific target. """
        incomplete_tasks = []
        for target in self.targets:
            if target["target"] == target_name:
                incomplete_tasks = [task for task in target["tasks"] if not task["completed"]]
                break
        return incomplete_tasks

    def set_last_hit_time(self, target_name: str, l_time=int(time.time())):
        """ Set the last_hit time of a target to the current time """
        for target in self.targets:
            if target['target'] == target_name:
                target['last_hit'] = l_time


    def get_oldest_target(self) -> str:
        """ Return the target_name of the target with the smallest "last_hit" variable """
        smallest = int(time.time())
        smallest_target_name = ""
        for target in self.targets:
            if target['last_hit'] < smallest and target['target'] != "general": 
                smallest = target['last_hit']
                smallest_target_name = target['target']

        if not smallest_target_name:
            assert False, "There are no targets!!!"

        return smallest_target_name

    def formatted_task_list(self, target_name: str, checkbox=False) -> str:
        """
            Create a string out of all the tasks for the
            target that can be given to a model or displayed
            to a user.
        """
        # Different bullet points are used for the model and for users
        bullet_completed = "-"
        bullet_uncomplete = "-"
        if checkbox:
            bullet_completed = "[✓]"
            bullet_uncomplete = "[ ]"

        formatted = ""
        for target in self.targets:
            if target['target'] == target_name:
                for task in target['tasks']:
                    bullet = [bullet_completed if task['completed'] else bullet_uncomplete]
                    formatted += f"\t{bullet} {task['task']}\n"


        print('formatted: ',formatted , type(formatted))
        assert len(formatted) > 1, "No Such target for task formatter (or maybe there are just no tasks?)"
        return formatted

    def target_needs_timeout(self, target_name: str) -> bool:
        """ Check if the target needs a timeout """
        target_document = self.get_target_document(target_name)
        if int(time.time()) - target_document["last_hit"] < self.timeout_seconds:
            return True
        return False










class NewTaskManager:
    _instance = None
    def __new__(cls):
        """ Make class signleton """
        if cls._instance is None:
            cls._instance = super(NewTaskManager, cls).__new__(cls)
        return cls._instance


    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.target_list = TargetList([{
            "target": "general",
            "last_hit": 0,
            "tasks": [
                {
                    "task": "Use `ip a` to find me your ip address and the local IP range.",
                    "completed": False
                },
                {
                    "task": "Use nmap to find all connected on the above mentioned range",
                    "completed": False
                },
            ]
        }])
        self.db = Database()



    def _new_objective_creator(self, target: str, target_info: str) -> str:
        """
            The task creator always tries to make general tasks
            that aren't easy to follow for a simple agent.

            This objective creator creates those tasks, which
            will be later split up by the task creator.
        """


        prompt = NEW_OBJECTIVE_CREATOR_STAGE0.format(
            target=target,
            target_info=target_info,
            tasks=self.target_list.formatted_task_list()
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


    def _objective_splitter(self, objective: str, target_info: str) -> list:
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


    def _automatic_task_creator(self, target_name: str):
        """ Add new tasks to the task_list """

        # Only create new tasks if there are none left
        # Its simpler to just call this function all the time
        # and decide here if new need to be added bc we never
        # know how many tasks were created.
        if self.target_list.get_incomplete_tasks(target_name):
            return

        target_context = self.db.get_context(target_name)
        new_objective = self._new_objective_creator(target_name, target_context)
        new_tasks = self._objective_splitter(new_objective, target_context)

        for task in new_tasks:
            self.target_list.add_task(target_name, task)


    def get_next(self, check_timeout=True) -> tuple[str,str]:
        """
            Get the next task for the agent to execute.

            The next task is determined by the following rules:
                - if general has tasks, do those
                - The next target is the one with the smallest last_hit variable
                - If this target has no un-completed tasks, create some
                - If there has not been 30 seconds since this target was last hit, wait a bit

            Returns:
               target name (str)
               task details (str)
        """

        # Check if all "general" tasks are complete
        incomplete_tasks = self.target_list.get_incomplete_tasks("general")
        if incomplete_tasks:
            return "general", incomplete_tasks[0]['task']

        # Get incomplete tasks
        target_name = self.target_list.get_oldest_target()

        # Run the task creator to make new tasks if there aren't any
        # This will just do nothing if there are already incomplete tasks
        self._automatic_task_creator(target_name)

        # Check timeout should only be false if we are just getting
        # the name of this last task to set it as complete
        if check_timeout:
            # If there has not yet been 30 seconds since the target was hit
            while self.target_list.target_needs_timeout(target_name):
                prints(f"---> Timeout on target {target_name}")
                time.sleep(5)

        # Get incomplete tasks
        incomplete_tasks = self.target_list.get_incomplete_tasks(target_name)

        # Return next task
        return target_name, incomplete_tasks[0]['task']


    def auto_mark_completed(self):
        """
            Mark task as completed and update last_hit time

            This function will automatically figure out what task needs to be marked
            as completed based on what task is next.
        """

        target, task = self.get_next(check_timeout=False)
        self.target_list.mark_task_completed(target, task)
        self.target_list.set_last_hit_time(target)




class TaskManagerByTarget:
    """ Group tasks by target """

    def __init__(self):

        self = [
                {"task": "Use `ip a` to find me your ip address and the local IP range.", "completed": False},
                {"task": "Use nmap to find all connected on the above mentioned range", "completed": False},
        ]





