"""
The purpose of this program is to be a sort of task manager for the agent.

The exposed class should be able to do the following:
    - Create a todo list that breaks down a goal into smaller tasks
    - Add and remove tasks from the todo list
    - Mark tasks as completed
    - Re-arrange the todolist to put the most important tasks first
    - Based on agent behaviour and outputs, recognise if new tasks need to be added to the list.
"""

import openai

class TaskManager:
    def __init__(self, openai, goal: str):

