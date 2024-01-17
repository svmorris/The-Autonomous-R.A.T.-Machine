"""
This is a new database whose goal is to replace the entity database used earlier in this project.

This new database will be based on a summary engine and a regular vector database at pinecone. Further
it will include a secondary database called `targitlist` which should just house all known targets IPs.
The database will attempt to interface the same way as the entity db did with the rest of the project.
"""


import re
import os
import time
import pinecone
from openai import OpenAI
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone
from langchain.text_splitter import CharacterTextSplitter

from debug import prints
from prompts import SUMMARIZER
from prompts import RANGE_FINDER


load_dotenv()


class Database():
    def __init__(self):
        """ Set things up """
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.target_list: list[dict] = []
        self.target_counter = 0

        pinecone.init(
            api_key=os.getenv("PINECONE_KEY"),
            environment="gcp-starter"
        )

        self.embeddings = OpenAIEmbeddings(
           openai_api_key=os.getenv("OPENAI_KEY"),
        )

        # Create a new namespace for the runtime which
        # exists as long as this program is running,
        # no matter how many times the database class
        # is initialized
        if os.getenv('DB_NAMESPACE') is None:
            self.namespace = "runtime-"+str(int(time.time())) 
            os.environ['DB_NAMESPACE'] = self.namespace
            prints(f"Running on pinecone namespace '{self.namespace}'")

        self.index_name = "autonomous-rat-machine"
        self.docsearch = Pinecone.from_existing_index(
            self.index_name,
            self.embeddings,
            namespace=self.namespace
        )

    def _create_summary(self, data) -> str:
        """ Create an entity-focused summary of an agents runtime """

        messages = [
                {"role": "system", "content": SUMMARIZER},
                {"role": "user", "content": data}
                ]

        response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages
                )

        return response.choices[0].message.content


    def add_new_data(self, data: str):
        """
            Provided the output of an agents runtime, create a summary
            of device information discovered and upload it to the vector
            database. Also find all new devices in that data to add to
            the target list.
        """
        summary = self._create_summary(data)

        # NOTE: might have to make the chunk sizes smaller to save space in the future
        text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=50, chunk_overlap=15
        )

        documents = text_splitter.split_text(summary)

        self.docsearch.from_texts(
                documents,
                self.embeddings,
                index_name=self.index_name,
                namespace=self.namespace
            )

        self.update_targetlist(data)

    def update_targetlist(self, data: str):
        """
            Takes input of any type of string and finds IP addresses
            within our (simplified version of a) range to add to the target list.

            The range in this case is the first two parts of the first
            IP address in the target list. If there is no device in it yet,
            then it is found with the rangefinder model.

            NOTE: It takes approximately 30 seconds to update the database
                  after adding new data. During this time, new information
                  will not be returned in queries.
        """

        if not self.target_list:
            range_or_ip = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": RANGE_FINDER},
                    {"role": "user", "content": data},
                ]
            ).choices[0].message.content.strip().split(" ")[0]
            ip_range = ".".join(range_or_ip.split(".")[:2])
        else:
            ip_range = ".".join(self.target_list[0]["ip"].split(".")[:2])

        # IP regex
        ips = re.findall(rf'\b{re.escape(ip_range)}\.\d{{1,3}}\.\d{{1,3}}(?:/\d{{1,2}})?\b', data)
        for ip in ips:
            if ip not in [t['ip'] for t in self.target_list]:
                self.target_list.append({
                    "ip": ip,
                    "finished": False,
                    "last_hit": int(time.time())
                })


    def get_context(self, text: str) -> str:
        """ Gets any related information to `text` from the vector database """
        docs = self.docsearch.similarity_search(text)
        context = "```\n"
        for d in docs:
            context += f"{d.page_content}\n"
        context += "```"
        return context


    def get_next_target(self) -> str:
        """
            Due to the database taking some time before new information
            shows up on it, we constantly rotate through all discovered
            targets to make sure we are always working on a new one.

            In case of there being very few targets, we make sure that
            the same target is not hit again within 30 seconds.
        """
        self.target_counter = (self.target_counter + 1) % len(self.target_list)
        target = self.target_list[self.target_counter]

        # If there has not yet been 30 seconds since the target was hit
        while int(time.time()) - target["last_hit"] < 30:
            prints(f"---> Timeout on target {target['ip']}")
            time.sleep(5)

        self.target_list[self.target_counter]['last_hit'] = int(time.time())
        return target["ip"]




sample_agent_data = """Task: Find open ports for all discovered devices on the network
Thought: To find open ports on each of these machines we can utilize the 'nmap' command, but it should be noted that scanning for open ports can be misinterpreted as an attack by the host and could result in the command being blocked by firewall settings, depending on network configuration. However, since this is a task, I will proceed as though permission to conduct the scan has been received.
Action: terminal
Action Input: nmap -Pn 192.168.1.179 192.168.1.1 192.168.1.114 192.168.1.146 192.168.1.158
Note: The -Pn option will scan the network and output any open ports that it discovers on these IP addresses. It might take a while to complete this operation, please be patient!
Observation: Starting Nmap 7.94SVN ( https://nmap.org ) at 2024-01-17 11:37 UTC
Nmap scan report for host.containers.internal (192.168.1.179)
Host is up (0.0055s latency).
All 1000 scanned ports on host.containers.internal (192.168.1.179) are in ignored states.
Not shown: 1000 closed tcp ports (reset)

Nmap scan report for 192.168.1.1
Host is up (0.0048s latency).
Not shown: 995 closed tcp ports (reset)
PORT      STATE SERVICE
80/tcp    open  http
5500/tcp  open  hotline
8180/tcp  open  unknown
9000/tcp  open  cslistener
10004/tcp open  emcrmirccd

Nmap scan report for 192.168.1.114
Host is up (0.0076s latency).
Not shown: 993 closed tcp ports (reset)
PORT      STATE SERVICE
53/tcp    open  domain
5000/tcp  open  upnp
7000/tcp  open  afs3-fileserver
7100/tcp  open  font-service
49152/tcp open  unknown
49155/tcp open  unknown
62078/tcp open  iphone-sync

Nmap scan report for 192.168.1.146
Host is up (0.40s latency).
All 1000 scanned ports on 192.168.1.146 are in ignored states.
Not shown: 1000 closed tcp ports (reset)

Nmap scan report for 192.168.1.158
Host is up (0.0090s latency).
Not shown: 997 closed tcp ports (reset)
PORT   STATE SERVICE
21/tcp open  ftp
22/tcp open  ssh
80/tcp open  http

Nmap done: 5 IP addresses (5 hosts up) scanned in 2.25 seconds
bash: line 2: Note:: command not found
Thought: The nmap command has scanned the specified machines and returned open ports for each one. So we have the information required to complete the task.

For the machine with IP 192.168.1.179, there are no open ports.

For the machine with IP 192.168.1.1, the open ports are 80, 5500, 8180, 9000, and 10004.

For the machine with IP 192.168.1.114, the open ports are 53, 5000, 7000, 7100, 49152, 49155, and 62078.

For the machine with IP 192.168.1.146, there are no open ports.

For the machine with IP 192.168.1.158, the open ports are 21, 22, and 80.

Final Answer: Open ports for each machine are as follows:
- 192.168.1.179: No open ports.
- 192.168.1.1: 80, 5500, 8180, 9000, 10004
- 192.168.1.114: 53, 5000, 7000, 7100, 49152, 49155, 62078
- 192.168.1.146: No open ports.
- 192.168.1.158: 21, 22, 80
"""

if __name__ == "__main__":
    db = Database()
    db.add_new_data(sample_agent_data)
    time.sleep(30)
    print(db.get_context("Find out what website is running on 1.1"))
    while True:
        time.sleep(5)
        print(db.get_next_target())

