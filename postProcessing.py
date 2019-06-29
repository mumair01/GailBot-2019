'''
	Script that contains post-processing functions as part of Gailbot-3.
	Connects gailbot.py and other post-processing modules.

	Part of the Gailbot-3 development project.

	Developed by:

		Muhammad Umair								
		Tufts University
		Human Interaction Lab at Tufts

	Initial development: 6/4/19	
'''

import json,csv
import sys, time, os
from termcolor import colored					# Text coloring library
import itertools								# Iterates over lists
import inquirer 								# Selection interface library.
from prettytable import PrettyTable				# Table printing library

# Gailbot scripts
import CHAT										# Script to produce CHAT files.
import rateAnalysis  							# Script to analyze speech rate.
import laughAnalysis 							# Script to analyze laughter.
import soundAnalysis 							# Script to analyze different sound characterists.
import numpy 									# Library to have multi-dimensional homogenous arrays.



# *** Global variables / invariants. ***

# post-processing module dictionary

# Current selection status of the post-processing modules
postModulesStatus = {
	"syllRate": colored("Selected",'green'),
	"laughter" : colored("Selected",'green'),
	"sound" : colored("Selected",'green')
}

# Mapping between display name and key name
mapping = {
	"Syllable rate module" : "syllRate",
	"Laughter detection module" : "laughter",
	"Sound analysis module" : "sound"
}

# Mapping between key name and appropriate post-processing function
funcMapping = {
	"syllRate" : rateAnalysis.analyzeSyllableRate,	
	"laughter" : laughAnalysis.analyzeLaugh,
	"sound" : soundAnalysis.analyzeSound
}

# Mapping between a function to the local menu 
menuMapping = {
	CHAT.formatCHAT : CHAT.main_menu
}


# List containing separate CSV headings.
CSVfields = ['Speaker Label','Start Time','End Time','Transcript','Confidence',
			'Periodic','Recieved Audio', 'Result Index']


# *** Menu function definitions ***

# Function that implements the main menu.
# Allows user to select the post-processing functions to implement.
def main_menu():
	while True:
		os.system('clear')
		x = PrettyTable()
		x.title = colored("Post-processing interface",'red')
		x.field_names = [colored("Module",'blue'),colored("Status",'blue')]
		x.add_row(["Syllable rate module",postModulesStatus['syllRate']])
		x.add_row(["Laughter detection module",postModulesStatus['laughter']])
		x.add_row(["Sound analysis module",postModulesStatus['sound']])
		print(x)
		print("\nUse options 1 through 2 to select the post-processing modules " 
			"to be implemented:")
		print("\n1. Change selections")
		print(colored("2. Proceed / Confirm selection\n",'green'))
		choice = input(" >>  ")
		if choice == '2':
			return applyLocalMenu();
		if choice == '1': 
			moduleList = inquire(postModulesStatus)
			createActionList(moduleList)

# Helper function for the main menu
def inquire(modules):
	options = [
			inquirer.Checkbox('postModules',
				message="Post-processing modules",
				choices=["Syllable rate module",
				"Laughter detection module",
				"Sound analysis module"],
				),
		]
	print("\nSelect the post-processing modules to be implemented:\n")
	print("Select --> Right arrow key")
	print("Unselect --> Left arrow key")
	print(colored("Proceed --> Enter / Return key\n",'green'))
	modules = inquirer.prompt(options)
	for key in mapping.keys():
		if key in modules['postModules']: postModulesStatus[mapping[key]] = colored("Selected",'green')
		else: postModulesStatus[mapping[key]] =colored("Not selected",'red')
	return modules['postModules']


# Main menu function
# Input: Tuple/List containing information.
def postProcess(infoList):
	processWrapper(infoList)

# *** Definitions for functions used in the postProcessing actions ***

# Function that converts a Gailbot json file to CSV.
# Input : List passed to main/postProcess
def jsonToCSV(infoList):
	for infoDic in infoList:
		# Getting relevant data list.
		jsonList = getJSON(infoDic)
		# Writing to CSV file.
		filename = infoDic['jsonFile'][:infoDic['jsonFile'].find('-json')]+".csv"
		jsonList.insert(0,CSVfields)
		writer = csv.writer(open(filename, 'w'))
		writer.writerows(jsonList)
		# Updating dictionary
		infoDic['csv'] = filename                   # Adding exit csv filename.
		infoDic['jsonList'] = jsonList				# Adding transcribed data to dictionary 
	# Removing file from list if it is not found.
	infoList=[infoDic for infoDic in infoList if len(infoDic['jsonList']) > 1]		
	return infoList


# *** Helper functions ****

# Wrapper function that calls all processing functions
# Input : List passed to main/postProcess
def processWrapper(infoList):
	for action in processingActions: 
		# Ending if no files to process.
		if len(infoList) == 0: 
			print(colored("Post-processing not applied\nNo data to process\n",'red'))
			return
		else: infoList = action(infoList)

# Function that assigns speaker names based on the number of speakers
# Input: Transcribed word List + additional metrics from getJSON
def assignSpeakers(jsonList,namesList):
	if len(namesList) == 1: 
		for listElem in jsonList: listElem[0] = namesList[0]
	elif len(namesList) == 2:
		for listElem in jsonList:
			if listElem[0] == 0 : listElem[0] = namesList[0]
			else: listElem[0] = namesList[1]
	return jsonList


# Function that retrieves json data from file.
# Returns: Transcribed word List + additional metrics
def getJSON(infoDic):
	jsonList = []
	labels = {}
	try:
		with open(infoDic['jsonFile']) as f: jsonObject = json.load(f)
	except FileNotFoundError:
		print(colored("\nERROR: File not found: {}".format(infoDic['jsonFile']),'red'))
		return []
	for res in jsonObject:
		if "speaker_labels" not in res:
			# Extracting main fields
			processingMetrics = res['processing_metrics']
			resultIndex = res['result_index'];results = res['results']
			final = results[0]['final'];wordData = results[0]['alternatives'][0]
			# Extracting data to be written to file.
			periodic = processingMetrics['periodic']
			recieved = processingMetrics['processed_audio']['received']
			confidenceVals = wordData['word_confidence'];words = wordData['timestamps']
			# Writing row per word.
			if final:
				for word,confidence in itertools.zip_longest(words,confidenceVals):
						# Extracting transcript and timing
						trans = word[0];startTime = word[1]
						endTime = word[2];confVal = confidence[1]
						jsonList.append([startTime,endTime,trans,confVal,
							periodic,recieved,resultIndex])
		else:
			speakerLabels = res['speaker_labels']
			for label in speakerLabels: labels.update({label['from']:label['speaker']})
	# Adding speaker labels to output list
	for listElem,label in zip(jsonList,labels): listElem.insert(0,labels[label])
	# Adding label if no speaker labels were returned.
	if len(labels) == 0: 
		labels = numpy.resize([0,1],len(jsonList))
		for elem,label in zip(jsonList,labels):elem.insert(0,label)
	# Changing labels to provided names
	jsonList = assignSpeakers(jsonList,infoDic['names'])
	return jsonList

# List of functions to implement
processingActions = [jsonToCSV,rateAnalysis.analyzeSyllableRate,
		laughAnalysis.analyzeLaugh,soundAnalysis.analyzeSound,
		CHAT.formatCHAT]

# List of functions to implement
#processingActions = [jsonToCSV,soundAnalysis.analyzeSound,CHAT.formatCHAT]

# Function that creates the processingActions list
def createActionList(moduleList):
	global processingActions
	actionList = [jsonToCSV]
	for module in moduleList:  actionList.append(funcMapping[mapping[module]])
	actionList.append(CHAT.formatCHAT)
	processingActions = actionList.copy()


# Function thacalls the local menus for post-processing functions being applied
def applyLocalMenu():
	for action in processingActions:
		if action in menuMapping.keys():
			if not menuMapping[action]({}): return False
	return True


if __name__ == '__main__':


	dic = {"outputDir" : "pair-0",
			"jsonFile" : "pair-0/test2a-json.txt",
			"audioFile" : "test2a-test2b-combined.wav",
			"names" : ["SP1"],
			"individualAudioFile" : "pair-0/test2a.wav"}
	dic2 = {"outputDir" : "pair-0",
			"jsonFile" : "pair-0/test2b-json.txt",
			"audioFile" : "test2a-test2b-combined.wav",
			"names" : ["SP2"],
			"individualAudioFile" : "pair-0/test2b.wav"}
	dic3 = {"outputDir" : "sample1",
			"jsonFile" : "sample1/sample1-json.txt",
			"audioFile" : "sample1.mp3",
			"names" : ["SP1","SP2"],
			"individualAudioFile" : "sample1/sample1.mp3"}
	dic4 = {"outputDir" : "pizza",
			"jsonFile" : "pizza/pizza-json.txt",
			"audioFile" : "pizza.mp3",
			"names" : ["SP1","SP2"],
			"individualAudioFile" : "pizza/pizza.mp3"}

	sampleInfo = [dic3]
	postProcess(sampleInfo)




























