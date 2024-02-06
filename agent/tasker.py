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
import re
import time
from debug import prints
from openai import OpenAI
from databases import Database
from dotenv import load_dotenv

from prompts import RANGE_FINDER
from prompts import TASK_SPLITTER
from prompts import NEW_OBJECTIVE_CREATOR_STAGE0

load_dotenv()


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
        self.timeout_seconds = int(os.getenv("TARGET_TIMEOUT", 30))


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

    def add_if_unique(self, target_name: str):
        """ Add a new target only if its unique """
        doc = self.get_target_document(target_name)
        if not doc:
            self.add_target(target_name)

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

    def set_last_hit_time(self, target_name: str):
        """ Set the last_hit time of a target to the current time """
        for target in self.targets:
            if target['target'] == target_name:
                target['last_hit'] = int(time.time())


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
                    bullet = bullet_completed if task['completed'] else bullet_uncomplete
                    formatted += f"\t{bullet} {task['task']}\n"

        return formatted

    def target_needs_timeout(self, target_name: str) -> bool:
        """ Check if the target needs a timeout """
        target_document = self.get_target_document(target_name)
        if int(time.time()) - target_document["last_hit"] < self.timeout_seconds:
            return True
        return False

    def get_targets(self) -> list:
        """ Return a list of target names """
        names = []
        for target in self.targets:
            names.append(target['target'])
        return names


    def remote_target(self, target_to_remove):
        """ Remove a specific target from the targetlist """
        new_list = []
        for target in self.targets:
            if target['target'] != target_to_remove:
                new_list.append(target)
        self.targets = new_list





class TaskManager:
    _instance = None
    def __new__(cls):
        """ Make class signleton """
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
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
        self.target_range = None
        # Targets that should not be added to the Target
        # These are generally any devices that belong to the host
        # computer or are gateways, etc
        self.blacklisted_targets = set()



    def _new_objective_creator(self, target: str, target_info: str) -> str:
        """
            The task creator always tries to make general tasks
            that aren't easy to follow for a simple agent.

            This objective creator creates those tasks, which
            will be later split up by the task creator.
        """

        # If the target has not had any tasks previously
        # than use the general tasks as example
        example_tasks = self.target_list.formatted_task_list(target)
        if not example_tasks:
            example_tasks = self.target_list.formatted_task_list("general")

        prompt = NEW_OBJECTIVE_CREATOR_STAGE0.format(
            target=target,
            target_info=target_info,
            tasks=example_tasks
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


    def _find_ip_addresses(self, data: str):
        """
            Use regex to pick out all IP addresses from a block of text
            that match a specific range and are not blacklisted.
        """
        assert self.target_range is not None, "Target IP range has not been set!"

        addresses = set()
        # IP regex
        ips = re.findall(rf'\b{re.escape(self.target_range)}\.\d{{1,3}}\.\d{{1,3}}(?:/\d{{1,2}})?\b', data)
        for target_name in ips:
            # Remove any range identifiers from the IP
            target_name = target_name.split("/")[0]
            if target_name not in self.blacklisted_targets:
                addresses.add(target_name)

        return list(addresses)

    def update_blacklist_from_c2(self, blacklist):
        """ Take blacklist updates form the c2 server """
        for blacklisted_target in blacklist:
            self.blacklisted_targets.add(blacklisted_target)

        targets = self.target_list.get_targets()
        for blacklisted_target in self.blacklisted_targets:
            if blacklisted_target in targets:
                self.target_list.remote_target(blacklisted_target)


    def update_targetlist(self, data: str):
        """
            Take all IP addresses that match the target range from
            a block of text and add it to the target list.
        """
        for target_name in self._find_ip_addresses(data):
            self.target_list.add_if_unique(target_name)

    def update_target_blacklist(self, data: str):
        """
            Take all IP addresses that match the target range from
            a block of text and add it to the target blacklist.

            IPs added here will not be added to target list in the future.
        """
        for target_name in self._find_ip_addresses(data):
            self.blacklisted_targets.add(target_name)


    def set_target_range(self, text: str):
        """
            Set the target range for the IP address finder. Only IPs within
            The range set here will be considered targets.
        """
        range_or_ip = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": RANGE_FINDER},
                {"role": "user", "content": text},
            ]
        ).choices[0].message.content.strip().split(" ")[0]
        self.target_range = ".".join(range_or_ip.split(".")[:2])


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

        # If there are incomplete tasks for general, then do them
        # before any other target
        incomplete_tasks = self.target_list.get_incomplete_tasks("general")
        if incomplete_tasks:
            target_name = "general"
        else:
            # If there aren't in general, then get the target
            # that hasn't been hit in the longest time
            target_name = self.target_list.get_oldest_target()

        # If the target is not general, then run the automatic task creator
        # This will create new tasks if there aren't any, but will do nothing
        # if there are still un-complete tasks
        if target_name is not "general":
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

