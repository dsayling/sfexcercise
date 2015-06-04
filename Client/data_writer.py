"""
Module containing a class for writing data to a disk
Class can be used to write data using the 'dd' utility on unix systems or
using the built in python file object.
    The 'dd' utility gives a much more accurate representation of the disk
    performance as the rollover occurs with out the delay in python
"""
__author__ = 'dayling'

from subprocess import check_output, STDOUT
import os
import shutil
import time
import platform


class DataWriter(object):
    """Class that writes data to a specified path
    After initialization, class should be run as a separate process to keep the
    time between operations as low as possible
    :param chunk_size: int, bytes size of data written to the disk at a time
    :param file_size: int, bytes size of the file that should be written
                      (i.e., when the next chunk reaches this size,
                      begin a new file)
    :param use_dd: bool, if True: use 'dd', if False: use file object, defaults
                   False
    :param test_path: string, same location on file system to write the data,
                      defaults to running directory
    """

    def __init__(self, chunk_size, file_size, use_dd=False, test_path='./'):
        self.chunk_size = chunk_size
        self.file_size = file_size
        self.block_count = file_size/chunk_size
        self.use_dd = use_dd
        self.is_darwin = False
        if platform.system() == 'Darwin':
            self.is_darwin = True

        self.test_path = test_path+'chunkfiles/'

    def run(self, write_queue, kill_sig):
        """start writing data to the disk as initialized
        When the client is shutdown, the files that were written will be erased
        :param write_queue: Queue(), send write results to parent
        :para kill_sig: Queue, used to trigger
        """
        counter = 0  # counter for the test files
        if not os.path.exists(self.test_path):
            os.makedirs(self.test_path)
        try:
            while kill_sig.empty():
                counter += 1
                t_file = self.test_path+str(counter)
                if self.use_dd:
                    write_queue.put(self.dd_syscall(t_file))
                else:
                    write_queue.put(self.file_io(t_file))
                time.sleep(.5)
        except KeyboardInterrupt:
            pass
        finally:
            time.sleep(5)  # wait to ensure the other processes have finished
            print "Deleting test files"
            shutil.rmtree(self.test_path)

    def dd_syscall(self, f_write):
        """
        makes a system call to 'dd'; writes from /dev/zero to f_write
        :param f_write: string, filename to write
        :return: runtime, total data_written, write speed
        """
        out = check_output(['dd', 'if=/dev/zero', 'of='+f_write,
                            'bs='+str(self.chunk_size),
                            'count='+str(self.block_count)], stderr=STDOUT)
        print out
        f_out = out.splitlines()[2].split()
        if self.is_darwin:
            return f_out[4], f_out[0], f_out[6].strip('(')+f_out[7].rstrip(')')
        return f_out[5], f_out[0], f_out[7]+f_out[8]

    def file_io(self, f_write):
        """
        Use file object to test disk
        writes '1's to the file in chunks
        :param f_write: string, filename to write
        :return: runtime, total data_written, write speed
        """
        try:
            t_file = open(f_write, 'wb')
            block_c = self.block_count
            s_time = time.time()
            while block_c != 0:
                t_file.write('1'*self.chunk_size)
                block_c -= 1
            t_file.close()
            run_time = time.time() - s_time
            return run_time, self.block_count * self.chunk_size, \
                str(self.block_count * self.chunk_size / run_time) + 'bytes/sec'
        except KeyboardInterrupt:
            return None
