"""
Server module that contains the Server class.
Writes all incoming reports from clients to a 'database'.
Logs incoming reports, heartbeats, performance stats, client connection
timeouts, and runtime.
Server will wait 30 seconds for an initial client to connect before shutting
down. Once all clients have disconnected the server will wait another 30
seconds in case another client attempts to connect
"""
__author__ = 'dayling'

from tcp_server import TCPServer
from hb_listener import HeartBeatListener
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import shelve
import thread
import time
import multiprocessing
import json
import anydbm
import logging
import logging.handlers
import cProfile
import pstats


class Server(object):
    """
    Server
    """

    def __init__(self, mc_listen_addr, mc_listen_port, tcp_port, db_location,
                 log_location):
        """
        :param mc_listen_addr: string, multicast address
        :param mc_listen_port: int, multlicast port
        :param tcp_port: int, port to accept tcp connections
        :param db_location: string, database (shelf) location
        :param log_location: string, log file location
        """
        # create a log file for the server
        logging.basicConfig(filename=log_location,
                            format='%(asctime)s %(levelname)s: %(message)s',
                            level=logging.INFO)

        self.client_list = []
        # While a python shelve is technically a true database, it provides
        # enough functionality without requiring
        # any additional dependencies and is fairly useful for this application
        # Ensure the shelf is not already open
        try:
            self.server_shelf = shelve.open(db_location, writeback=True)
        except anydbm.error:
            e_message = "Server Database is open somewhere else, " \
                        "please close it and restart server"
            print e_message
            logging.error(e_message)
            exit(0)

        # Start the TCPClient listening on available host address
        s_tcp = TCPServer('', tcp_port)
        self.tcp_queue = multiprocessing.Queue()
        self.s_tcp_proc = multiprocessing.Process(target=s_tcp.run,
                                                  args=(self.tcp_queue, ))
        self.s_tcp_proc.daemon = True

        # Start the UDP Heartbeat listener
        s_hb = HeartBeatListener(mc_listen_addr, mc_listen_port)
        hb_queue = multiprocessing.Queue()
        self.s_hb_proc = multiprocessing.Process(target=s_hb.rec_data,
                                                 args=(hb_queue, ))
        self.s_hb_proc.daemon = True

    def run_server(self):
        """
        Actually run the server
        Starts the heartbeat monitor in one process & the tcp socket in another
        Puts the tcp message manager in a separate thread
        Server will start up for and wait for 30 seconds until a client
        makes a connections. Once all clients are gone, the server will wait 30
        more seconds until shutting down.
        :return: None
        """
        self.s_hb_proc.start()

        self.s_tcp_proc.start()
        thread.start_new_thread(self.tcp_listener, (self.tcp_queue, ))
        try:
            # wait for clients to connect
            while True:
                if not self.client_list:  # if there are no clients
                    time.sleep(30)        # wait 30 seconds
                    if not self.client_list:  # if still no clients, break
                        break
        except KeyboardInterrupt:
            pass
        finally:
            shutdown_m = "Server shutting down"
            print shutdown_m
            logging.info(shutdown_m)
            self.server_shelf.close()
            return

    def tcp_listener(self, data_queue):
        """
        Process the data in the queue sent from the process that is
        running the tcp listener socket
        Keep track of connections
        :param data_queue: Queue(), send data to parent process
        :return: none
        """
        while True:
            message, c_ip = data_queue.get()
            if message is None:
                print "Removing Client", c_ip[0], c_ip[1]
                try:
                    self.client_list.remove(c_ip)
                except ValueError:
                    print 'Client connected, but never sent data'
                continue
            log_string = "Message received [RAW] from:", \
                         c_ip[0]+':'+str(c_ip[1]), message
            logging.info(log_string)
            # ensure multiple messages are written individually
            for s_message in message.split('}{'):
                self.write_db(s_message)
            if c_ip not in self.client_list:
                self.client_list.append(c_ip)
                print 'New Client Connected!'
                print "Current Clients:", self.client_list

            # Note the error handling here could drastically be improved. Any
            #  client that connects to the server on this port would break
            # the server

    def write_db(self, message):
        """Decode the json message
        Write the incoming message to the database/shelve by checking the id in
        the message to the keys in the shelve
        :param message: string, as single json blob
        :return: None
        """
        message = json.loads(message)
        c_id = str(message.keys()[0])
        if c_id not in self.server_shelf:
            self.server_shelf[c_id] = [message[c_id]]
        else:
            self.server_shelf[c_id].append(message[c_id])
        return

    @staticmethod
    def udp_data(udp_message):
        """Simple callback to log the heartbeats
        :param udp_message: string, udp message to be logged
        """
        logging.info(udp_message)

if __name__ == "__main__":

    M_PARSE = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    M_PARSE.add_argument('-a', '--hb_address', required=True,
                         help='The multicast address to listen.')
    M_PARSE.add_argument('-p', '--hb_port', type=int, required=True,
                         help='The multicast port to listen on.')
    M_PARSE.add_argument('-t', '--tcp_port', type=int, required=True,
                         help='The tcp port to listen for clients.')
    M_PARSE.add_argument('-d', '--database', help='The database file '
                                                  'location. Default',
                         default='test_db')
    M_PARSE.add_argument('-l', '--log', help='The log file location',
                         default='info_server.log')
    MAIN_A = M_PARSE.parse_args()

    SERVER1 = Server(MAIN_A.hb_address, MAIN_A.hb_port, MAIN_A.tcp_port,
                     MAIN_A.database, MAIN_A.log)

    PRO = cProfile.Profile()
    PRO.enable()
    SERVER1.run_server()
    PRO.disable()
    STATS = pstats.Stats(PRO)
    STATS.sort_stats('cumulative')
    STATS.print_stats(.1)
