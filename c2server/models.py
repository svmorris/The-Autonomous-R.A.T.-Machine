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
