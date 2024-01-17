# The autonomous Rat machine

This repo contains the code for my university dissertation. The project aims to create a fully autonomous agent with the goal of hacking everything it can access on a local network, then providing a backdoor for researchers to access both the network and the hacked devices.


## How to run


#### 1. Build the sandbox

The sandbox is a docker container used so that the agent cannot run commands on the host computer. To run the agent, the sandbox container needs to be built.

First make sure that either docker or podman is installed.
Second, run the build script within the `./sandbox-image` directory. Note, if you use docker, than root privileges are needed to run the agent and the build script

#### 2. Setup python environment and install requirements.txt

Next create a python virtual environment and just install the libraries in the `requirements.txt`.

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r ./requirements.txt
```

NOTE: python 3.10 or above needs to be used.


#### 3. Run debug.py

The program will only work if `./src/debug.py` is running in a separate window. This program will display logs. For the time being the agent wont run without it.

#### 4. Run the agent

In its current state, the main file of the agent is the `hacker.ipynb` notebook in the `./src` folder. In the future there will be a proper main file, but for now this is the only way to use the agent.




# Ideas to implement later

- For work, I created a better way of handing model memory. Instead of the entity DB that exists in this project, there could be a separate model that summarizes all information
collected during a run of the agent, and then gets stored in a standard vector database. This seems to give a lot of well condensed information.


- The above + splitting the database + Tasker based on full context
I think the best way to go about this would be a combination of three new things. Firstly, we replace the entity database with a vector one. Data in the vector database will be only summaries of agents running. (well have to tell the summariser to focus on entities though)
Secondly, a separate database will hold all know targets. This could probably be done with just regex on the range.
Finally, the tasker would have a different way of creating new tasks. Instead of based on the last command, it would go one target at a time, get all relevant info about it and come up with a new task based on the saved info. Due to the way the vector database works, this could lead to some tasks being repeated, but if something gets repeated its more likely to be shown to the tasker anyway.


- Simple error check: Both when the scratchpad doesnt catch commands and when the model decides it cannot complete some "hacking task" no commands are being run. A simple way to re-try such commands would be to check for no commands being run during an agent execution, rephrase the task slightly, and re-run the agent
