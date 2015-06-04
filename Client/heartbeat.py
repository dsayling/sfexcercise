"""
Module that encapsulates the multicast heartbeat class
Sends a JSON blob containing the client id and the current time
"""
__author__ = 'dayling'

import socket
import time
import json


class Heartbeat(socket.socket):
    """
    Class that creates a new MC heartbeat socket
    Inherit from socket class
    :param host: string, multicast address to publish on
    :param port: int, port for above address
    :param client_id: string, unique id for the client that wants to generate a
                      heartbeat
    :param send_interval: int, interval in seconds to send message
    """

    def __init__(self, host, port, client_id, send_interval=5.0):
        socket.socket.__init__(self, socket.AF_INET, socket.SOCK_DGRAM)
        self.setsockopt(socket.IPPROTO_IP, socket.IP_DEFAULT_MULTICAST_LOOP, 0)
        self.host = host
        self.port = port
        self.send_interval = send_interval
        self.client_id = client_id

    def run(self, kill_sig):
        """
        start the heartbeat
        """
        try:
            while kill_sig.empty():
                # dict to use as json blob containing id and time
                json_blob = {"id": self.client_id, "time": time.asctime()}
                # Keep sending the heartbeat until something fails
                while self.sender(json.JSONEncoder()
                                  .encode({"heartbeat": json_blob})):
                    json_blob["time"] = time.time()
                    time.sleep(self.send_interval)
            raise KeyboardInterrupt
        except KeyboardInterrupt:
            print "\rClosing Heartbeat UDP socket"
            self.close()

    def sender(self, message):
        """
        publish the udp message
        :param message: string, message you want to send
        :return: bool, did it work or not
        """
        try:
            self.sendto(message, (self.host, self.port))
            return True
        except IOError:
            print "UDP Socket failed to send message; " \
                  "check ethernet interfaces and restart client"
            return False
