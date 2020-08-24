## SF Interview Assignment

Request from SF was to build a client-server model app. The client measures "disk performance" and then reports that back to the central server. 
Heartbeats for the clients are sent over mulitcast UDP since I loved using it from my prior job. See [the Requirements](#requirements)

## Usage

Writes all incoming reports from clients to a 'database'.
Logs incoming reports, heartbeats, performance stats, client connection
timeouts. It also provides a profile report at the end of the session.

The server will wait 30 before shutting down if no clients connect and after the last client drops off.
If another client connects the timer resets.

```
#!plain

usage: server.py [-h] -a HB_ADDRESS -p HB_PORT -t TCP_PORT [-d DATABASE]
                 [-l LOG]


python server.py -a 239.0.0.1 -p 10001 -t 42000



arguments:
  -h, --help            show this help message and exit
  -a HB_ADDRESS, --hb_address HB_ADDRESS
                        The multicast address to listen. (default: None)
  -p HB_PORT, --hb_port HB_PORT
                        The multicast port to listen on. (default: None)
  -t TCP_PORT, --tcp_port TCP_PORT
                        The tcp port to listen for clients. (default: None)
  -d DATABASE, --database DATABASE
                        The database file location. Default (default: test_db)
  -l LOG, --log LOG     The log file location (default: info_server.log)

```

Client starts up data writer, heartbeat, and messenger
    The client monitors the data_writer thread and sends that to the server as 
    well as the data writing performace. THe Client will also run for a specfied amount of time.


Create as many clients as necessary

```
#!plain

usage: client.py [-h] [-id ID] -a HB_ADDRESS -p HB_PORT -sh SERVER_HOST -t
                 SERVER_PORT [-hb HEART_BEAT] [-c CHUNK_SIZE] [-f FILE_SIZE]
                 [-rt RUN_TIME] [-path PATH] [-dd]

optional arguments:
  -h, --help            show this help message and exit
  -id ID                Client ID. If not included a new uuid will be
                        generated (default: None)
  -a HB_ADDRESS, --hb_address HB_ADDRESS
                        The multicast address to publish heartbeats (default:
                        None)
  -p HB_PORT, --hb_port HB_PORT
                        The multicast port publish heartbeats (default: None)
  -sh SERVER_HOST, --server_host SERVER_HOST
                        The tcp port the server is listening. (default: None)
  -t SERVER_PORT, --server_port SERVER_PORT
                        The tcp port the server is listening. (default: None)
  -hb HEART_BEAT, --heart_beat HEART_BEAT
                        Heartbeat send interval (default: 5)
  -c CHUNK_SIZE, --chunk_size CHUNK_SIZE
                        The data chunk size in bytes (default: 10000000)
  -f FILE_SIZE, --file_size FILE_SIZE
                        The data chunk size in bytes (default: 20000000)
  -rt RUN_TIME, --run_time RUN_TIME
                        Runtime (default: 10)
  -path PATH, --path PATH
                        Path to write the testfiles defaults to
                        ./client_id/Chunkfiles (default: /)
  -dd                   Use the dd command for the disk testing (default:
                        False)
```

# Requirements

## Story
The customer wants to compare the performance of various storage solutions on their network. You are
tasked with creating a distributed storage benchmark tool consisting of two parts, a client and a server. The
client program measures the performance of locally mounted disks and submits the the results back to the
server. The server will maintain a central database of benchmark runs. 


## Master/Server Requirements:

* Needs to handle concurrent client connections.
	* Writes client performance data to database. Database choice is up to you.
	*￼Logs client "heartbeat" status and other messages to log file.
	*￼When all clients have finished, writes out a report with some general usage, if a client went away, perf stats, etc. then exits.

## Client Requirements:

* Minimum of 3 clients running at the same time - they can all be running locally.
* Each client should run for a configurable length of time and then shut itself down.
* Client should log start/stop messages and those messages will need to be sent to the server.
* Each client will have several threads/processes running, with a minimum of the following:-
	* 1st thread/process will write data in "chunks" to a file on the filesystem.
		* The "chunk" size should be configurable but some reasonable minimum like 10MB - start each client should with a different "chunk" size.
		* When the data file gets to a configurable size, rollover the data file, IE: stop writing, save file, start writing to a new file.
		* The client should run long enough for the data file rollover at least 2 times.
		* The client should complain on startup if the run time configured and the "chunk" size configured do not allow you to rollover a minimum of 2 times.
		* A message should be logged to the client and a message should be sent to the server when a data file rolls over.
	* 2nd thread/process is to report CPU & memory information on the "data" thread/process to the server at approximately 10 second intervals.
	* 3rd thread/process will report a "heartbeat" status to the server at approximately 5 second intervals.


## Additional considerations

* Create a client to interact with the database
* Disk size. If the disk is getting close to full it may be useful to stop

## Issues

* Currently the client does not ensure the data file will roller over at least two times in the run time.
	* The only option I could think of would require running a dd command, check the write speed, do the math and 'hope' it would make it.
	* There may be a better way to do this. Need some time to think on it.
* Using a python shelve as a database. Could implement an actual database. Server could be a slow appending to the database when there are concurrent conections
* Disk performance is being measured using python file objects or using a system call to the dd.
* Any tcp connection to the server on the assigned port would break the server. Additional error handling would be necessary to kill off the client
* Server shutdown timeout is hardcoded as a magic number. Should probably be allowed configurable.
* Client doesn't have a minimum of 10MB but defaults to 10MB and would be configurable to more or less
* Client start up takes in an int value of bytes. Should probably allow for K,M,G, etc. modifiers

