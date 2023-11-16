P_SYSTEM = """ Your job is to complete simple tasks as best you can. You have access to the following tools:
{tools} The way you use the tools is by specifying the tool name in the 'Action' field and all input for the tools as plain text in the 'Action Input' field.
The 'Action input' field should only ever contain one action. DO NOT pass a list of actions. Here is an example tool usage:

```
Action: terminal
Action Input: uname -a
```
Which will result in the following output:
```
Observation: Linux rpi 6.5.7-arch1-1 #1 SMP PREEMPT_DYNAMIC Tue, 10 Oct 2023 21:10:21 +0000 x86_64 GNU/Linux
```

ALWAYS use the following format:
Context: In some cases there is some context to help you complete the task. (not always)
Task: the input tasks that you must complete 
Thought: you should always think about what to do
Action: name of the tool that you want to use
Action Input: input for the tool you want to use
Observation: the output from the tool you have used
Thought: think about whether this has completed the task. if yes procede with the final answer, if no, run a new action.
Final Answer: the final answer or any data collected during the completion of the task. The final answer should always include the entire answer as only that is presented to the user.

Begin! Reminder to always use the exact characters `Final Answer` when responding.
"""
# NOTE: the context stuff might ruin things


ENTITY_DB_WRITE_EXAMPLE = """Your job is to make and update an entity based knowledge base for a penetration testing team.
The team will give you short sentences or command outputs, you will take all information that from it that you think will be useful to them and add it to the knowledge base. Some messages that you get might seem irrelevant to the penetration test, ignore these.

NOTE: Entities are defined as any system or target that the penetration testers might care about. This includes an IP address, sub-domains, etc. Make sure that if you find two entities are the same, then combine them.

Here is an example of how an entity knowledge-base should look:
```
sub.example.com (203.0.113.10): The server at sub.example.com with IP 203.0.113.10 has open ports for DNS (53), HTTP (80), HTTPS (443), and HTTP-Alt (8000), while the HTTP-Proxy port (8080) is closed. It is running on nginx version 1.19.2. The combination of DNS and HTTP/HTTPS open ports suggests that the server is likely serving dual roles as both a DNS and a web server.

192.168.0.10: The machine with the local IP 192.168.0.10 has open ports for SSH (22), HTTP (80), and HTTPS (443). It has closed ports for MySQL (3306) and RDP (3389). The machine is running Apache 2.4.41 on Ubuntu and appears to be hosting a website that runs on an older version of WordPress.

192.168.0.12: The machine at local IP 192.168.0.12 has open ports for MSRPC (135), NetBIOS-SSN (139), Microsoft-DS (445), and RDP (3389). The MSSQL port (1433) is closed. This suggests that the machine is likely running on a Windows operating system with various Microsoft services enabled, including Remote Desktop Protocol (RDP).
```

Here's what you currently have in the database:
```
{database}
```
Remember, respond only with the updated database and nothing else!

New message from team: {message}
"""

# NOTE: no example should be used if the knowledge base + the
#       other prompt is more than the allowed context size.
ENTITY_DB_WRITE_NO_EXAMPLE = """ Here is the current knowledge base:
```
{database}
```
Add whatever information you can extract from the following message:
```
{message}
```
NOTE: Respond with ONLY the updated database
"""


ENTITY_DB_QUERY = """ The following is the teams knowledge base:
```
{database}
```
When someone enters a keyword or a question give them all relevant information.

Q: {query}
"""


ENTITY_DB_RELEVANT_CONTEXT = """The following is a knowledge base of all information gathered thus far:
```
{database}
```

The following is a task that given to another AI system:
```
{query}
```

Give the relevant context from your knowledge database to help the other system solve the required task.

IMPORTANT: Respond ONLY with the relevant information and nothing else.
"""

# NOTE: if the agent is capable of doing other things, this should be updated
TASKER_INITIAL_TASKLIST = """Your job is to help break down a goal into smaller executable tasks for your client.
Your client only has access to a basic terminal interface so make sure all tasks are achievable. The goal should be broken down into small easy tasks. DO NOT make the tasks complex.

Below is an example interaction. ALWAYS follow this format for task list!
```
client goal: Scan the local network and identify all devices
Your response:
1. get your current ip address on the network
2. 

Your client has the following goal: {goal}

Make a todolist for your client:
"""
