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
