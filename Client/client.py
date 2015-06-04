"""
Module to create a client class
From that start the data_writer, heartbeat, messenger
    The client monitors the data_writer thread and sends that to the server as
    well. THe Client will also run for a specfied amount of time.
"""
__author__ = 'dayling'

from multiprocessing import Process, Queue
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from subprocess import check_output, STDOUT
from heartbeat import Heartbeat
from data_writer import DataWriter
from tcp_client import TCPClient
import time
import logging
import json
import thread
import uuid
import Queue as Queue2


class Client(object):
    """
    Client object
    """
    def __init__(self, client_id, server_host, server_port, mc_address,
                 mc_port, send_interval=5, chunk_size=10000000,
                 file_size=10000000*2, run_time=30, test_path='./',
                 dd_method=False):
        """
        :param client_id: string, unique id for the client
        :param server_host: string, ip address/hostname for sever
        :param server_host: string, port server will listen on
        :param mc_address: string, multicast group address to publish heartbeat
        :param mc_port: int, port for multicast group
        :param send_interval: int, heartbeat send interval
        :param chunk_size: int, in bytes, the size to data size to write to a
        file at a time
        :param file_size: int, maximum file size for the writer
        :param run_time: int, self explanatory, ya know
        :param test_path: string, path to write the data files
        :param dd_method: bool, use dd or not for the file writing
        """

        self.client_id = client_id
        self.server_host = server_host
        self.chunk_size = chunk_size
        self.file_size = file_size
        self.run_time = run_time
        self.mc_group = mc_address, mc_port
        self.send_interval = send_interval
        self.test_path = test_path
        # if dd_method is True, dd will be used
        # if dd_method is False, python file object will be used
        self.dd_method = dd_method
        logging.basicConfig(filename=client_id+'.log',
                            format='%(asctime)s %(levelname)s: %(message)s',
                            level=logging.INFO)

        # Unsure on requirements, going to assume worst case
        # Need to check to see if the chunk size and
        # run time will allow two instances of the time to be written
        try:
            # check to see if two chunks can be written to the file
            assert self.file_size/self.chunk_size >= 2

        except AssertionError:
            print "Client chunk size is too small for max file size." \
                  "Please reconfigure"
            exit(1)

        # Create the initial TCP connection
        self.tcp = TCPClient((server_host, server_port))
        self.hb1 = Heartbeat(self.mc_group[0], self.mc_group[1],
                             self.client_id, self.send_interval)
        self.kill_sig = Queue(1)
        self.hb_process = Process(target=self.hb1.run, args=(self.kill_sig,))
        self.hb_process.daemon = True
        self.queue1 = Queue()
        dw1 = DataWriter(self.chunk_size, self.file_size, self.dd_method,
                         self.test_path)
        self.dw_process = Process(target=dw1.run, args=(self.queue1,
                                                        self.kill_sig))
        self.dw_process.daemon = True
        self.dw_process_pid = None

    def start_client(self):
        """
        start the client
        """
        thread.start_new_thread(self.monitor, ())
        thread.start_new_thread(self.run_timer, ())
        self.hb_process.start()
        self.start_writer()

    def start_writer(self):
        """
        start the data writer
        """
        # Start the process for the data writing, chunking, thing,

        self.dw_process.start()
        self.dw_process_pid = self.dw_process.pid
        try:
            while self.kill_sig.empty():
                try:
                    dw_res = self.queue1.get(block=False)
                except Queue2.Empty:
                    continue
                self.tcp.send_data(json.JSONEncoder().encode(
                    {self.client_id:{"operation_time": dw_res[0],
                                     "file_size": dw_res[1],
                                     "chunk_size": self.chunk_size,
                                     "write_speed": dw_res[2]}}))
                logging.info(dw_res)
        except KeyboardInterrupt:
            pass
        finally:
            print "Closing Client"
            # ensure files were deleted
            self.kill_sig.put(True)
            self.dw_process.join()
            logging.info("Client shutting down")
            exit(0)

    def monitor(self):
        """
        monitor the data writier
        """
        try:
            while self.kill_sig.empty():
                if self.dw_process_pid:  # Probably not the best way...
                    time.sleep(10)
                    monitor_m = check_output(['ps', 'p',
                                              str(self.dw_process_pid), '-o',
                                              '%cpu,%mem'], stderr=STDOUT)
                    cpu, mem = monitor_m.splitlines()[1].strip().split()
                    self.tcp.send_data(json.JSONEncoder().encode(
                        {self.client_id+'_Performance': {"cpu": cpu,
                                                         "mem": mem}}))
        except KeyboardInterrupt:
            pass

    def run_timer(self):
        """
        run timer
        """
        timer = 0
        while timer < self.run_time:
            time.sleep(1)
            timer += 1
        print "Timer ran out"
        self.tcp.close()
        self.hb1.close()
        self.kill_sig.put(True)



if __name__ == '__main__':

    M_PARSE = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    M_PARSE.add_argument('-id',
                         help='Client ID. If not included a new uuid will be '
                              'generated')
    M_PARSE.add_argument('-a', '--hb_address', required=True,
                         help='The multicast address to publish heartbeats')
    M_PARSE.add_argument('-p', '--hb_port', type=int, required=True,
                         help='The multicast port publish heartbeats')
    M_PARSE.add_argument('-sh', '--server_host', required=True,
                         help='The tcp port the server is listening.')
    M_PARSE.add_argument('-t', '--server_port', type=int, required=True,
                         help='The tcp port the server is listening.')
    M_PARSE.add_argument('-hb', '--heart_beat', type=int,
                         help='Heartbeat send interval', default=5)
    M_PARSE.add_argument('-c', '--chunk_size', type=int,
                         help='The data chunk size', default=10000000)
    M_PARSE.add_argument('-f', '--file_size', type=int,
                         help='The data chunk size', default=20000000)
    M_PARSE.add_argument('-rt', '--run_time', type=int, help='Runtime',
                         default=30)
    M_PARSE.add_argument('-path', '--path', help='Path to write the test'
                                                 'files defaults to '
                                                 './client_id/Chunkfiles',
                         default='/')
    M_PARSE.add_argument('-dd',
                         help='Use the dd command for the disk testing',
                         action="store_true")
    MAIN_A = M_PARSE.parse_args()

    if not MAIN_A.id:
        MAIN_A.id = uuid.uuid4().__str__()

    CLIENT = Client(MAIN_A.id, MAIN_A.server_host, MAIN_A.server_port,
                    MAIN_A.hb_address, MAIN_A.hb_port, MAIN_A.heart_beat,
                    MAIN_A.chunk_size, MAIN_A.file_size, MAIN_A.run_time,
                    MAIN_A.id+MAIN_A.path, MAIN_A.dd)
    CLIENT.start_client()
