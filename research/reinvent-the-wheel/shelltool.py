"""
Agents are unpredictable.
Especially when given the task to hack things they will often run
weird commands, try to download tools, etc. I don't thin its
particularly wise to run this agent on my main system, both because
it does odd things and as I don't feel comfortable giving it root
access to install things.

The goal of this library is to create a command executor like langchains
ShellTool, but entirely in a sandbox environment using podman. (or docker, but I don't prefer that)
"""


import os
import time
import threading
import subprocess
from typing import Tuple

from debug import prints

class ExecutionSandbox:
    """ A thread to run the sandbox environment """

    def __init__(self, sandbox="podman", container="rat-machine-image"):
        self.sandbox = sandbox
        self.container_thread = None
        self.container_name = container
        self.running_name = "rat-machine-sandbox"

        if self.sandbox == "docker":
            self._warn_root_access()

        self._assert_command_exists(self.sandbox)

        # Extra description stuff
        self.name = "terminal"
        self.description = "Run shell commands on this Linux machine."


    @staticmethod
    def _assert_command_exists(command):
        try:
            # Trying to run the program
            subprocess.run(
                    [
                        command,
                        "--version"
                        ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
            # If the above command does not raise an exception, the program is installed
            return True
        except subprocess.CalledProcessError:
            assert False, f"{command} is not installed or is not working correctly"
        except FileNotFoundError:
            assert False, f"{command} is not installed."


    @staticmethod
    def _warn_root_access():
        if os.geteuid() == 0:
            print("WARNING: application being run as root may be dangerous")
        else:
            print("WARNING: Docker may not work if not running as root.")



    def _assert_image_availability(self, image_name: str):
        """ Make sure the container image set up for this project is available """

        try:
            # Get all docker images
            result = subprocess.run(
                [
                    self.sandbox,
                    "images",
                    "--format",
                    "{{.Repository}}:{{.Tag}}"
                 ],
                capture_output=True,
                text=True,
                check=True
            )

            # Splitting the output into lines
            available_images = result.stdout.strip().split('\n')

            if image_name not in available_images:
                print(
                        "Cannot run the sandbox without the container"\
                        f"image: {image_name}. If if not built yet, there"\
                        "should be a dockerfile for the image included with"\
                        "the project"
                    )
                assert False, f"Image '{image_name}' does not exists"

        except Exception as err: # pylint: disable=broad-exception-caught
            assert False, f"Critical error while checking image availability: {err}"

    def _container_thread(self):
        """ A threaded function that runs the container """
        try:
            # TODO: There is a bug here I'm struggling to Fix
            #       If you run the podman without the --network
            #       option than its IP address will be in a different
            #       range as the host computer. This might confuse the
            #       system not knowing what subnet to scan.

            #       If however you do add this host, some bug on my computer
            #       does not allow me to run tools like nmap.

            #       I was hoping to fix this by creating a separate macvlan
            #       for the rat machine but I am struggling to do it as of now.
            subprocess.run(
                [
                    self.sandbox,
                    "run",
                    "--cap-add=NET_RAW",
                    "--cap-add=NET_ADMIN",
                    # "--network",
                    # "host",
                    # "--add-host=host_ip_address:host-gateway",
                    "--name",
                    self.running_name,
                    "--rm",
                    self.container_name
                    ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )

        except Exception as err: # pylint: disable=broad-exception-caught
            print(f"Container exited with error {err}")
            assert False, "Execution sandbox failed to run"


    def start_sandbox(self):
        """ Start the container """
        self.container_thread = threading.Thread(target=self._container_thread)
        self.container_thread.start()
        # Make sure the sandbox has time to start before executing commands
        time.sleep(2)

    def kill_sandbox(self):
        """ kill the container """
        self.run("rm /stop-flag")
        self.container_thread = None


    @staticmethod
    def _command_filter(command: str) -> (str, bool):
        """
           The language model does not know that its in a docker container
           where it already has root (but the sudo command does not exist)
           and where it cannot interact with commands like apt.

           This function is supposed to be a simple filter to clean up some
           common errors from commands by GPT. It obviously won't solve
           everything, but some errors are so common I might as well plan
           for them.

           This method is also not foolproof for chaining commands, however,
           I don't think that any of the filtered commands would be in chains
           very often.

           Returns:
               - str: filtered command
               - bool: if true, needs to be run on host instead of container
                       NOTE: this must only be true on commands known to be safe

           """
        run_on_host = False

        command = command.strip("\n")
        command = command.strip(" ")

        # Make sure we remove any sudo's bc we are already root
        # and the command does not exist in the sandbox.
        if command.startswith("sudo "):
            command = command[5:].strip(" ")

        # Make sure that apt is not waiting for input
        if command.startswith("apt") and " -y " not in command:
            command += " -y"

        if command.startswith("nmap"):
            if "-sn" in command:
                # Ping commands need raw packets so that they work within the docker container
                command = command.replace("-sn", "-PO -sn")

        # Need to get the host IP addresses
        if command in ("ip a", "ifconfig"):
            run_on_host = True

        return command, run_on_host


    def run(self, command: str) -> str:
        """
            Run a command in the sandbox

            Args:
                - command (string): the command to run

            Returns:
                - string: output of the command or a string explaining that it didn't work.
                          As we are working with language models, the string explaining that
                          the terminal does not work is actually better than just crashing.
        """

        if self.container_thread is None:
            prints("Starting sandbox")
            self.start_sandbox()

        # Fix some common command issues
        command, run_on_host = self._command_filter(command)

        try:
            command_arr: list = []
            # If the command needs to be run on host, then do not include the
            # sandbox arguments
            if run_on_host:
                command_arr = command.split(" ")
                # Need to make sure this is a list
                if isinstance(command_arr, list) is False:
                    command_arr = [command_arr]

            # Include the sandbox arguments
            else:
                command_arr = [
                            self.sandbox,
                            "exec",
                            "-it",
                            self.running_name,
                            "bash",
                            "-c",
                            command
                            ]

            with subprocess.Popen(
                    command_arr,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    ) as process:

                stdout, _ = process.communicate()
                return str(stdout.decode())

        except Exception as err: # pylint: disable=broad-exception-caught
            print(f"Failed to run command with error: {err}")
            return f"Terminal failed to run with error: {err}"



if __name__ == "__main__":
    sandbox = ExecutionSandbox()

    try:
        while True:
            stdout = sandbox.run(input(">> "))
            print(stdout)

    except KeyboardInterrupt:
        sandbox.kill_sandbox()
        time.sleep(3)
