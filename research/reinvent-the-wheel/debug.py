"""
While developing this program there is a lot of
debug output that I need it to print so I can make
sure things are working as intended.

Unfortunately at the same time I cannot allow the
debug output to clutter up stdout as I need it to
see if the program is working as intended.

This file aims to solve this issue by using a socket
to send debug output to a different terminal window.
"""

import socket
import threading

def prints(*args, **kwargs):
    """ Alternate print command that sends data to a different window over a socket """
    sep = kwargs.get("sep", " ")
    end = kwargs.get("end", "\n")
    message = sep.join(map(str, args)) + end

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(('localhost', 9999))
        client_socket.sendall(message.encode('utf-8'))


def _handle_client(client_socket):
    """ Handle output from client """
    while True:
        msg = client_socket.recv(1024)
        if not msg:
            break
        print(msg.decode('utf-8'), flush=True, end="")

def _server():
    """ Listen for new connections """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 9999))
    server_socket.listen(5)

    while True:
        client, _ = server_socket.accept()
        client_handler = threading.Thread(target=_handle_client, args=(client,))
        client_handler.start()


if __name__ == "__main__":
    _server()
