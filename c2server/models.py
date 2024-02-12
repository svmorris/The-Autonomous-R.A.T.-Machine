
import os
import time
import secrets
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()


import database
from prompts import LIST_OPEN_PORTS
from prompts import REPORT_SUBTITLES
from prompts import GUESS_DEVICE_PURPOSE
from prompts import REPORTER_SYSTEM_PROMPT

db = database.Database()
vdb = database.VectorDatabase()


class ReporterTool:
    def __init__(self, instance, target):
        """ Gather information and create a report """
        self._target = target
        self._instance = instance
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


        # data for the user
        self.ports = []
        self.purpose = ""
        self.subtitles = []
        self.report = []

        # auto-run
        self._get_target_purpose()
        self._list_open_ports()
        self._set_subtitles()


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

        return self.ports


    def _set_subtitles(self):
        """ Format the REPORT_SUBTITLES list to the current target"""
        self.subtitles = []

        for subtitle in REPORT_SUBTITLES:
            if subtitle['title'] == "Analysis of port x":
                for port in self.ports:
                    self.subtitles.append({
                            "title": f"Analysis of port {port.split(' ')[0]}",
                            "keyword": port
                        })
            else:
                self.subtitles.append(subtitle)



    def write(self) -> list:
        """ Write the report """
        formatted_subtitles = "\t- " + "\n\t- ".join(
                [subtitle['title'] for subtitle in self.subtitles]
            ).strip("\n")

        prompt = REPORTER_SYSTEM_PROMPT.format(target=self._target, report_subtitles=formatted_subtitles)
        messages = [
                {"role": "system", "content": prompt}
                ]

        report = []

        for subtitle in self.subtitles:
            print('subtitle: ',subtitle , type(subtitle))
            keywords = f"{self._target} {subtitle['keyword']}".strip(" ")
            context = vdb.get_context(self._instance, keywords)

            messages.append({
                "role": "user",
                "content": f"## {subtitle['title']}\nNotes:\n```\n{context}\n```"
                })

            report.append({
                "type": "title",
                "content": subtitle['title']
                })

            response = self._client.chat.completions.create(
                model="gpt-4",
                messages=messages
            )

            messages.append({
                "role": "assistant",
                "content": response.choices[0].message.content
                })

            report.append({
                "type": "text",
                "content": messages[-1]['content']
                })


        self.report = report
        return report

