from socket import *
import sys
import math
import threading
import time

# --- global variables ---
# command line variables
portNumberOfTheRouter = 0

# program constants
PORT_NUMBER_START_ANCHOR = 3000
INFINITY = math.inf
IP_ADDRESS = "127.0.0.1"
TIMEOUT_DURATION = 5
VECTOR_DELIMITER = "-"

# thread lock variables
# Create a lock
lock = threading.Lock()

# program variables
totalNumberOfRoutersInTheNetwork = 0
distanceTable = []
connectionSockets = []

def getIndexInDistanceTable(port_number):
	return (port_number % PORT_NUMBER_START_ANCHOR)

def getCommandLineArguments():
	# declare global variables
	global portNumberOfTheRouter

	# get the argument number
	cmdArgNumber = len(sys.argv) - 1
	# if the argument number is not equal to 1
	# compare with 2 because program name is also count as an argument
	if (cmdArgNumber != 1):
		print("ERROR: 1 argument expected, but", cmdArgNumber, "is given!")
		# terminate the program
		exit(1)
	# if the given argument number is correct
	else:
		# assign the port number of this router
		portNumberOfTheRouter = int(sys.argv[1])

def getNeighborInformation():
	# declare global variables
	global portNumberOfTheRouter
	global totalNumberOfRoutersInTheNetwork

	filePath = str(portNumberOfTheRouter) + ".costs"
	# open the .costs file of this router (with read mode)
	f = open(filePath, 'r')

	# read the file line by line
	lines = f.readlines()

	# close the file
	f.close()

	# assign total number of routers in the network
	totalNumberOfRoutersInTheNetwork = int(lines[0][:-1])

	# declare a list to return neighbors port number and the strict distance
	neighborInformation = []

	# fill in the neighborInformation
	linesLength = len(lines)
	for i in range(1, linesLength):
		modifiedElement = lines[i][:-1]
		modifiedElement = modifiedElement.split()
		for j in range(2):
			modifiedElement[j] = int(modifiedElement[j])
		modifiedElement = tuple(modifiedElement)
		neighborInformation.append(modifiedElement)

	return neighborInformation

def createDistanceTable(neighborInformationArg, numOfRouters):
	distanceTable = []
	# initialize distance table with infinity values
	for i in range(numOfRouters):
		row = []
		for j in range(numOfRouters):
			row.append(INFINITY)
		distanceTable.append(row)

	# set the distance from our node to our node to 0
	distanceTable[getIndexInDistanceTable(portNumberOfTheRouter)][getIndexInDistanceTable(portNumberOfTheRouter)] = 0

	# modify the distance table using neighbor information
	neighborInformationArgLength = len(neighborInformationArg)
	for i in range(neighborInformationArgLength):
		port_number_of_tuple = neighborInformationArg[i][0]
		distance_value_of_tuple = neighborInformationArg[i][1]
		distanceTable[getIndexInDistanceTable(portNumberOfTheRouter)][getIndexInDistanceTable(port_number_of_tuple)] = distance_value_of_tuple

	return distanceTable

def createRoutersDistanceVector(distance_table):
	global portNumberOfTheRouter
	distance_vector_of_our_router = distance_table[getIndexInDistanceTable(portNumberOfTheRouter)]
	return distance_vector_of_our_router

def encodeRoutersDistanceVectorToString():
	global portNumberOfTheRouter
	global distanceTable

	# get the distance vector of our router as a list
	distance_vector = createRoutersDistanceVector(distanceTable)
	
	# add our routers port number to the string
	string_distance_vector = str(portNumberOfTheRouter) + " "

	for i in range(len(distance_vector)):
		# if this is the last element of the routers distance vector
		if (i == len(distance_vector) - 1):
			# add this element without space
			string_distance_vector = string_distance_vector + str(distance_vector[i]) + VECTOR_DELIMITER
		# otherwise
		else:
			string_distance_vector = string_distance_vector + str(distance_vector[i]) + " "

	return string_distance_vector

def decodeDistanceVectorFromString(given_distance_vector_string):
	given_distance_vector = given_distance_vector_string.split()
	source_router = int(given_distance_vector[0])
	result_distance_vector = given_distance_vector[1:]
	result_distance_vector_length = len(result_distance_vector)
	for i in range(result_distance_vector_length):
		if (result_distance_vector[i] == "inf"):
			result_distance_vector[i] = INFINITY
		else:
			result_distance_vector[i] = int(result_distance_vector[i]) # error
	return (source_router, result_distance_vector)

def updateDistanceTable(index, row_to_be_inserted):
	global distanceTable
	global portNumberOfTheRouter

	# insert the row
	distanceTable[index] = row_to_be_inserted

	### update our distance vector according to the recently inserted row ###
	# get the index of our distance vector in distance table
	our_routers_index = getIndexInDistanceTable(portNumberOfTheRouter)

	# if the source port of the message is 3005, then save the current cost from us to that router
	cost_from_our_router_to_the_source_router = distanceTable[our_routers_index][index]

	is_updated = False

	# loop over the columns of the our router's distance vector
	for i in range(totalNumberOfRoutersInTheNetwork):
		temp = min(cost_from_our_router_to_the_source_router + distanceTable[index][i], distanceTable[our_routers_index][i])
		if (distanceTable[our_routers_index][i] != temp):
			# update the cell
			distanceTable[our_routers_index][i] = temp
			is_updated = True
			continue
	
	return is_updated

def advertiseDistanceVector(encoded_distance_vector):
	global connectionSockets
	number_of_connection_sockets = len(connectionSockets)
	for i in range(number_of_connection_sockets):
		connectionSockets[i].send(encoded_distance_vector.encode())
	
# thread function
# peer_port_number parameter is only for logging purposes
def communicate(connectionSocket, peer_port_number):
	global portNumberOfTheRouter

	received_empty_message_number = 0

	#### create and encode the initial distance vector of our router ####
	# get the lock for this thread because we want to access the distance table (read)
	lock.acquire()
	# create and encode the initial distance vector of our router
	initial_distance_vector_of_our_router = encodeRoutersDistanceVectorToString()
	# release the lock
	lock.release()
	####

	#### send the initial distance vector of our router ####
	# get the lock for this thread because we want to use the connection socket (send)
	#lock.acquire()
	# send the initial distance vector of our router
	connectionSocket.send(initial_distance_vector_of_our_router.encode())
	connectionSocket.settimeout(TIMEOUT_DURATION)
	#lock.release()
	####

	
	while True:
		try:
			# get the lock for this thread because we want to use the connection socket (send)
			#lock.acquire()
			# attempt to receive message from the neighbor
			# if any message does not come within connection_socket_timeout interval, the connection socket throws an exception
			received_message = connectionSocket.recv(4096).decode()
			#lock.release()
		except timeout:
			#lock.release()
			# any message from the neighbor does not come within connection_socket_timeout interval
			# print an error message
			break
		else:
			# a message has been received from the neighbor peer
			# check if the message received is empty
			if (len(received_message) == 0):
				if (received_empty_message_number == 5):
					break
				else:
					received_empty_message_number += 1
					continue
			


			#### test ####
			received_message = received_message[:-1]
			received_message = received_message.split(VECTOR_DELIMITER)
			for k in range(len(received_message)):
			#### test ####

				# decode the received message
				source_port, received_distance_vector = decodeDistanceVectorFromString(received_message[k])
			
				### make your updates on our router's distance table ###
				# get the index to be updated from the distance table
				distance_row_index_to_be_updated = getIndexInDistanceTable(source_port)
				# get the lock for this thread because we want to access the distance table (write / update)
				lock.acquire()
				# update the distance table
				# if there is no change, False will be returned
				# if there is a change, True will be returned
				is_distance_table_updated = updateDistanceTable(distance_row_index_to_be_updated, received_distance_vector)
				# release the lock
				lock.release()
			
				# if there is an update in teh distance table
				if (is_distance_table_updated):
					# get the lock for this thread because we want to access the connection sockets (advertisement)
					lock.acquire()
					### advertise our distance vector to all neighbors ###
					# create and encode the initial distance vector of our router
					initial_distance_vector_of_our_router = encodeRoutersDistanceVectorToString()
					lock.release()
				
					# advertise it
					advertiseDistanceVector(initial_distance_vector_of_our_router)

			# continue listening
			continue
	
	# close the connection socket
	connectionSocket.close()
	
# thread function
def connectToNeighbor(neighbor_port_number):
	global IP_ADDRESS
	global portNumberOfTheRouter
	global connectionSockets

	# check if there is an incorrect call for this function
	if (portNumberOfTheRouter == neighbor_port_number):
		print("Router " + str(portNumberOfTheRouter) + ": " + "ERROR: attemt to connect to the current router!")
		exit(1)

	#### create a proper TCP socket to interact with the given neighbor ####
	# the port number of this socket is assigned by the operating system
	connectionSocket = socket(AF_INET, SOCK_STREAM)

	# Set the SO_REUSEADDR option on the socket
	connectionSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

	# set timeout for socket
	connectionSocket.settimeout(TIMEOUT_DURATION)
	####

	# try to connect to the neighbor until making a connection successfully
	while True:
		try:
			# attempt to connect to the neighbor
			connectionSocket.connect((IP_ADDRESS, neighbor_port_number))
		except error:
			# if the connection fails, print an error message and continue the loop
			continue
		else:
			# if the connection succeeds, break out of the loop
			break
	
	#### add the connection socket to the connection sockets list ####
	lock.acquire()
	connectionSockets.append(connectionSocket)
	lock.release()
	####

	# start a thread for this new connection of the certain router pair
	newThread = threading.Thread(target = communicate, args = (connectionSocket, neighbor_port_number, ))
	newThread.start()

	#### wait for the created thread to terminate ####
	if (newThread.is_alive()):
		newThread.join()
	####

# thread function
# this function will be called once in the router
# it will handle every connection requests
# for every new connection established in this function, the function will create a new communication thread
# every thread created by this function will be responsible for one router pair
def connectByNeighbor():
	global portNumberOfTheRouter
	global totalNumberOfRoutersInTheNetwork
	global connectionSockets

	# create a threadlist to save all threads started by this function
	threadList = []

	# create a TCP socket to interact with the given neighbor
	routerConnectionRequestReceiverSocket = socket(AF_INET, SOCK_STREAM)

	# Set the SO_REUSEADDR option on the socket
	routerConnectionRequestReceiverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

	# set a timeout for the socket
	routerConnectionRequestReceiverSocket.settimeout(TIMEOUT_DURATION)

	# Set a flag to track whether the router socket is still open
	is_router_socket_open = True

	# bind the created socket to the routers port number
	routerConnectionRequestReceiverSocket.bind(('', portNumberOfTheRouter))

	# start listening for connection requests coming from routers that has lower port number
	# maximum number of queued connections is specified as the total number of routers in the network
	routerConnectionRequestReceiverSocket.listen(totalNumberOfRoutersInTheNetwork)

	# when a connection request came, accept it and start communication for this pair
	# and then, wait for another connection request
	while is_router_socket_open:
		try:
			# attempt to accept the connection request if there is
			# if there is no any queued connection request, the thread will wait on this statement until a connection request arrives or timeout occurs
			# connectionSocket is a new socket dedicated to serve the communication between a certain router pair
			connectionSocket, addr = routerConnectionRequestReceiverSocket.accept()
		except timeout:
			# if no connection request is received in the timeout period, close the router socket
			routerConnectionRequestReceiverSocket.close()
			is_router_socket_open = False
			break
		else:
			# a connection request is received

			### add the new connection socket to the connection sockets list
			lock.acquire()
			connectionSockets.append(connectionSocket)
			lock.release()
			###

			# start a thread for this new connection of the certain router pair
			newThread = threading.Thread(target = communicate, args = (connectionSocket, 0))
			newThread.start()
			
			# add this communicate thread to the list of threads started by this function 
			threadList.append(newThread)

			# continue the loop for new connection requests
			continue

	### wait for all threads started by this function to to terminate
	# save the length of the thread list
	threadListLength = len(threadList)
	# for all threads started by this function
	for j in range(threadListLength):
		# if the current thread is still running
		if (threadList[j].is_alive()):
			# wait for it to terminate
			threadList[j].join()
		# otherwise
		else:
			# skip to the next thread in the thread list
			continue
	###


def establishConnectionsWithNeighbors(neighborInformationArg):
	global portNumberOfTheRouter

	threadList = []

	# start a thread waiting for connection requests from routers that has lower port number
	connectionRequestReceiverThread = threading.Thread(target = connectByNeighbor, args = ())
	connectionRequestReceiverThread.start()

	# append this thread to the thread list
	threadList.append(connectionRequestReceiverThread)

	# save neighbor number
	neighborInformationArgLength = len(neighborInformationArg)

	# for all neighbors
	for i in range(neighborInformationArgLength):

		# save neighbor port number
		neighbor_port = neighborInformationArg[i][0]

		# if an unexpected situation happened
		if (portNumberOfTheRouter == neighbor_port):
			print("Router " + str(portNumberOfTheRouter) + ": " + "ERROR!")
			exit(1)

		# if our router has a lower port number
		elif (portNumberOfTheRouter < neighbor_port):
			# this router initiates the TCP connection
			# start a thread initiating connection to the neighbor router
			connectionInitiatorThread = threading.Thread(target = connectToNeighbor, args = (neighbor_port, ))
			connectionInitiatorThread.start()

			# add the thread to the thread list
			threadList.append(connectionInitiatorThread)
		
		# if this router has a greater port number
		else:
			# this router will wait for a connection request from its neighbor
			# we have handled this at the beginning of this function in connectByNeigbor() call
			# this means do nothing
			continue

	### wait for the threads started by this function to end
	# save the length of the thread list
	threadListLength = len(threadList)
	# for all threads started by this function
	for j in range(threadListLength):
		# if the current thread is still running
		if (threadList[j].is_alive()):
			# wait for it to end
			threadList[j].join()
		# otherwise
		else:
			# pass to the next one
			continue


### MAIN PROGRAM ###
getCommandLineArguments()

neighborInformation = getNeighborInformation()

distanceTable = createDistanceTable(neighborInformation, totalNumberOfRoutersInTheNetwork)

### create TCP connections with all neighbors to send and receive packets asynchronously
establishConnectionsWithNeighbors(neighborInformation)

final_distance_table = distanceTable[getIndexInDistanceTable(portNumberOfTheRouter)]

for i in range(len(final_distance_table)):
	to = PORT_NUMBER_START_ANCHOR + i
	print(str(portNumberOfTheRouter) + " - " + str(to) + " | " + str(final_distance_table[i]))