" This file is an experiment to use a couple language models as an entity database "

import os
import prompts
from openai import OpenAI
from dotenv import load_dotenv



class EntityDatabase:
    def __init__(self, openai_client, model: str):
        self.model = model
        self.client = openai_client
        self.database = ""


    def update(self, message: str):
        message_with_example = prompts.ENTITY_DB_WRITE_EXAMPLE
        message_without_example = ""
        message = message_with_example.format(database=self.database, message=message)
        output = self.client.ChatCompletion.create(
                model=self.model,
                messages = [{"role": "user", "content": message}]
                )

        # maybe make some sort of error checker first
        self.database = output["choices"][0]["message"].get("content")

    def query(self, query: str):
        """
            Get information from the database directly.
            The query parameter takes either a keyword(s) or a question. The database
            will attempt to provide all relevant information.
        """
        query_template = prompts.ENTITY_DB_QUERY
        message = query_template.format(database=self.database, query=query)

        output = self.client.ChatCompletion.create(
                model=self.model,
                messages = [{"role": "user", "content": message}]
                )

        return output["choices"][0]["message"].get("content")

    def get_context(self, query: str):
        """
            The goal of this function is to use the database to help provided
            useful information for a query to an agent (or something similar).

            For example, when the executor agent gets a new task, this database
            is checked for any information it can provide to help the
            agent do its work.
        """
        query_template = prompts.ENTITY_DB_RELEVANT_CONTEXT
        message = query_template.format(database=self.database, query=query)

        output = self.client.ChatCompletion.create(
                model=self.model,
                messages = [{"role": "user", "content": message}]
                )

        return output["choices"][0]["message"].get("content")








if __name__ == "__main__":
    load_dotenv()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    db = EntityDatabase(client, "gpt-3.5-turbo")

    db.update("There are three devices on the network: 192.168.1.3 is a webserver with only port 80 open. 192.168.1.32 is a linux pc with ssh open, and the third 192.168.1.1 we dont know much about yet.")
    db.update(""" Starting Nmap 7.91 ( https://nmap.org ) at 2021-10-19 05:19 UTC
Nmap scan report for 192.168.1.1
Host is up (0.000035s latency).
Not shown: 994 closed ports
PORT     STATE SERVICE    VERSION
22/tcp   open  ssh        OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
80/tcp   open  http       Apache httpd 2.4.29 ((Ubuntu))
443/tcp  open  ssl/http   Apache httpd 2.4.29
3128/tcp open  http-proxy Squid http proxy 3.5.27
8080/tcp open  http-proxy Apache Tomcat/Coyote JSP engine 1.1
Device type: general purpose
Running: Linux 2.6.X|3.X|4.X
OS CPE: cpe:/o:linux:linux_kernel:2.6 cpe:/o:linux:linux_kernel:3 cpe:/o:linux:linux_kernel:4
OS details: Linux 2.6.32 - 3.13, Linux 2.6.32 - 4.9, Linux 3.2 - 4.9, Linux 3.7 - 4.1, Linux 3.8 - 3.11, Linux 3.8 - 4.9, Linux 4.2
Network Distance: 1 hop""")
    print(db.database)
    # print(db.query(input("Q: ")))
    while True:
        print(db.get_context(input("Task: ")))

