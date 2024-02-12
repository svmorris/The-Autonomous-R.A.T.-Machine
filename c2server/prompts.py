EXTENSIVE_REPORTER = """A penetration test report on an IP address consists of the following sub-titles:
- Target information
 General data about the target. This should mainly consist of guesses around what the target could be and what its purpose is.
- Recon information
 Open ports and services running on them. Any extra information that can be reported on from about each service
"""

BASIC_REPORTER = """ A penetration test was conducted on target: {target}.
Below is un-organised information relating to the target:

```
{context}
```

Take only the information that directly relates to the target, and creete a brief report about all information found.
NOTE: Do not include sections such as "recommendations", "fixes", etc. ONLY talk about the data and make assumptions about what the target could be and what its purpose might be.
"""



GUESS_DEVICE_PURPOSE = """You are part of a larger system where each model has a small, specific task. Your job is to guess what the purpose of a device on a scanned network is based on some information provided.

Your target device: {target}

Here are some rules you need to follow:
- Respond only with a few word answer, something like: "Likely a personal laptop", "A server with samba and ngnix running on it.", "An Iphone"
- Use works like "likely" or "probably" if you aren't sure, use more direct language if you are sure of your guess.
- The information given to you, may have data related to other devices. Ignore all data that is not related to your target.
- Respond with ONLY your guess and NOTHING ELSE
- If you cannot make a guess from the data provided, respond with "Unknown"

Here is the data you can use to make your guess:
```
{context}
```
"""



LIST_OPEN_PORTS = """You are part of a larger system where each model has a small, specific task. Your job is to list out all open ports on your target device.

Your target device: {target}

Here are some rules you need to follow:
- Respond only with a bullet point list of ports (as integers) and in brackets what that port could mean (on the same line) NOTING ELSE!
- The information given to you, may have data related to other devices. Ignore all data that is not related to your target.
- You must use the "-" symbol as the bullet point
- If the data indicates that no ports are open, or the data is unclear, respond with "No open ports"

Here is the data you can use to find the open ports:
```
{context}
```
"""



REPORT_SUBTITLES = [
        {"title": "Target information", "keyword": ""},
        {"title": "Recon results", "keyword": "scan"},
        {"title": "Analysis of port x", "keyword": ""},
        {"title": "Vulnerability scan results", "keyword": "vulnerability"},
        {"title": "Conclusion", "keyword": ""},
]

REPORTER_SYSTEM_PROMPT = """Your job is to write a small network scan and Vulnerability analysis report on the target: `{target}`.
You will be writing the report one section (sub-title) at a time to conserve context space. The user will give you a sub-title and some random related notes taken during the pentest. You will use it to write one section of the report.

The final report will consist of these subtitles:
{report_subtitles}

Here are some rules you have to follow:
    - Only write the sub-title that the user has given you, do not continue on before the user can give you related notes to it.
    - The notes given might contain information about other targets. You can safely ignore this. Only focus on your target!
    - If there is not relevant information about your target and sub-title then say "Not enough information"
    - Write only in passive voice.


The report begins below:

# Penetration test report of {target}.
"""
