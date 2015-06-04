"""
Module containing TCPServer class to maintain multiple client connections
Data only flows to this Server
Class runs a new thread for every remote connection and provides the data in
a Queue as (data, (host_ip, port))
"""
__author__ = 'dayling'

import socket
import thread
import logging


class TCPServer(socket.socket):
    """TCP Server that binds to host and port
    Call run on a thread, process or in a loopo
    :param host: string, address to listen on (typically '' for any interface)
    :param port: int, port to listen on on
    """

    def __init__(self, host, port):
        socket.socket.__init__(self, socket.AF_INET, socket.SOCK_STREAM)
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = host
        self.port = port
        self.bind((self.host, self.port))
        self.listen(32)

    def run(self, data_queue):
        """
        :param data_queue: Queue(), provide messages to parent process
        :return: None
        """
        while True:
            # server waits for a client to connect, upon connection,
            # new thread begins
            try:
                client, _ = self.accept()
            except KeyboardInterrupt:
                logging.info('Closing Server TCP connection')
                self.close()
                return
            thread.start_new_thread(self.process_client,
                                    (client, data_queue))

    @staticmethod
    def process_client(client, data_queue):
        """Receives and queues the data to the server
        :param client: socket._object, where the connection was made
        :param data_queue: Queue(), same from run
        :return: None
        """
        try:
            while True:
                data = client.recv(1024)
                client_ip = client.getpeername()
                if data == '':
                    data_queue.put((None, client_ip))
                    return
                data_queue.put((data, client_ip))
        except KeyboardInterrupt:
            logging.warning("Server stopped while receiving TCP data")
            return
