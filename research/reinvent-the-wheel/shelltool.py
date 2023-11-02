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

class ExecutionSandbox:
    """ A thread to run the sandbox environment """

    def __init__(self, sandbox="podman", container="autonomous-rat-machine"):
        self.sandbox = sandbox
        self.container_thread = None
        self.container_name = container
        self.running_name = "rat-machine-sandbox"

        if self.sandbox == "docker":
            self._warn_root_access()

        self._assert_command_exists(self.sandbox)



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
            subprocess.run(
                [
                    self.sandbox,
                    "run",
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

    def run(self, command: str) -> Tuple[str,str,bool]:
        """
            Run a command in the sandbox

            Args:
                - command (string): the command to run

            Returns:
                - stdout
                - stderr
                - bool: true if command ran, false if it didn't
                        If this is false, then neither stdout or error
                        should have anything as it means the command didn't
                        even have a chance to run and there is an error with
                        the sandbox.
        """

        if self.container_thread == None:
            print("Starting sandbox")
            self.start_sandbox()

        try:
            with subprocess.Popen(
                    [
                        self.sandbox,
                        "exec",
                        "-it",
                        self.running_name,
                        "bash",
                        "-c",
                        command # TODO: make sure this is not exploitable
                        ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    ) as process:

                stdout, stderr = process.communicate()
                return (stdout.decode(), stderr.decode(), True)

        except Exception as err: # pylint: disable=broad-exception-caught
            print(f"Failed to run command with error: {err}")
            return ("", "", False)



if __name__ == "__main__":
    sandbox = ExecutionSandbox()

    try:
        while True:
            stdout, stderr, ran = sandbox.run(input(">>"))
            if ran:
                print(stdout)
                print(stderr)
            else:
                print("Failed to run command")

    except KeyboardInterrupt:
        sandbox.kill_sandbox()
        time.sleep(3)
