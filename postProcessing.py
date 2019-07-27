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
import copy 		
import numpy 									# Library to have multi-dimensional homogenous arrays.							# Copying module.
import yaml


# Gailbot scripts
import CHAT										# Script to produce CHAT files.
import rateAnalysis  							# Script to analyze speech rate.
import laughAnalysis 							# Script to analyze laughter.
import soundAnalysis 							# Script to analyze different sound characterists.




# *** Global variables / invariants. ***

# Hidden meta-data file for auto-post processing.
metaFileName = ".meta.json"

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
	print(colored("Use arrow keys to navigate",'blue'))
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
	# Function that creates hidden file for post-processing.
	addMetaData(infoList)



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
			input("\nPress any key to continue...")
			return
		else: infoList = action(infoList)

# Function that writes a meta-data file for automatic post-processing.
def addMetaData(infoList):
	count = 0
	for elem in infoList:
		outDic = {} ; wrapper = {}
		outDic['jsonFile'] = elem['jsonFile'] ; outDic['names'] = elem['names']
		outDic['audioFile'] = elem['audioFile']
		outDic['individualAudioFile'] = elem['individualAudioFile']

		# Deleting existing instance.
		if not os.path.exists(os.path.join(elem['outputDir'], metaFileName)):
			with open(os.path.join(elem['outputDir'], metaFileName), 'w') as f:
				json.dump([],f)
		# Writing new data
		with open(os.path.join(elem['outputDir'], metaFileName), 'r') as f: 
			data = json.load(f)
		if outDic not in data: data.append(outDic)
		with open(os.path.join(elem['outputDir'], metaFileName), 'w') as f:
			json.dump(data,f)



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

#  *** List of functions to implement ***
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


# *** Local menu functions ***


# Global list of files to be processed.
infoList = []
# Copy of the defualt dictionary.
infoListOriginal = infoList.copy()

# Executes the appropriate function based on user input.
def exec_menu(choice,function_list):
	os.system('clear')
	choice = choice.lower()
	if choice == '': return
	else:
		try: function_list[choice]()
		except KeyError: print("Invalid selection, please try again.\n")
	return

# Function that runs the entire post-processing module as a separate entity.
def runLocal(username,password,closure):
	if not local_menu(): return False
	if not main_menu(): return False
	os.system('clear')
	postProcess(infoList)
	print(colored("\nPost-processing completed\n",'green'))
	input(colored("Press any key to continue...",'red'))
	infoList.clear()


# Main menu function
def local_menu():
	while True:
		os.system('clear')
		print("Welcome to Gailbot's " + colored('Post-processing','red') + " interface!\n")
		x = PrettyTable()
		x.title = colored("Post-processing request",'red')
		x.field_names = [colored("Out-Directory",'blue'),colored("jsonFile",'blue'),
			colored("Combined Audio",'blue'),colored("Names",'blue'),colored("Individual Audio",'blue')]
		for infoDic in infoList:
			x.add_row([infoDic['outputDir'],infoDic['jsonFile'][infoDic['jsonFile'].rfind('/')+1:],
				infoDic['audioFile'][infoDic['audioFile'].rfind('/')+1:],
				infoDic['names'],
				infoDic['individualAudioFile'][infoDic['individualAudioFile'].rfind('/')+1:]])
		print(x)
		print(colored("\nNOTE: This module is meant to be applied to Gailbot outputs"
			" **exactly** as outputted\n",'red'))
		print(colored("NOTE: For pair files, input the information for both files separately",'red'))
		print('\nUse options 1 through 4 to configure the post-processing menu:\n')
		print("1. Add files to process")
		print("2. Change added files")
		print(colored("3. Proceed",'green'))
		print(colored("4. Return to main menu\n",'red'))
		choice = input(" >>  ")
		if choice == '3': return True
		if choice == '4' :
			infoList.clear() ; return False
		exec_menu(choice,local_actions)


# Function that obtains post-processing specific information
# Returns: List of dictionaries that can be given to postProcess.
def postInput():
	localDic = {}
	if not getOutDir(localDic,"outputDir"): return None
	# Attempting to retrieve the metadata file for post-processing.
	if not retrieveMetaData(localDic['outputDir']):
		if remainingInputs(localDic) == None: return None



# Function that allows the user to change the already selected files
# Input: InfoList global variable.
def modifySelections():
	global infoList
	dirList = [] ; localDic = {}
	for elem in infoList: dirList.append(elem["jsonFile"])
	dirList.append(colored("Return",'red'))
	jsonFile = generalInquiry(dirList,"Selection to change") ; 
	if jsonFile == colored("Return",'red'): return
	for elem in infoList:
		if elem["jsonFile"] == jsonFile: 
			localDic["outputDir"] = elem["outputDir"] ; dic = elem
	infoList = [elem for elem in infoList if (elem["jsonFile"] != jsonFile)]
	if remainingInputs(localDic) == None: infoList.append(dic)

# Actions for the main menu
local_actions = {
	'1' : postInput,
	'2' : modifySelections,
	'3' : main_menu
}

# *** Helper functions for the local menu ***

# Helper Function that gets an input
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


# Function that reads metadata file to add fileds automatically for post-processing
# Returns True of data found and false if not found.
def retrieveMetaData(outputDir):
	if os.path.exists(os.path.join(outputDir,metaFileName)):
		with open(os.path.join(outputDir,metaFileName), 'r') as stream:
			dicList = json.load(stream)
			if dicList == None: return False
			for dic in dicList:
				dic['outputDir'] = outputDir
				infoList.append(dic)
		return True
	else: return False
	

# Function that gets the remaining inputs for post-processing
def remainingInputs(localDic):
	# Getting a list of all files in the specific directory.
	dirFiles = fileList(localDic["outputDir"]) ; dirFiles.append(colored("Return",'red'))
	# Getting all remaining inputs
	if not getJsonFile(localDic,"jsonFile",dirFiles): return None
	print("Enter " +colored("combined",'red')+ " audio file\nSelect 'Return' to go back to options\n")
	print(colored("EXAMPLE: pair-0/test2a-test2b-combined.wav\n",'blue'))
	if not getAudio(localDic,"audioFile",dirFiles): return None
	if not getNames(localDic,"names"): return None
	os.system('clear')
	print("Enter " +colored("individual",'red')+ " audio file\nPress 'Return' to go back to options\n")
	print(colored("EXAMPLE: pair-0/test2a.wav\n",'blue'))
	if not getAudio(localDic,"individualAudioFile",dirFiles): return None
	infoList.append(localDic)
	return True




def getOutDir(dic,key):
	os.system('clear')
	print("Enter output directory\nPress 0 to go back to options\n")
	print(colored("NOTE: All inputs must be as outputted by Gailbot 0.3.0\n",'red'))
	print(colored("EXAMPLE: sample1\n",'blue'))
	while True:
		if get_val(dic,key,str) == None: return False
		if not os.path.isdir(dic[key]):
			print(colored("\nERROR: Invalid Directory. Try again\nPress 0 to go back to options\n",'red'))
		else: os.system('clear') ; return True

def getJsonFile(dic,key,dirList):
	os.system('clear')
	print("Enter JSON data file\nSelect 'Return' to go back to options\n")
	print(colored("NOTE: All inputs must be as outputted by Gailbot 0.3.0\n",'red'))
	print(colored("EXAMPLE: sample1/sample1-json.txt\n",'blue'))
	while True:
		jsonFile = generalInquiry(dirList, "Selected JSON File")
		if jsonFile == colored("Return",'red'): return False
		else: dic[key] = dic['outputDir'] + '/' + jsonFile
		if not os.path.isfile(dic[key]) or not os.path.splitext(dic[key])[1] == ".txt":
			print(colored("\nERROR: Invalid file. Try again\nSelect 'Return' to go back to options\n",'red'))
		else: os.system('clear') ; return True

def getNames(dic,key):
	os.system('clear')
	print("Enter speaker names (space delimited)\nSelect '0' to go back to options\n")
	print(colored("EXAMPLES:\nOne speaker: SP1\nTwo Speakers: SP1 SP2\n",'blue'))
	return get_val(dic,key,list)

def getAudio(dic,key,dirList):
	print(colored("NOTE: All inputs must be as outputted by Gailbot 0.3.0\n ",'red'))
	while True:
		audioFile = generalInquiry(dirList,"Selected Audio File")
		if audioFile ==colored("Return",'red'): return False
		else: dic[key] = dic['outputDir'] + '/' + audioFile
		if not os.path.isfile(dic[key]):
			print(colored("\nERROR: Invalid file. Try again\nSelect 'Return' to go back to options\n",'red'))
		else: os.system('clear') ; return True


# Function that returns a list of all files in a directory
# Input: File directory
# Output: List of all files in the directory.
def fileList(dir):
	return [file for file in os.listdir(dir) if file[0] != '.']

# General inquiry meny funtion.
def generalInquiry(choiceList,message):
	options = [
			inquirer.List('inputVal',
				message=message,
				choices=choiceList,
				),
		]
	print(colored("Use arrow keys to navigate\n",'blue'))
	print(colored("Proceed --> Enter / Return key\n",'green'))
	return inquirer.prompt(options)['inputVal']

if __name__ == '__main__':

	#runLocal('a','b',{})


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

	sampleInfo = [dic4]
	postProcess(sampleInfo)




























