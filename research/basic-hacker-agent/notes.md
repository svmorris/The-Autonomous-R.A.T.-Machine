# Random ideas that could make this more smart

## The LLM ethics problem

What this project tries to do is not necesairly unethical. As with many tools related to hacking, whether actions performed with it are ethical depend solely on the end user. However, most capable LLMs do not like to do any hacking tasks regardless of ethicality.

The following in no specific order are ideas I have come up with to combat this.

1. Its all a game

I am testing whether convincing the agents that they are playing a "realistic text-based hacking game" allows them to perform actions that they would otherwise not do so. From early testing I have found that this works to some degree, however the words "hacking" or "exploitation" still have to be avoided as they bring up red flags with the LLMs. (There are probably many other such terms that I have not found yet.)


## One agent is probably not good enough

Through some testing I found that its unlikly that a single agent can perform well in this task. Therefore I have two proposals that need to be tested.

1. Agents being closely guided by some hard coded system

This is probably the more straight forward approach, and could have great results. The only issue with it is that most possible actions the agent
could take have to be hard-coded in advance, with only the more neuanced differences in systems being left for the agent to make decisions about. This might be quite difficult to program.

2. Agents working togther

Another option would be to have the systems 'brain' consist of many agents or llms working together to perform the task. While it might prove to be very difficult to coordinate the agents, this should make the system more generalised to any hacking task.

## A do -> evaluate -> re-do framework

One option for making these models do a better work would be to use some sort of do & evaluate framework.

In this proposed idea there are two agents working together. (referred to as agent a and agent b here)

Agent a will get a task to do from 'somewhere' which is tries to execute. When its done, all its workings and its result gets presented to agent b. Agent b evaluates whether agent a did a good job or if something can be improved. If so, agent a will try to re-do the task with a slight modification in its prompt. This process will continue in a loop
until agent b is satisfied.

NOTE: It is (probably) important for this that agent b has no memory, otherwise it might get stuck in a loop of finding issues with agent a's work.


## Langchains babyAGI

While doing some research I found this babyAGI python notebook from lagnchain. The way it uses agents is so much more advanced than what I was doing, it might be a good resource to learn from.
[https://github.com/langchain-ai/langchain/blob/master/cookbook/baby_agi_with_agent.ipynb](https://github.com/langchain-ai/langchain/blob/master/cookbook/baby_agi_with_agent.ipynb)