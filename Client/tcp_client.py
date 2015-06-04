"""
Module containing TCPClient class to make a send only connection to the server
Data only flows from this client
"""
__author__ = 'dayling'

import socket


class TCPClient(socket.socket):
    """
    TCP Client class that simply connects to a host and port and sends the data
    :param (host, port): (string, int) host and port to connect to
    """

    def __init__(self, (host, port)):
        socket.socket.__init__(self, socket.AF_INET, socket.SOCK_STREAM)
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.connect((host, port))
        except socket.error:
            print "Connection to server cannot be established"
            exit(0)

    def send_data(self, message):
        """
        After connection has been establish, just send the data
        If server is shutdown, Client will shut down
        :param message: object to send
        :return: None
        """
        try:
            self.sendall(message)
        except socket.error:
            self.close()
            raise KeyboardInterrupt
