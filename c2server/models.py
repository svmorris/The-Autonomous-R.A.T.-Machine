
import os
import time
import secrets
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()


import database
from prompts import LIST_OPEN_PORTS
from prompts import GUESS_DEVICE_PURPOSE

db = database.Database()
vdb = database.VectorDatabase()


class ReporterTool:
    def __init__(self, instance, target):
        """ Gather information and create a report """
        self._target = target
        self._instance = instance
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


        # data for the user
        self.purpose = ""
        self.ports = []

        # auto-run
        self._get_target_purpose()
        self._list_open_ports()


    def _get_target_purpose(self) -> str:
        """
            Attempts to guess what the target device's purpose
            is in about 1 sentence. (website, dns, etc)
        """

        context = vdb.get_context(self._instance, self._target+ " operating system")

        prompt = GUESS_DEVICE_PURPOSE.format(target=self._target, context=context)

        response = self._client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}]
        )

        self.purpose = response.choices[0].message.content
        return self.purpose


    def _list_open_ports(self) -> list:
        """ Get all open ports on the target """
        context = vdb.get_context(self._instance, self._target+ " port")

        prompt = LIST_OPEN_PORTS.format(target=self._target, context=context)

        response = self._client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}]
        )

        ports_str = response.choices[0].message.content

        for line in ports_str.split("\n"):
            line = line.strip()
            if line.startswith("-"):
                self.ports.append(line.strip().strip("-").strip())
