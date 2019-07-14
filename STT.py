'''
	Script that sends requests to IBM Watson's STT API and receives the 
	results in json format. Uses multi-threading for multiple speakers

	Part of the Gailbot-3 development project.

	Developed by:

		Muhammad Umair								
		Tufts University
		Human Interaction Lab at Tufts

	Initial development: 5/25/19	

	Changelog:
	1. sterr has been closed to prevent error messages from an unidentified source.
		Error does not cause problems with data generation.
'''

import sys
import json                        # json
import threading                   # multi threading
import os                          # for listing directories
import queue as Queue              # queue used for thread syncronization
import sys                         # system calls
import argparse                    # for parsing arguments
import base64                      # necessary to encode in base64
#                                  # according to the RFC2045 standard
import requests                    # python HTTP requests library
import time 					   # Python timing library
from termcolor import colored					# Text coloring library

# WebSockets
from autobahn.twisted.websocket import WebSocketClientProtocol, \
    WebSocketClientFactory, connectWS
from twisted.python import log	
from twisted.internet import ssl, reactor

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Invariants / Global variables

IBM_host = "stream.watsonplatform.net"				# Name of the IBM host / service.
STT_service = "speech-to-text"						# Speech to Text service name.
IDModels = ["en-US_BroadbandModel",  				# Base models that return speaker ID's
			"en-GB_BroadbandModel",
			"en-US_ShortForm_NarrowbandModel",
			"en-US_NarrowbandModel"]

opt_out_key = "X-Watson-Learning-Opt-Out"			# Opt out key for header sent to STT
Watson_token_key = "X-Watson-Authorization-Token"	# Key for using Watson instead of access tokens for authentication.
Access_token_key = "Authorization"					# Key for using Watson access tokens for authentication.

Audio_chunk_size_bytes = 2000						# Size of Audio Sample that can be sent to Watson in one message.

# Output information tuple
outputInfo = []



# Utility class for communicating for Watson's STT API.
class Utilities:

	# Static and tied to class instead of a specific instance.
	# Function that obtains an authentication token from the service server being
	# connected to
	# Token documentation at: https://cloud.ibm.com/docs/services/watson?topic=watson-gs-tokens-watson-tokens
	@staticmethod
	def getAuthenticationToken(hostname, serviceName, username, password):
		form = "{0}/authorization/api/v1/token?url={0}/{1}/api"				# using cloud foundary tokens for IBM bluemix service.	
		uri = form.format(hostname,serviceName)
		auth = (username,password)
		headers = {'Accept': 'application/json'}
		resp = requests.get(uri,auth=auth,verify=True,headers=headers,
			timeout=(30,30))
		jsonObject = resp.json()			# Converting response into a serialized dictionary.
		if 'token' in jsonObject: return jsonObject['token']	# Returning authentication token recieved from service.
		return None		


# This class acts as a factory for producing instances of the WebSocket protocol.
class WSInterfaceFactory(WebSocketClientFactory):

	# Initializing the WebSocket client factory.
	'''
		url: The WebSocket url the factory is working for / IBM host url.
		headers: Optional headers to send to the url during HANDSHAKING.
		queue : Queue set up for threading.
		dirOutput : Directory to write the output file.
		contentType : Content/Audio Type parameter required by Watson STT service.
		default_model : Specifies the default language model used by Watson STT service.
		protocolQueue : Queue of audio files the client protocol is implemented on.
		customization_weight: Weight given to the custom model vs. the base lnaguage model.
		custom : Indicates if a custom language model is being used.
	'''
	def __init__(self,queue,base_model,customization_weight,
		custom=False,url=None,headers=None,debug=None):

		WebSocketClientFactory.__init__(self,url=url,headers=headers)
		self.queue  = queue
		self.base_model = base_model
		self.customization_weight = customization_weight
		self.custom = custom
		self.protocolQueue = Queue.Queue()

		self.closeHandshakeTimeout = 10										# Expected time for a closing handshake (seconds)
		self.openHandshakeTimeout = 10

		# Defining and starting the thread that ends the script automatically.
		endingThread = threading.Thread(target=self.endReactor, args = ())
		endingThread.daemon = True											# Functions as a daemon in the background.
		endingThread.start()


	# Function that adds the given audio to the queue the client protocol is implemented on.
	def prepareAudio(self):
		try:
			audioSampleInfo = self.queue.get_nowait()					# Getting the first audio file from the queue of audio files to be processed.
			self.protocolQueue.put(audioSampleInfo)						# Adding to the protocol queue.
			return True
		except Queue.Empty:
			print("Empty Queue: No more utterances to process")
			return False

	# Function that controls the daemon for ending the thread.
	def endReactor(self):
		self.queue.join()					# Stops progression until all queue items have been processed.
		print("Stopping reactor")
		reactor.stop()						# Ending the reactor for the twisted interface.

	# This function gets called every time connectWS is called (once
    # per WebSocket connection/session)
    # Part of the twisted.internet library.
	def buildProtocol(self,addr):
		try:
			audioSampleInfo = self.protocolQueue.get_nowait()			# Getting audio sample information to be sent to service.
			protocol = WSInterfaceProtocol(self,self.queue, 
				self.customization_weight,self.custom,self.base_model)
			protocol.finalCheck(audioSampleInfo)						# Performing final checks before sending Audio sample.
			return protocol
		# The Queue should never be empty.
		except Queue.Empty: return None





# WebSockets interface to the STT service
# Object is created for every Websocket connection.
class WSInterfaceProtocol(WebSocketClientProtocol):

	'''
		factory: The instance of the WebSocket factory the client protocol is running under.
		queue : Queue set up for threading.
		dirOutput : Directory to write the output file.
		contentType : Content/Audio Type parameter required by Watson STT service.
		chunkSize : Size of audio chunk being sent to Watson.
		bytesSent : Audio data in bytes already sent to Watson.
		sampleName : Name of the sample.
		sampleNumber : Number of the sample.
		jsonFile : Name of the JSON file.
		custom : Indicates if a custom language model is being used.
	'''
	def __init__(self, factory, queue,customization_weight,
		custom,base_model):
		self.factory = factory 								# Current Factoy Protocol.
		self.queue = queue 									# Initial queue set up for threading.
		self.listening_state_count = 0						# Count for the number of state messages recieved.
		self.json_output = []								# List of all json outputs recieved.
		self.chunkSize = Audio_chunk_size_bytes
		self.bytesSent = 0
		self.customization_weight = customization_weight
		self.custom = custom
		self.resultIndex = 0
		self.base_model = base_model
		super(self.__class__,self).__init__()				# Initializing the current class and the parent class.

	# Function to performs a final check before audio sample is sent.
	def finalCheck(self,audioSampleInfo):
		self.names = audioSampleInfo[4]
		self.contentType = audioSampleInfo[3]
		self.dirOutput = audioSampleInfo[2]
		self.sampleNumber = audioSampleInfo[1]
		self.sampleName = audioSampleInfo[0]
		if self.sampleName.find('/') == -1:
			self.jsonFile = self.dirOutput + "/" +self.sampleName[:self.sampleName.rfind(".")]+"-json.txt"
		else:
			name = self.sampleName[self.sampleName.rfind('/')+1:]
			self.jsonFile = self.dirOutput + "/" +name[:name.rfind(".")]+"-json.txt"
		# Removing json file data will be written to if it already exists.
		try : os.remove(self.jsonFile)
		except OSError : pass

	# Function that deals with the amount of audio sent per message. (Helper function)
	# Audio is chunked and callback function is used.
	def checkChunk(self,data):
		# Function that sends a chunk of audio to the server
		def sendChunk(chunk,final=False):
			self.bytesSent += len(chunk)						# Updating the bytes sent to server.
			self.sendMessage(chunk,isBinary = True)
			# If this is the final chunk that is part of one audio sample.
			if final: self.sendMessage(b'',isBinary=True)

		if (self.bytesSent+self.chunkSize >= len(data)):
			# Sending Final chunk
			if (len(data) > self.bytesSent):
				sendChunk(data[self.bytesSent:len(data)],True)
				return
		# Sending intermediate chunks
		sendChunk(data[self.bytesSent:self.bytesSent+self.chunkSize])
		# Calls the defined function at time x in the future.
		self.factory.reactor.callLater(0.01,self.checkChunk,data=data)
		return 

	# Function that handles data recieved from the server during handshake.
	def onConnect(self, response):
		print("onConnect: {0}\nserver connected: {1}".format(self.sampleName,response.peer))
		print("Audio source: {}".format(self.sampleName))
		print("Websocket Protocol : {}".format(response.protocol))
		print("Protocol Version : {}\n".format(response.version))


	# Callback recieved after handshake is completed and data transmission is
	# possible.
	def onOpen(self):
		print("Opening API Connection")
		# Setting labels off for non standrd base_model
		if self.base_model not in IDModels:labels = False
		else: labels = True
		params = {
			"action":"start",												# Sent as initialization to Watson
			"continuous" : True,											# Prevents timeout due to inactivity.
			"audio_metrics":True,											# Returns signal characteristics of data
			"content-type": str(self.contentType),							# Specifies format of audio data sent.
			"inactivity_timeout": 60,										# Time (seconds) of no audio after which service terminates request
			"interim_results": True,										# Service returns intermediate results
			'max_alternatives': 1,											# The number of alternative results recieved.
			"processing_metrics": True,										# Detailed service analysis notes
			"profanity_filter":False,										# Profanity
			"timestamps":True,												# Word timing data
			"speaker_labels":labels,										# Labels to identify diffenrent individuals in conversation
			'word_confidence': True,										# Confidence values for the words
		}
		# Adding customization weight only if custom model is being used.
		if self.custom : params["customization_weight"] = float(self.customization_weight)
		# Intitial data/parameters sent on handshake completion as json string.
		self.sendMessage(json.dumps(params).encode('utf8'))
		# Audio data sent to and buffered in server.
		with open(str(self.sampleName),'rb') as f:			
			self.bytesSent = 0
			audioFile = f.read()
		self.checkChunk(audioFile)

	# Callback fired when a complete WebSocket message was recieved.
	def onMessage(self,payload,isBinary):
		# Parsing the json string returned by service.
		jsonObject = json.loads(payload.decode('utf8'))

		# Initial / final server response for a new connection
		if 'state' in jsonObject:
			self.listening_state_count +=1
			if self.listening_state_count == 1: print('Starting listening state: {}'.format(self.sampleName))
			else : print("\nEnding listening state: {}".format(self.sampleName))
			# A total of two {'state' : value } JSON objects are sent for a single request.
			# The second indicates end of resukts for audio sent.
			if self.listening_state_count == 2: self.sendClose(1000)
		# Recieving results from service
		elif 'results' in jsonObject:
			# Empty transcription
			if len(jsonObject['results']) == 0: print("Empty transcipt returned")
			# Normal transcript
			else:
				# Dumping result to list
				self.json_output.append(jsonObject)
				bFinal = (jsonObject['results'][0]['final'] == True)				# Case when final results recieved.
				trans = jsonObject['results'][0]['alternatives'][0]['transcript']	# Transcript recieved.
				if bFinal: pass
				else: 
					# Indicating message recieved on stdout.
					sys.stdout.write('.')
					sys.stdout.flush()
		elif 'speaker_labels' in jsonObject or 'result_index' in jsonObject:
			self.json_output.append(jsonObject)


		# Printing an error message if it exists
		if 'error' in jsonObject:
			print("\nServer error encountered\nDetails: {}\n".format(jsonObject['error']))

	# Callback fired when the WebSocket Connection has closed.
	def onClose(self, wasClean, code, reason):
		print("\nClosing API WebSocket connection")
		print('Websocket Connection closed:\n\tCode: {0}\n\tReason: {1}\n'
		'\twasClean: {2}'.format(code,reason,wasClean))
		# Dumping results to a json file.
		with open(self.jsonFile,"a") as f: f.write(json.dumps(self.json_output, indent=4,sort_keys=True))

		# Adding file info to output information dictionary
		dic = {"outputDir" : self.dirOutput,
				"jsonFile" : self.jsonFile,
				"audioFile" : self.sampleName,
				"names" : self.names}
		# Deleting output files for an abnormal connection. 1000 = clean connection
		if code != 1000: dic['delete'] = True
		else: dic['delete'] = False
		outputInfo.append(dic)

		# Marking the task as done
		self.queue.task_done()						

		# Ending the connection if all Audio samples have been processed.
		if not self.factory.prepareAudio: return

		# Establishing a new WebSocket connection to process remainder of queue.
		# Adding Secure Scoekt Layer (SSL/TLS) security to communication
		if self.factory.isSecure: contextFactory = ssl.ClientContextFactory() # Checking if the factory is using SSL and getting TLS object
		else: contextFactory = None
		connectWS(self.factory,contextFactory)	


# *** Helper functions for various tasks ***

# Checks if the given value is a positive integer.
def check_positive_int(value):
	ivalue = int(value)
	if ivalue < 1:
		raise argparse.ArgumentTypeError(
	            '"%s" is an invalid positive int value' % value)
	return ivalue

# Function that checks all files in a list exist
def verifyFiles(audio_files):
	newList = []
	for file in audio_files:
		if not os.path.isfile(file):
			print(colored("\nERROR: File not found: {}\nRemoving"
			" from transcription list\n".format(file),'red'))
		else: newList.append(file)
	return newList

# Main function that interacts with Watson STT
'''
	out_dir = output directory name dictionary (Filename : Directory)
	base_model = base model name for STT
	acoustic_id = custom acoustic model id
	language_id = custom language model id
	num_threads = Number of threads to run.
	opt_out = Set True to opt out of of Watson service log (https://cloud.ibm.com/docs/services/watson?topic=watson-gs-logging-overview)
	watson_token = Set True to use Watson Tokens instead of access tokens for authentication (https://cloud.ibm.com/docs/services/speech-to-text?topic=speech-to-text-websockets)
	audio_files = list of audio files to transcribe.
	names = Speaker names 
	combined_audio = Name of combined audio file
'''
# Return List Template:
# [
	#infodic = {"outputDir" : "",
	#		"jsonFile" : "",
	#		"audioFile" : "",
	#		"names" : []}
# ]
def run(username,password,out_dir,base_model,acoustic_id,language_id,
	num_threads,opt_out,watson_token,audio_files,names,combined_audio,
	contentType,customization_weight):

	sys.stderr.close()	# Suppressing error messages from the WebSocket library (Internal library bugs)
	print(colored("Initiating transcription process..\n",'blue'))

	# Removing files that do not exist
	audio_files = verifyFiles(audio_files)

	# Checking parameters for correctness (Checked runtime Errors)
	for k,v in out_dir.items():
		if not os.path.exists(v): raise OSError("Output directory does not exist")
	check_positive_int(num_threads)
	if not [os.path.isfile(f) for f in audio_files]:
		print("ERROR: Audio file does not exist")
		return

	# Initializing Headers passed to Watson STT as part of request.
	headers = {opt_out_key : '1'} if opt_out else {}

	# Authenticating using Watson tokens.
	if watson_token == 1:
		headers[Watson_token_key] = (Utilities.getAuthenticationToken(
			'https://'+IBM_host,STT_service,username,password))
	else:
	# Authenticating using Access tokens tokens.
		auth = username + ":" + password
		headers[Access_token_key] = "Basic " + base64.urlsafe_b64encode(auth.encode('UTF-8')).decode('ascii')	# Encoding token in base 64

	# Creating and adding additional parameters to request url.
	fmt = "wss://{0}/{1}/api/v1/recognize?model={2}"
	url = fmt.format(IBM_host,STT_service,base_model)
	if language_id != None: url += '&language_customization_id={}'.format(language_id)		# Adding custom language model id.																		# Set if a custom language model for customization weight.
	if acoustic_id != None: url += '&acoustic_customization_id={}'.format(acoustic_id)		# Adding custom acoustic model id.
	if language_id != None: custom = True 													# Indicating if custom weight used.
	else : custom = False

	# Setting up a queue for threading
	q = Queue.Queue()
	fileNumber = 0
	for fileName in audio_files:
		print("Adding to queue\nFilename: {0}, FileNumber: {1}, "
			"Output Directory: {2}".format(fileName,fileNumber,out_dir[fileName]))
		print("Speaker names: {}".format(names[fileName]))
		q.put((fileName,fileNumber,out_dir[fileName],contentType[fileName],names[fileName]))		# Adding File information as a tuple in the processing queue.
		fileNumber +=1


	# Creating a WebSocket interface factory instance to produce instances of 
	# the WebSocket protocol.
	factory = WSInterfaceFactory(queue=q,
		base_model=base_model,url=url,headers=headers,
		customization_weight=customization_weight,custom=custom,debug=False)
	factory.protocol = WSInterfaceProtocol 								# Setting the protocol for the factory.
	for i in range(min(int(num_threads),q.qsize())):					# Using the smaller value out of queue size or threads specified.
		factory.prepareAudio()
		if factory.isSecure: contextFactory = ssl.ClientContextFactory()# Checking for secure or insecure websocket.
		else: contextFactory = None
		connectWS(factory,contextFactory)								# Connecting to the given url using a WebSocket Connection.

	# Moves the reactor to running state.
	# Twisted Reactor library python: https://twistedmatrix.com/documents/current/api/twisted.internet.interfaces.IReactorCore.html
	reactor.run()

	# Returning information dictionary
	print(colored("\nTranscription process completed\n",'green'))
	return outputInfo
	

if __name__ == '__main__':
	pass























