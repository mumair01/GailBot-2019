'''
	Script that acts as the main driver for Gailbot. 
	Sends requests to Watson, sets custom models, and uses post-processing functions.

	Part of the Gailbot-3 development project.

	Developed by:

		Muhammad Umair								
		Tufts University
		Human Interaction Lab at Tufts

	Initial development: 5/30/19	

'''

# Libraries to build standalone executable.
import sklearn.ensemble
import sklearn.tree
import sklearn.neighbors.typedefs
import sklearn.neighbors.quad_tree
import sklearn.tree._utils
import sklearn
import sklearn.utils._cython_blas
from sklearn.preprocessing import StandardScaler

import json
import sys, time, os
from termcolor import colored					# Text coloring library
import time 									# Timing library
from prettytable import PrettyTable				# Table printing library
import copy
import argparse  
import subprocess
import queue as Queue 
import tempfile									# Directory library
import shutil									# Directory library
import glob 									# Directory library

# Gailbot scripts
import STT 										# Script that sends transcription requests
import language_model							# Script that selects language models
import acoustic_model							# script that selects acoustic models
import postProcessing 							# Script that performs post-processing.
import CHAT										# script to produce CHAT files.

# Audio processing libraries
from pydub import AudioSegment
from pydub.utils import make_chunks

# Audio recording libraries
import pyaudio
import wave

# Progressbar library
from progressbar import AnimatedMarker, Bar, BouncingBar, Counter, ETA, \
    AdaptiveETA, FileTransferSpeed, FormatLabel, Percentage, \
    ProgressBar, ReverseBar, RotatingMarker, \
    SimpleProgress, Timer, UnknownLength


# *** Global variables / invariants ***


# Constants for audio segmentation and chunking
maxChunkBytes = 90000000   								# Max audio length per request = 90 MB.

# Audio recording variables
recordingVals = {
"Recording_chunk_size" : 1024,						# Size of chunk that can be recorded
"Format" : pyaudio.paInt16,							# Recording format
"channels" : 1,										# Number of audio channels
"recordSeconds" : 30,								# Number of seconds to be recorded
"rate" : 48000,										# Recording rate
"audioFilename" : 'Recorded.wav'}
recordingValsOriginal = recordingVals.copy()

# Watson request variables
watsonVals = {
	"username" : "",
	"password" : "",
	"output-directory" : {},
	"base-model" : "en-US_BroadbandModel",
	"acoustic-id" : None,
	"custom-id" : None,
	"opt-out" : True,
	"token-type" : "Access",
	"names" : {},
	"contentType" : {},
	"customizationWeight" : 0.5,
	"files" : [],
	'combinedAudio' : {}
}
watsonValsOriginal = watsonVals.copy()

# Map from audio formats to file extensions
audioFormatMapping = {"audio/alaw" : "alaw", "audio/basic" : "basic","audio/flac": "flac",
	"audio/g729" : "g729" , "audio/l16" : "pcm" , "audio/mp3" : "mp3" , 
	"audio/mpeg" : "mpeg" , "audio/mulaw" : "ulaw" , "audio/ogg" : "opus",
	"audio/wav" : "wav","audio/webm" : "webm" }

# Supported Video file formats and their extensions
videoFormats = {"Material-Exchange-Format" : "mxf",
				"Quicktime-File-Format" : "mov",
				"MPEG-4" : "mp4",
				"Windows-Media-Video" :"wmv",
				"Flash-Video-Format" : "flv",
				"Audio-Video-Interleave" :"avi",
				"Shockwave-Flash" : "swf",
				"Apple MPEG-4" : "m4v"}

 # Number of channels to extract from each video format
videoFormatChannels = {
 	"mxf" : 2,
 	"mov" : 1,
 	"mp4" : 1,
 	"wmv" : 1,
 	"flv" : 1,
 	"avi" : 1,
 	"swf" : 1,
 	"m4v" : 1
 }

# Recording library formats
formats = {'8' : 'paInt16' , '4' : 'paInt24', '2' : 'paInt32','16' : 'paInt8 '}

# Shell commands:
shellCommands = {
	"convertOpus" : "./opusenc --bitrate 24 {0} {1}",													#.format(audioFile, newOpusName)
	"singleChannelFFmpeg" : "ffmpeg -i {0} -acodec pcm_s16le -ar 16000 {1}.wav",						#.format(file,file-No extension)
	"dualChannelFFmpeg" : "ffmpeg -i {0} -map 0:1 -c copy -acodec pcm_s16le -ar 16000 {1}-speaker1.wav \
					-map 0:2 -c copy -acodec pcm_s16le -ar 16000 {1}-speaker2.wav", 					#.format(file,file-No extension)
	"overlay" : "ffmpeg -i {0} -i {1} -filter_complex join=inputs=2:channel_layout=stereo {2}"			#.format(file1,file2,outPath)
}

# Queue of intermediate files to be deleted at the end of request.
deleteQueue = Queue.Queue()


# ***********************

# User interface function
def interface(username,password):
	main_menu(username,password,{})

# *** Menu function definitions ***

# Executes the appropriate function based on user input.
def exec_menu(choice,function_list,username,password,closure):
    os.system('clear')
    choice = choice.lower()
    if choice == '': return
    else:
        try: function_list[choice](username,password,closure)
        except KeyError: print("Invalid selection, please try again.\n")
    return

# Main menu function
def main_menu(username,password,closure):
	while True:
		watsonDefaults(username,password,closure)
		recordDefaults(username,password,closure)
		os.system('clear')
		print(colored('Gailbot 0.3.0\nDeveloped by: HUMAN INTERACTION LAB - TUFTS\n','red')
			+'\nGailbot is an automated transcription system '
			'that specializes in transcribing in the Conversation Analysis (CA)'
			' format\n')
		print("Use options 1 through 4 to configure and use Gailbot\n")
		print("Please choose one of the following options:\n")
		print("1. Transcribe existing conversation(s)")
		print("2. Record and transcribe a conversation")
		print("3. Apply post-processing on existing Gailbot data")
		print(colored("4. Quit\n",'red'))
		choice = input(" >>  ")
		exec_menu(choice,menu_actions,username,password,closure)

# Audio recording menu function
def recording_menu(username,password,closure):
	while True:
		os.system('clear')
		x = PrettyTable()
		x.title = colored("Audio recording settings",'red')
		x.field_names = [colored('Setting','blue'),colored('Value','blue')]
		x.add_row(['Current chunk size (bytes)',recordingVals['Recording_chunk_size']])
		x.add_row(["Current audio format", formats[str(recordingVals['Format'])]])
		x.add_row(["Current audio channels",recordingVals['channels']])
		x.add_row(["Current recording rate (Hertz)",recordingVals['rate']])
		x.add_row(["Current audio filename",recordingVals['audioFilename']])
		x.add_row(["Current recording length (seconds)",recordingVals['recordSeconds']])
		print(x)
		print("\n1. Modify audio chunk size")
		print("2. Modify audio format")
		print("3. Modify audio channels")
		print("4. Modify recording rate")
		print("5. Modify audio filename")
		print("6. Modify recording length")
		print("7. Restore defaults")
		print(colored("8. Start recording",'green'))
		print(colored("9. Return to main menu\n",'red'))
		choice = input(" >>  ")
		if choice == '9' : return False
		exec_menu(choice,record_actions,username,password,closure)
		if choice == '8' : return True

# Watson request menu function
def request_menu(username,password,closure):
	while True:
		watsonVals['username'] = username
		watsonVals['password'] = password
		os.system('clear')
		y = PrettyTable()
		y.title = colored("Pre-request Menu",'red')
		y.field_names = [colored("Request variable",'blue'),colored("Value",'blue')]
		y.add_row(["IBM Bluemix Username",watsonVals['username']])
		y.add_row(["IBM Bluemix password",watsonVals['password']])
		y.add_row(["Base language model",watsonVals['base-model']])
		y.add_row(["Base acoustic model",acoustic_model.output['base-model']])
		y.add_row(["Custom acoustic model ID",watsonVals['acoustic-id']])
		y.add_row(["Custom language model ID",watsonVals['custom-id']])
		y.add_row(["X-Watson-Learning opt out",watsonVals['opt-out']])
		y.add_row(["Authentication type",watsonVals['token-type']])
		y.add_row(["Custom language model weight",watsonVals['customizationWeight']])
		print(y)
		x = PrettyTable()
		x.field_names  = [
			colored('Audio file','blue'),colored('Output Directory','blue'),
			colored('Content-Type','blue'),colored('Speaker names','blue')
		]
		for k,v in watsonVals['output-directory'].items(): 
			x.add_row([k,v,watsonVals['contentType'][k],str(watsonVals['names'][k])])
		print(x)
		if watsonVals['base-model'] != acoustic_model.output['base-model']:
			print(colored("\nWARNING: Ensure acoustic and language base model consistency",'red'))
		print("\n1. Change base / custom language model")
		print("2. Change custom acoustic model")
		print("3. Change X-Watson-Learning status")
		print("4. Change authentication type")
		print("5. Change customization weight")
		print("6. Restore defaults")
		print(colored("7. Start transcription",'green'))
		print(colored("8. Return to main menu\n",'red'))
		choice = input(" >>  ")
		if choice == '8' : return False
		if choice == '7' : return True
		exec_menu(choice,request_actions,username,password,True)				# Passing True to reset value.
		if len(watsonVals['files']) == 0 : return False


# *** Definitions for functions used in the main menu ***

# Function that records a new conversation before transcribing it.
def transcribe_new(username,password,closure):
	if not recording_menu(username,password,closure): return
	# Setting and verifying dictionary values.
	pairDic = {"files" : []}
	watsonVals['files'] = [recordingVals['audioFilename']]
	if any(file for file in watsonVals['files'] if not os.path.isfile(file)):
		print("\nERROR: File does not exist")
		return
	# Verifying content Type and extracting opus file if needed.
	watsonVals['files'],pairDic = convertOpus(watsonVals['files'],deleteQueue,pairDic)
	setOutputDir(watsonVals['files'],watsonVals['files'][0][:watsonVals['files'][0].rfind('.')])	
	watsonVals['contentType'] = setContentType(audioFormatMapping,watsonVals['files'])
	# Setting speaker names
	setSpeakers(watsonVals['files'],pairDic)

	# Selecting post-processing modules to be implemented
	if not postProcessing.main_menu(): return

	# Ensure base model consistency
	if not request_menu(username,password,closure): return
	while not checkBaseModels(acoustic_model.output["base-model"],language_model.output["base-model"]):
		if not request_menu(username,password,closure): return
	# Sending request.
	sendRequest(username,password,closure)
	

# Function that transcribes a pre-recorded conversation
def transcribe_recorded(username,password,closure):
	if getAudioFileList() == None: return

	# Selecting post-processing modules to be implemented
	if not postProcessing.main_menu(): return

	# Ensure base model consistency
	if not request_menu(username,password,closure): return 
	while not checkBaseModels(acoustic_model.output["base-model"],language_model.output["base-model"]):
		if not request_menu(username,password,closure): return 
	sendRequest(username,password,closure)

# Exit program
def exit(username,password,closure):
    sys.exit()

# Actions for the main menu
menu_actions = {
    'main_menu': main_menu,
    '1' : transcribe_recorded,
    '2' : transcribe_new,
    '3' : postProcessing.runLocal,
    '4' : exit
}

# *** Definitions for functions used in the recording menu ***

# Function that records the audio for real-time transcription mode.
def record_audio(username,password,closure):
	# Setting up a progressbar
	widgets = ['Recording: ', Percentage(), ' ', Bar("|"), ' ', ETA(), ' ']
	pbar = ProgressBar(widgets=widgets, maxval=recordingVals['rate']/recordingVals['Recording_chunk_size'] * recordingVals['recordSeconds'])
	print('\n\n')

	# Creating a PyAudio instance
	audio = pyaudio.PyAudio()
	# Starting to record
	stream = audio.open(format=recordingVals['Format'], channels=recordingVals['channels'],
                    rate=recordingVals['rate'], input=True,
                    frames_per_buffer=recordingVals['Recording_chunk_size'])
	frames = []
	for i in range(0, int(recordingVals['rate']/recordingVals['Recording_chunk_size'] * recordingVals['recordSeconds'])):
		pbar.update(i)
		data = stream.read(recordingVals['Recording_chunk_size'])
		frames.append(data)

	# Stop Recording
	stream.stop_stream()
	stream.close()
	audio.terminate()
	# Ending progressbar
	pbar.finish()

	waveFile = wave.open(recordingVals['audioFilename'], 'wb')
	waveFile.setnchannels(recordingVals['channels'])
	waveFile.setsampwidth(audio.get_sample_size(recordingVals['Format']))
	waveFile.setframerate(recordingVals['rate'])
	waveFile.writeframes(b''.join(frames))
	waveFile.close()
	input("\nFinished recording!\nPress any key to continue...")

# Function that modifies the Chunk size
def modifyChunk(username,password,closure):
	print("Enter Chunk size\nPress 0 to go to back to options")
	get_val(recordingVals,"Recording_chunk_size",int)

# Function that modifies Audio format
def modifyFormat(username,password,closure):
	while True:		
		try: 
			for k,v in formats.items(): print(k + ' : ' + v)
			recordingVals['Format'] = int(input("\nEnter audio format\nPlease choose a number from the list above\n"
				"Press 0 to go back to options\n"))
			if recordingVals['Format'] == 0: 
				recordingVals['Format'] = recordingValsOriginal['Format']
				return
			if str(recordingVals['Format']) not in formats: raise ValueError
			break
		except ValueError: print("Error: Choose format from displayed list")

# Function that modifies Audio channels
def modifyChannels(username,password,closure):
	print("Enter the number of channels\nPress 0 to go back to options\n")
	get_val(recordingVals,"channels",int)

# Function that modifies Audio rate
def modifyRate(username,password,closure):
	print("Enter the recording rate (Hertz)\nPress 0 to go back to options\n")
	get_val(recordingVals,"rate",int)

# Function that modifies Audio filename
def modifyName(username,password,closure):
	print("Enter the output filename\nMust include extension\nPress 0 to go back to options\n")
	get_val(recordingVals,"audioFilename",str)
	print(recordingVals['audioFilename'].find('.'))
	if recordingVals['audioFilename'].find('.') == -1: recordingVals['audioFilename'] = recordingVals['audioFilename'] + '.wav'

# Function that modifies the recording length
def modifyLength(username,password,closure):
	print("Enter the length of audio to be recorded (seconds)\nNote: Length must be greater than " +colored("30 seconds",'red')+"\n"
		"Press 0 to go back to options\n")
	while recordingVals['recordSeconds'] <= 30: get_val(recordingVals,"recordSeconds",int)

# Function that restores all defaults
def recordDefaults(username,password,closure):
	for k,v in recordingValsOriginal.items(): recordingVals[k] = v
	#input('Values reset!\nPress any key to return to menu...')

# Actions for the recording menu
record_actions = {
	'1' : modifyChunk,
	'2' : modifyFormat,
	'3' : modifyChannels,
	'4' : modifyRate,
	'5' : modifyName,
	'6' : modifyLength,
 	'7' : recordDefaults,
	'8' : record_audio
}

# *** Definitions for functions used in the request menu ***

# Function that modifies the custom language model.
def modifyLangModel(username,password,closure):
	output = language_model.interface(username,password)
	watsonVals['base-model'] = output['base-model']
	watsonVals['custom-id'] = output['custom-model']

# Function that modifies the custom acoustic model.
def modifyAcoustModel(username,password,closure):
	output = acoustic_model.interface(username,password)
	watsonVals['acoustic-id'] = output['acoustic-model']

# Function that modifies the X-Watson-Learning parameter.
def modifyLearning(username,password,closure):
	watsonVals['opt-out']  = not watsonVals['opt-out']

# Function that modifies the type of authentication used.
def modifyAuth(username,password,closure):
	if watsonVals['token-type'] == "Access" :  watsonVals['token-type'] = "Watson" 
	elif watsonVals['token-type'] == "Watson" :  watsonVals['token-type'] = "Access" 

# Function that modifies the speaker names.
def modifyNames(username,password,closure):
	print("Enter speaker names\nPress 0 to go back to options\n")
	get_val(watsonVals,'names',list)

# Function that modifies the customization weight
def modifyWeight(username,password,closure):
	print('Specify custom language model customization weight\nPress 0 to go back to options\n')
	get_val(watsonVals,"customizationWeight",float)
	if watsonVals['customizationWeight'] < 0 :
		watsonVals['customizationWeight'] = watsonValsOriginal['customizationWeight']

# Function that restores watsonVals to defaults
def watsonDefaults(username,password,closure):
	for k,v in watsonValsOriginal.items(): watsonVals[k] = v
	watsonVals['output-directory'].clear()
	#input('Values reset!\nPress any key to return to menu...\n')
	os.system('clear')
	# Getting new audio file names before returning to main menu 
	getAudioFileList(closure)			

# Actions for the request menu
request_actions = {
	'1' : modifyLangModel,
	'2' : modifyAcoustModel,
	'3' : modifyLearning,
	'4' : modifyAuth,
	'5' : modifyWeight,
	'6' : watsonDefaults,
}

# *** Helper functions for various tasks ***

# Function that recieves and verifies input file.
# Use '-pair' to specify pairs of files.
# Set getval to False to not get audio files.
# Returns None to nor proceed. True to proceed
def getAudioFileList(getVal=True):
	if not getVal :return
	audioTable = PrettyTable() ; videoTable = PrettyTable()
	audioTable.title = colored("Supported audio formats",'red')
	videoTable.title = colored("Supported video formats",'red')
	audioTable.field_names = [colored('Audio Format','blue'),colored('Extension','blue')]
	videoTable.field_names = [colored('Video Format','blue'),colored('Extension','blue'),
		colored("Required audio channels",'blue')]
	for k,v in audioFormatMapping.items():  audioTable.add_row([k,v])
	for k,v in videoFormats.items(): videoTable.add_row([k,v,videoFormatChannels[v]])
	print(audioTable)
	print(videoTable)
	print('\n')
	while True:
		print("Enter audio/video file name(s)-"+ colored(" Space delimited",'red'))
		print("NOTE: Use " + colored("'-pair [file-1] [file-2]'",'red'),
			"to input an audio file pair part of a single conversation")
		print("NOTE: Use " + colored("'-dir [directory name]'",'red'),
			"to input all files in a directory. " +
			colored("Sub-directories not included",'red'))
		print("Press 0 to go back to options\n")
		localDic = {}
		if get_val(localDic,'files',list)==None: return
		# Extracting all files from a directory and removing -directory flag
		localDic['files'] = setDirectoryFiles(localDic['files'])
		if len(localDic['files']) == 0: print("\nERROR: File does not exist") ; continue
		# Extracting pairs from the input list and removing -pair keyword
		localDic['files'],pairDic = setFilePairs(localDic['files'])
		# Ensuring files exist
		if any(file for file in localDic['files'] if not os.path.isfile(file)):
			print("\nERROR: File does not exist") ; continue
		# Verifying file formats.
		if not verifyFormat(videoFormats,audioFormatMapping,localDic['files']): continue
		# Extracting audio from video inputs.
		localDic['files'],pairDic = extractAudio(localDic['files'],pairDic)
		# Converting files larger than threshold to Opus 
		localDic['files'],pairDic = convertOpus(localDic['files'],deleteQueue,pairDic)
		# Setting output directories.
		for file in localDic['files']:
			trimmedKeys = [x[:x.find('.')] for x in watsonVals['output-directory'].keys()]
			# Setting putput directory in case opus files were generated for file pairs.
			if file[:file.find('.')] in trimmedKeys and file not in watsonVals['output-directory'].keys():
				watsonVals['output-directory'][file] = watsonVals['output-directory'][file[:file.find('.')]+'.wav']
				del watsonVals['output-directory'][file[:file.find('.')]+'.wav']
			elif file not in watsonVals['output-directory'].keys():
				setOutputDir([file],file[:file.rfind('.')])
		# Setting audio content type
		watsonVals['contentType'] = setContentType(audioFormatMapping,
			localDic['files'])
		# Setting speaker names
		setSpeakers(localDic['files'],pairDic)	
		# Overlaying pair files
		overlay(pairDic['files'],watsonVals['output-directory'])	
		# Setting requestd ictionary variables
		watsonVals['files'] = localDic['files']
		return True

# Helper Function that gets an input for the recording menu
def get_val(dic,key,type):
	while True:
		try:
			if type == list: 
				choice = input(" >> ").split()
				if len(choice) == 0:continue
				if choice[0] == str(0): return None
				dic[key] = choice
				return True
			else: 
				choice = type(input(" >> "))
				if len(str(choice)) == 0:continue
				if choice == type(0): return None
				else: 
					dic[key] = choice
					return True
		except ValueError: print("Error: Value must be of type: {}".format(type))

# Function that sends requests to Watson.
def sendRequest(username,password,closure):
	os.system('clear')
	# Setting request variables.
	if watsonVals['token-type'] == 'Access' : token = 0
	elif watsonVals['token-type'] == 'Watson' : token = 1
	print
	# Command to run the Speeach to Text core module.
	outputInfo = STT.run(username=watsonVals['username'],password = watsonVals['password'],
		base_model= watsonVals['base-model'],acoustic_id = watsonVals['acoustic-id'],
		language_id=watsonVals['custom-id'],watson_token=token,
		audio_files=watsonVals['files'],names=watsonVals['names'],combined_audio = '',
		contentType=watsonVals['contentType'],num_threads = len(watsonVals['files']),
		customization_weight = watsonVals['customizationWeight'],
		out_dir=watsonVals['output-directory'],opt_out = watsonVals['opt-out'])
	# Removing unprocessed files.
	for dic in outputInfo:
		if dic['delete'] : 
			try: shutil.rmtree(dic['outputDir'])
			except: pass 
	outputInfo = [dic for dic in outputInfo if not dic['delete']]
	# Adding combined audio information to output.
	for dic in outputInfo:
		# Copying original audiofiles to output directory
		copyFile(dic['audioFile'],dic['outputDir']+'/')
		# Adding individual file path and name
		if dic['audioFile'].find('/') == -1:
			dic['individualAudioFile'] =dic['outputDir']+'/'+ dic['audioFile']
		else:
			names = dic['audioFile'][dic['audioFile'].rfind('/')+1:]
			dic['individualAudioFile'] =dic['outputDir']+'/'+ names
		if dic['audioFile'] in watsonVals['combinedAudio'].keys():
			dic['audioFile'] = watsonVals['combinedAudio'][dic['audioFile']]
		# Copying audiofiles to output directory
		copyFile(dic['audioFile'],dic['outputDir']+'/')
	# Performing post-processing
	postProcessing.postProcess(outputInfo)
	# Deleting generated opus files
	while not deleteQueue.empty(): os.remove(deleteQueue.get_nowait())
	input("\nRequest Processed\nPress any key to continue")
	# Restoring defaults after request
	watsonDefaults(username,password,False)
	recordDefaults(username,password,closure)
	# Preventing the reactor from restarting.
	time.sleep(0.5)
	os.execl(sys.executable, sys.executable, *sys.argv)	

# Function that converts audio to ogg / opus format.
# Requires opusend exe : https://mf4.xiph.org/jenkins/view/opus/job/opus-tools/ws/man/opusenc.html
def convertOpus(audiofileList,queue,pairDic):
	names = []
	for audiofile in audiofileList:
		if os.path.getsize(audiofile) > maxChunkBytes:
			opusName = audiofile[:audiofile.find('.')] + ".opus"
			cmd = shellCommands['convertOpus'].format(audiofile,opusName)
			subprocess.call(cmd, shell=True)
			names.append(opusName)
			queue.put(opusName)	
			for pair in pairDic['files']:			# Changing pair filenames
				for count,file in enumerate(pair): 
					if file == audiofile:pair[count] = opusName
		else: names.append(audiofile)
	return names,pairDic

# Function that sets the contentType parameter based on the type of audio
def setContentType(formatDic,audioFileList):
	newDic = {}
	for file in audioFileList:
		ext = file[file.rfind('.')+1:]
		for k,v in formatDic.items():
			if v == ext.lower(): 
				newDic[file] = k
	return newDic

# Function that extracts audio from video file if required.
# Video format must be in Video Format Dictionary.
def extractAudio(fileList,pairDic):
	newList = []
	for file in fileList:
		for k,v in videoFormatChannels.items():
			extension = file[file.find('.')+1:].lower()
			fileName = file[:file.find('.')+1]
			if not extension in videoFormatChannels: 
				cmd = ''
				newList.append(file)
				break
			if videoFormatChannels[extension] == 1:
				cmd = shellCommands['singleChannelFFmpeg'].format(file,fileName[:-1])
				newList.append(fileName+"wav")
				break
			elif videoFormatChannels[extension] == 2:
				cmd = shellCommands['dualChannelFFmpeg'].format(file,fileName[:-1])
				newList.extend([fileName[:-1]+"-speaker1.wav",fileName[:-1]+"-speaker2.wav"])
				# Setting same output directory for pair files.
				setOutputDir([fileName[:-1]+"-speaker1.wav",fileName[:-1]+"-speaker2.wav"],fileName[:-1])
				# Adding files as a pair
				pairDic['files'].append([fileName[:-1]+"-speaker1.wav",fileName[:-1]+"-speaker2.wav"])
				break
		subprocess.call(cmd, shell=True)
	return newList,pairDic

# Function that verifies that the file format is supported.
# Returns True if all files are supported.
def verifyFormat(videoFormatDic,audioFormatDic,fileList):
	for file in fileList:
		ext = file[file.rfind(".")+1:].lower()
		if ext not in audioFormatDic.values()and ext not in videoFormatDic.values():
			print("\nERROR: Format not supported: {0}".format(file))
			return False
	return True

# Function that maps files from a list to a given directory
# Creates watsonVals['out_dir'] dirctionary and the directory.
def setOutputDir(fileList,dirName):
	for file in fileList: watsonVals['output-directory'].update({file:dirName})
	if os.path.exists(dirName):
		input(colored("\nWARNING: ", 'red') + "Overwriting existing directory: {}\n" 
			"Press any key to continue\n".format(dirName))
		tmp = tempfile.mktemp(dir=os.path.dirname(dirName))
		shutil.move(dirName, tmp)
		shutil.rmtree(tmp)
	os.makedirs(dirName)

# Extracts the files that are pairs into a separate list
def setFilePairs(fileList):
	pairDic = {}
	pairDic['files'] = [] ; newList = [] ; ext = False
	for file in fileList:
		if ext:
			newList.append(file)
			if len(newList) == 2:
				pairDic['files'].append(newList)
				ext = False ; newList = [] ; continue
		if file == '-pair': ext = True
	for count,listElem in enumerate(pairDic['files']):
		setOutputDir(listElem,'pair-{}'.format(count))
	fileList = [val for val in fileList if val != '-pair']
	return fileList,pairDic

# Extracts all the files from a given directory and sets as files to be transcribed.
# Input: List of files to be transcribed.
# Returns an empty list of any of the files does not exist
def setDirectoryFiles(fileList):
	newList = [] ; ext = False
	for file in fileList:
		if ext:
			files = [file+'/'+f for f in os.listdir(file) if os.path.isfile(os.path.join(file, f))]
			newList.extend(files) ; ext = False
		elif file == '-dir': ext = True
		else: 
			if not os.path.isfile(file) and file != '-pair':
				print("\nERROR: File does not exist") ; return []
			newList.append(file)
	# Ensuring files are supported.
	newList = [file for file in newList if file[file.rfind('.')+1:] in videoFormats.values()
			or  file[file.rfind('.')+1:] in audioFormatMapping.values()or file == '-pair']
	return newList

# Function that sets speaker names for each file.
# Pair files have two different speakers per file.
def setSpeakers(fileList,pairDic):
	pairList = pairDic['files'] ; processedList = []
	for files in pairList:
		for count,file in enumerate(files):
			processedList.append(file)
			watsonVals['names'][file] = ['SP{}'.format(str(count+1))]
	for file in fileList:
		if file not in processedList:
			watsonVals['names'][file] = ['SP1','SP2']

# Function that overlays two audio files to combine them into a single audio file.
# Input: List of lists containing audio file pair.
#		Output directory for combined audio file.
def overlay(pairList,outDirDic):
	for pair in pairList:
		name = pair[0][:pair[0].rfind('.')]+"-"+pair[1][:pair[1].rfind('.')]+'-combined.wav'
		path = outDirDic[pair[0]]+'/'+name
		cmd = shellCommands['overlay'].format(pair[0],pair[1],path)
		devnull = open(os.devnull, 'w')
		subprocess.call(cmd, shell=True,stdout=devnull,stderr=devnull)
		for file in pair:watsonVals['combinedAudio'][file] = name

# Function that copies a file from one directory to another.
def copyFile(currentPath,newDirPath):
	try:shutil.copy(currentPath,newDirPath)
	except (shutil.Error,FileNotFoundError): pass

# Function that verifies whether the acoustic and custom base models are complementary
# Returns True if base models are the same
# Returns false otherwise
def checkBaseModels(acousticBase,languageBase):
	if acousticBase == None or languageBase == None: return True
	if str(acousticBase) == str(languageBase): return True
	else:
		os.system('clear')
		print(colored("\nERROR: Ensure acoustic model and language model have the same base model",'red'))
		print(colored("\nCurrent acostic base model: {}".format(acousticBase),'blue'))
		print(colored("\nCurrent language base model: {}".format(languageBase),'blue'))
		input(colored("\nPress any key to return to pre-request menu...",'red'))
		return False



if __name__ == '__main__':

	# parse command line parameters
	parser = argparse.ArgumentParser(
		description = ('client to recoginize type of request to be set to te Watson STT system'))
	parser.add_argument(
		'-username', action = 'store', dest = 'username', 
		help = "IBM bluemix username", required = True)
	parser.add_argument(
		'-password', action = 'store', dest = 'password',
		help = 'IBM bluemix password', required = True)
	args = parser.parse_args()

	interface(args.username,args.password)











