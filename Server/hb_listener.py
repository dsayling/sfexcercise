"""
Module that creates a generic multicast UDP socket that uses a Queue to send
data wherever it needs to go
"""
__author__ = 'dayling'

import socket
import logging


class HeartBeatListener(socket.socket):

    """
    HearBeatListener class
    Inherits from socket.socket object
    :param address: address of multicast group to listen on
    :param port: associated port on multicast group to listen on
    """

    def __init__(self, address, port):
        socket.socket.__init__(self, socket.AF_INET, socket.SOCK_DGRAM,
                               socket.IPPROTO_UDP)
        self.bind(('', port))
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                        socket.inet_aton(address) + socket.inet_aton('0'))

    def rec_data(self, data_queue):
        """
        Function to sit and listen on multicast group/port
        This function locks until an EnvironmentError is caught or a
        Keyboard interrupt is received
        :param data_queue: Queue to send data to parent process
        :return:
        """
        try:
            while True:
                buf = self.recv(1024)
                data_queue.put(buf)
        except EnvironmentError as e_string:
            logging.warning("UDP socket failed to receive data: " +
                            e_string.message)
            return None
        except KeyboardInterrupt:
            logging.info("UDP Socket closed")
