'''
	Script that generates a CHAT file from a CSV input as formatted by Gailbot.

	Part of the Gailbot-3 development project.

	Developed by:

		Muhammad Umair								
		Tufts University
		Human Interaction Lab at Tufts

	Initial development: 6/6/19	
'''


import csv
import sys, time, os
from termcolor import colored					# Text coloring library
import itertools								# Iterating dictionary
import operator									# Sorting library
import io
import subprocess
from prettytable import PrettyTable				# Table printing library
import re 										# Regular expression library
import shutil

# Gailbot scripts
import timing 									# Beat / absolute timing transcription module

# *** Global variables / invariants ***


# Dictionary that contains CHAT post-processing parameters.
CHATVals = {
	"gap" : 0.3,
	"lowerBoundLatch" : 0.01,
	"upperBoundLatch" : 0.09,
	"lowerBoundPause" : 0.2,
	"upperBoundPause" : 1.0,
	"lowerBoundMicropause" : 0.1,
	"upperBoundMicropause" : 0.2,
	"LargePause" : 1.0,
	"turnEndThreshold" : 0.1,
	"lowerBoundLaughAcceptance" : 0.4,
	"LowerBoundLaughLength" : 0.05,
	"beatsMode" : False,
	"FTOMode" : False
}
CHATValsOriginal = CHATVals.copy()

# Headers for the CHAT file
CHATheaders = {
	"corpusName" : "In_Conversation_Corpus",
	"language" : "eng",
	"speaker1Gender" : "male",
	"speaker2Gender" : "male",
	"corpusLocation" : "HI_LAB",
	"roomLayout" : "HI-LAB Duplex",
	"situation" : "Human Interaction Lab Tufts",
	"speaker1Role" : "Unidentified",
	"speaker2Role" : "Unidentified"
}
CHATheadersOriginal = CHATheaders.copy()

# Shell commands:
shellCommands = {
	"CHAT2CA" : "./jeffersonize chat2calite {0}",		#.format(CHATfilename)
	"indentCA" : "./indent {0}"							#.format(CAfilename)
}


# Dictionary of unicode symbols used in CHAT transcripts
CHATsymbols = {
	"latch" : u'\u2248'
}

# Name for the final CHAT file.
CHATname = 'Results.cha'

# List containing separate CSV headings.
CSVfields = ['Speaker Label','Start Time','End Time','Transcript']

# ***********************

# User interface function
def interface(infoList):
	main_menu()

# Executes the appropriate function based on user input.
def exec_menu(choice,function_list,closure):
    os.system('clear')
    choice = choice.lower()
    if choice == '': return
    else:
        try: function_list[choice](closure)
        except KeyError: print("Invalid selection, please try again.\n")
    return

# *** Menu function definitions ***

# Main menu function
def main_menu(closure):
	while True:
		os.system('clear')
		print("Welcome to Gailbot's " + colored('CHAT generation module','red') + " interface!\n")
		print("Use options 1 through 4 to configure CHAT variables.\n")
		print("Please choose one of the following options:")
		print("1. Modify CHAT file headers")
		print("2. Modify CHAT file transcription parameters")
		print(colored("3. Proceed",'green'))
		print(colored("4. Return to main menu\n",'red'))
		choice = input(" >>  ")
		if choice == '3' : return True
		if choice == '4' : return False
		exec_menu(choice,menu_actions,closure)

# CHAT headers menu function
def headers_menu(closure):
	while True:
		os.system('clear')
		x = PrettyTable()
		x.title = colored("CHAT headers settings",'red')
		x.field_names = [colored("Header variable",'blue'),colored("Value",'blue')]
		x.add_row(["Current corpus name",CHATheaders['corpusName']])
		x.add_row(["Current corpus location",CHATheaders['language']])
		x.add_row(["Current corpus location",CHATheaders['corpusLocation']])
		x.add_row(["Current corpus room layout",CHATheaders['roomLayout']])
		x.add_row(["Current corpus situation",CHATheaders['situation']])
		x.add_row(["Current speaker 1 gender",CHATheaders['speaker1Gender']])
		x.add_row(["Current speaker 1 role",CHATheaders['speaker1Role']])
		x.add_row(["Current speaker 2 gender",CHATheaders['speaker2Gender']])
		x.add_row(["Current speaker 2 role",CHATheaders['speaker2Role']])
		print(x)
		print("\nPlease choose one of the following options:")
		print("1. Modify corpus name")
		print("2. Modify corpus language")
		print("3. Modify corpus location")
		print("4. Modify corpus room layout")
		print("5. Modify corpus situation")
		print("6. Modify speaker 1 gender")
		print("7. Modify speaker 1 role")
		print("8. Modify speaker 2 gender")
		print("9. Modify speaker 2 role")
		print("10. Reset selections to default values")
		print(colored("11. Proceed / Confirm selection\n",'green'))
		choice = input(" >>  ")
		if choice == '11' : return
		exec_menu(choice,headers_actions,closure)

# CHAT headers menu function
def vals_menu(closure):
	while True:
		os.system('clear')
		x = PrettyTable()
		x.title = colored("CHAT transcription parameters settings",'red')
		x.field_names = [colored("Transcription parameter",'blue'),colored("Value",'blue')]
		x.add_row(["Current gap length",CHATVals['gap']])
		x.add_row(["Current lower bound - latch",CHATVals['lowerBoundLatch']])
		x.add_row(["Current upper bound - latch",CHATVals['upperBoundLatch']])
		x.add_row(["Current lower bound - pause",CHATVals['lowerBoundPause']])
		x.add_row(["Current upper bound - pause",CHATVals['upperBoundPause']])
		x.add_row(["Current lower bound - micropause",CHATVals['lowerBoundMicropause']])
		x.add_row(["Current upper bound - micropause",CHATVals['upperBoundMicropause']])
		x.add_row(["Current lower bound - large pause",CHATVals['LargePause']])
		x.add_row(["Current lower bound - laugh probability",CHATVals['lowerBoundLaughAcceptance']])
		x.add_row(["Current lower bound - laugh length",CHATVals['LowerBoundLaughLength']])
		x.add_row(["Current turn end threshold",CHATVals['turnEndThreshold']])
		x.add_row(["Beat transcription mode", CHATVals['beatsMode']])
		x.add_row(["FTO (Floor transfer offset) transcription mode", CHATVals['FTOMode']])
		print(x)
		print("\nPlease choose one of the following options:")
		print("1. Modify lower and upper bound - latch")
		print("2. Modify lower and upper bound - pause")
		print("3. Modify lower and upper bound - micropause")
		print("4. Modify lower bound - large pause")
		print("5. Modify lower bound - laugh probability")
		print("6. Modify lower bound - laugh length")
		print("7. Modify gap length")
		print('8. Modify pause transcription mode (Beats / Absolute)')
		print("9. Modify FTO transcription mode")
		print("10. Reset selections to default values")
		print(colored("11. Proceed / Confirm selection\n",'green'))
		choice = input(" >>  ")
		if choice == '11' : return
		exec_menu(choice,vals_actions,closure)

# Actions for the main menu
menu_actions = {
	'1' : headers_menu,
	'2' : vals_menu
}

# *** Definitions for functions used in the transcription parameters menu ***

def modifyCorpusName(closure):
	print("Enter corpus name\nPress 0 to go to back to options\n")
	get_val(CHATheaders,"corpusName",str)

def modifyCorpusLang(closure):
	print("Enter corpus language\nPress 0 to go to back to options\n")
	get_val(CHATheaders,"language",str)

def modifyCorpusLoc(closure):
	print("Enter corpus location\nPress 0 to go to back to options\n")
	get_val(CHATheaders,"corpusLocation",str)

def modifyCorpusRoom(closure):
	print("Enter corpus room layout\nPress 0 to go to back to options\n")
	get_val(CHATheaders,"roomLayout",str)

def modifyCorpusSituation(closure):
	print("Enter corpus recording situation\nPress 0 to go to back to options\n")
	get_val(CHATheaders,"situation",str)

def modifySpeaker1Gender(closure):
	print("Enter speaker 1 gender\nPress 0 to go to back to options\n")
	get_val(CHATheaders,"speaker1Gender",str)

def modifySpeaker1Role(closure):
	print("Enter speaker 1 role\nPress 0 to go to back to options\n")
	get_val(CHATheaders,"speaker1Role",str)

def modifySpeaker2Gender(closure):
	print("Enter speaker 2 gender\nPress 0 to go to back to options\n")
	get_val(CHATheaders,"speaker2Gender",str)

def modifySpeaker2Role(closure):
	print("Enter speaker 2 role\nPress 0 to go to back to options\n")
	get_val(CHATheaders,"speaker2Role",str)

def headersDefault(closure):
	for k,v in CHATheadersOriginal.items(): CHATheaders[k] = v


headers_actions = {
	'1' : modifyCorpusName,
	'2' : modifyCorpusLang,
	'3' : modifyCorpusLoc,
	'4' : modifyCorpusRoom,
	'5' : modifyCorpusSituation,
	'6' : modifySpeaker1Gender,
	'7' : modifySpeaker1Role,
	'8' : modifySpeaker2Gender,
	'9' : modifySpeaker2Role,
	'10' :headersDefault
}

# *** Definitions for functions used in the headers menu ***

def modifyLatch(closure):
	print("Enter lower bound - latch\nPress 0 to go to back to options\n")
	get_val(CHATVals,"lowerBoundLatch",float)
	os.system('clear')
	print("Enter upper bound - latch\nPress 0 to go to back to options\n")
	get_val(CHATVals,"upperBoundLatch",float)

def modifyPause(closure):
	print("Enter lower bound - pause\nPress 0 to go to back to options\n")
	get_val(CHATVals,"lowerBoundPause",float)
	os.system('clear')
	print("Enter upper bound - pause\nPress 0 to go to back to options\n")
	get_val(CHATVals,"upperBoundPause",float)

def modifyMicropause(closure):
	print("Enter lower bound - Micropause\nPress 0 to go to back to options\n")
	get_val(CHATVals,"lowerBoundMicropause",float)
	os.system('clear')
	print("Enter upper bound - Micropause\nPress 0 to go to back to options\n")
	get_val(CHATVals,"upperBoundMicropause",float)

def modifyLargePause(closure):
	print("Enter lower bound - Large pause\nPress 0 to go to back to options\n")
	get_val(CHATVals,"LargePause",float)

def modifyLaughProb(closure):
	print("Enter lower bound - Laugh probability\nPress 0 to go to back to options\n")
	get_val(CHATVals,"lowerBoundLaughAcceptance",float)

def modifyLaughLen(closure):
	print("Enter lower bound - Laugh length\nPress 0 to go to back to options\n")
	get_val(CHATVals,"LowerBoundLaughLength",float)

def modifyGap(closure):
	print("Enter gap length\nPress 0 to go to back to options\n")
	get_val(CHATVals,"gap",float)

def modifyBeatMode(closure):
	CHATVals['beatsMode'] = not CHATVals['beatsMode']

def modifyFTOMode(closure):
	CHATVals['FTOMode'] = not CHATVals['FTOMode']

def valsDefault(closure):
	for k,v in CHATValsOriginal.items(): CHATVals[k] = v

vals_actions = {
	'1' : modifyLatch,
	'2' : modifyPause,
	'3' : modifyMicropause,
	'4' : modifyLargePause,
	'5' : modifyLaughProb,
	'6' : modifyLaughLen,
	'7' : modifyGap,
	'8' : modifyBeatMode,
	'9' : modifyFTOMode,
	'10' : valsDefault
}


# Wrapper function for CHAT_actions functions dictionary
def formatCHAT(infoList):
	print(colored("\nGenerating CHAT/CA file(s)\n",'blue'))
	for infoDic in infoList:
		print("Loading file: {}".format(infoDic['jsonFile']))
	for action in CHAT_actions.values(): 
		infoList = action(infoList)
		if len(infoList) == 0: return infoList
	print(colored("\nCHAT/CA file generation completed\n",'green'))
	return infoList


# *** Definitions for CHAT file formatting functions ***

# Function that changes Watson comment markers
# Input: Dictionay containing perocessed file information
def commentMarkers(infoList):
	for infoDic in infoList:
		for elem in infoDic['jsonList'][1:]:
			if elem[3].find("%HESITATION") != -1:
				elem[3]=elem[3].replace("%HESITATION","uhm")
	return infoList


# Function that constructs turn per individual CSV file based on turn construction 
# thresholds.
# Input: Dictionay containing perocessed file information
def constructTurn(infoList):
	for infoDic in infoList:
		newList = [] ; count = 0 ; changed = False
		jsonList = infoDic['jsonList'][1:]
		jsonList = [elem[:4] for elem in jsonList]				# Extracting transcription relevent data.
		while count < len(jsonList) - 1:
			curr = jsonList[count] ; nxt = jsonList[count+1]
			if nxt[1] - curr[2] <= CHATVals['turnEndThreshold'] and curr[0] == nxt[0]:
				changed = True
				jsonList[count] = [curr[0],curr[1],nxt[2],curr[3]+" "+nxt[3]]
				del jsonList[count+1]
			else: count +=1
		infoDic['jsonListTurns'] = jsonList
		# Removing extra period markers
		for elem in jsonList: elem[3]=elem[3].translate({ord('.'):None}) 
	return infoList

# directories are grouped.
# Input: list of individual dictionaries
# Output: list of lists containing dictionaries.
def groupDictionaries(infoList):
	newInfo = [];dirs = []
	if len(infoList) == 1: newInfo.append([infoList[0]])
		# Generating all possible combinations of items in infoList
	for a,b in itertools.combinations(infoList,2):
		if a['outputDir'] == b['outputDir']:
			newInfo.append([a,b]);dirs.append(a['outputDir'])
	for a,b in itertools.combinations(infoList,2):
		if a['outputDir'] not in dirs: 
			newInfo.append([a]);dirs.append(a['outputDir'])
		if b['outputDir'] not in dirs: 
			newInfo.append([b]);dirs.append(b['outputDir'])
	return newInfo

# Function that builds a combined transcript for both speakers.
# Useful in case audio was analyzed on separate streams
# Input: list of lists containing dictionaries.
# Output : list of lists containing dictionaries.
def combineTranscripts(infoList):
	for item in infoList:
		jsonListCombined = []
		if len(item) == 1: 
			item[0]['jsonListCombined'] = item[0]['jsonListTurns'];continue
		for list1 in item[0]['jsonListTurns']: jsonListCombined.append(list1)
		for list2 in item[1]['jsonListTurns']: jsonListCombined.append(list2)
		jsonListCombined=sorted(jsonListCombined, key = operator.itemgetter(1))
		for dic in item: dic['jsonListCombined'] = jsonListCombined
	return infoList

# Function that transcribes overlaps
# Input: list of lists containing dictionaries.
# Output : list of lists containing dictionaries.
def overlaps(infoList):
	markerLimit = 4 										# Minimum number of chars to have a marker
	for item in infoList:
		newList = []
		jsonListCombined = item[0]['jsonListCombined']
		for count,curr in enumerate(jsonListCombined[:-1]):
			nxt = jsonListCombined[count+1]
			if curr[2] > nxt[1]:
				pos = overlapPositions(curr,nxt)			# Getting overlap marker positions
				# Not adding markers if difference is below limit
				if (abs(pos['posXcurr'] - pos['posYcurr']) <= markerLimit
					or abs(pos['posXnxt'] - pos['posYnxt']) <= markerLimit):
					newList.append(curr);continue
				# Not adding markers if there is no character within limit
				# Not adding markers encompassing comments.
				if (not re.search('[a-zA-Z]',curr[3][pos['posXcurr']:pos['posYcurr']])
					or not re.search('[a-zA-Z]',curr[3][pos['posXcurr']:pos['posYcurr']])):
					newList.append(curr);continue
				# Adding overlap markers
				newCurrTrans = curr[3][:pos['posXcurr']] +' < ' + curr[3][pos['posXcurr']:]
				curr[3] = (newCurrTrans[:pos['posYcurr']] + ' > [>] ' + newCurrTrans[pos['posYcurr']:]).rstrip()
				newNxtTrans = nxt[3][:pos['posXnxt']] +' < ' + nxt[3][pos['posXnxt']:]
				nxt[3] = (newNxtTrans[:pos['posYnxt']] + ' > [<] ' + newNxtTrans[pos['posYnxt']:]).rstrip()
			newList.append(curr)
		newList.append(jsonListCombined[-1])
		for dic in item: dic['jsonListCombined'] = newList
	return infoList	


# Function that adds pause markers to the combined speaker transcripts.
# Pauses added to combined list to prevent end of line pause transcriptions.
# Input: list of lists containing dictionaries.
# Output : list of lists containing dictionaries.
def pauses(infoList):
	return timing.pauses(infoList,CHATVals)


# Function that combines successive turns of the same speaker.
# Input: list of lists containing dictionaries.
# Output : list of lists containing dictionaries.
def combineSameSpeakerTurns(infoList):
	for item in infoList:
		jsonListCombined = item[0]['jsonListCombined'] ; newList = []
		for count,curr in enumerate(jsonListCombined):
			if len(newList) == 0: newList.append(curr)
			elif newList[-1][0] == curr[0]:
				newList[-1][2] = curr[2] ; newList[-1][3] += ' '+curr[3]
			else: newList.append(curr)
		for dic in item: dic['jsonListCombined'] = newList
	return infoList


# Function that adds FTO's to the transcript if enabled
# Input: list of lists containing dictionaries.
# Output : list of lists containing dictionaries.
def transcribeFTO(infoList):
	if not CHATVals['FTOMode']: return infoList
	for item in infoList:
		jsonListCombined = item[0]['jsonListCombined'] ; newList = []
		for count,curr in enumerate(jsonListCombined[:-1]):
			nxt = jsonListCombined[count+1] ; FTO = str(round(nxt[1] - curr[2],1))
			newItem = ['FTO',curr[2],nxt[1],FTO] ; newList.extend([curr,newItem])
		for dic in item: dic['jsonListCombined'] = newList
	return infoList

# Function that adds gaps to the transcript
# Input: list of lists containing dictionaries.
# Output : list of lists containing dictionaries.
def gaps(infoList):
	return timing.gaps(infoList,CHATVals)

# Function that converts the combinedList to CHAT format
# Input: list of lists containing dictionaries.
# Output : list of lists containing dictionaries.
def CHATList(infoList):
	for item in infoList:
		CHATList = [];jsonListCombined = item[0]['jsonListCombined']
		# Formatting speaker ID.
		for elem in jsonListCombined: elem[0] = '*'+elem[0]+':'
		# Removing pause / gap markers.
		for elem in jsonListCombined: elem[0] = elem[0].replace("**GAP:",'')
		for elem in jsonListCombined: elem[0] = elem[0].replace("**PAU:",'')
		# Converting time to milliseconds
		for elem in jsonListCombined: elem[1] = int(elem[1]*1000);elem[2]=int(elem[2]*1000)
		# Adding eol delimiter.
		for count,curr in enumerate(jsonListCombined[:-1]):
			nxt = jsonListCombined[count+1]
			if nxt[0] != '': curr[3] += ' . '
		# Adding a carridge return every 80 chars
		for elem in jsonListCombined:
			elem[3]="\n\t".join([elem[3][i:i+80] for i in range(0,len(elem[3]),80)])
		# Adding bullets with timing details.
		for elem in jsonListCombined:
			turn = '{0}\t{1} \u0015{2}_{3}\u0015\n'.format(elem[0],elem[3].lstrip(),elem[1],elem[2])
			CHATList.append(turn)
		CHATList.append("@End\r")
		for dic in item:dic['CHATList'] = CHATList
	return infoList


# Function that writes a CHAT file
# Input: list of lists containing dictionaries.
# Output : list of lists containing dictionaries.
def buildCHAT(infoList):
	for item in infoList:
		# Assigning appropriate speaker names and ID's
		names = []
		if len(item) == 1: names = ([item[0]['names'][0].upper(),item[0]['names'][1].upper()])
		elif len(item) == 2: names = ([item[0]['names'][0].upper(),item[1]['names'][0].upper()])
		speakerID = [names[0][0:3].upper(),names[1][0:3].upper()]
		if item[0]['audioFile'][:item[0]['audioFile'].find('.')].find('/') == -1:
			audioName = item[0]['audioFile'][:item[0]['audioFile'].find('.')]
		else:
			name = item[0]['audioFile'][:item[0]['audioFile'].find('.')]
			audioName = name[name.rfind('/')+1:]
		# Setting comments
		if CHATVals['beatsMode']: timingMode = "Beat timing mode: Pauses/Gaps in beats"
		else: timingMode = "Absolute timing mode: Pauses/Gaps in seconds"
		headers = [
			"@Begin\n@Languages:\t{0}\n".format(CHATheaders['language']),
			"@Participants:\t{0} {1} {2}, {3} {4} {5}\n".format(
				speakerID[0],names[0],CHATheaders['speaker1Role'],
				speakerID[1],names[1],CHATheaders['speaker2Role']),
			"@Options:\tCA\n",
			"@ID:\t{0}|{1}|{4}||{2}|||{3}|||\n".format(CHATheaders['language'],CHATheaders['corpusName'],
				CHATheaders['speaker1Gender'],CHATheaders['speaker1Role'],speakerID[0]),
			"@ID:\t{0}|{1}|{4}||{2}|||{3}|||\n".format(CHATheaders['language'],CHATheaders['corpusName'],
				CHATheaders['speaker2Gender'],CHATheaders['speaker2Role'],speakerID[1]),
			"@Media:\t{0},audio\n".format(audioName),
			"@Comment:\t{0}\n".format(timingMode),
			"@Transcriber:\tGailbot 0.3.0\n",		
			"@Location:\t{0}\n".format(CHATheaders['corpusLocation']),
			"@Room Layout:\t{0}\n".format(CHATheaders['roomLayout']),
			"@Situation:\t{0}\n@New Episode\n".format(CHATheaders['situation'])
		]
		# Writing CHAT file.
		if item[0]['outputDir'].find('/') == -1:
			CHATfilename = item[0]['outputDir']+'/'+ item[0]['outputDir']+ '-' +CHATname
		else:
			name = item[0]['outputDir'][item[0]['outputDir'].rfind('/')+1:]
			CHATfilename = item[0]['outputDir']+'/'+ name+ '-' +CHATname
		if os.path.isfile(CHATfilename): os.remove(CHATfilename)
		try: 
			with io.open(CHATfilename,"w",encoding = 'utf-8') as outfile:
				for s in headers: outfile.write(s)
				for elem in item[0]['CHATList']:outfile.write(elem)
		except FileNotFoundError:
			print(colored("\nCHAT file generation FAILED",'red'))
			print("Directory or file not found\n")
			return []
		# Adding CHAT filename to item list.
		for elem in item:elem['CHATfilename'] = CHATfilename
	return infoList

# Function that creates a CA file by running shell commands on the created CHAT file.
# Input: list of lists containing dictionaries.
# Output : list of lists containing dictionaries.
def buildCA(infoList):
	for item in infoList:
		CHATfilename = item[0]['CHATfilename']
		CAfilename = CHATfilename[:CHATfilename.find('.')]+'.S.ca'
		indentFilename = CAfilename[:CAfilename.rfind('.')]+'.indnt.cex'
		# Redirecting shell output to null
		devnull = open(os.devnull, 'w')
		# Creating CA file 
		cmd_CA = shellCommands['CHAT2CA'].format(CHATfilename)
		try: subprocess.check_call(cmd_CA,shell=True,stderr=devnull,stdout=devnull)
		except subprocess.CalledProcessError: 
			print(colored("\nCHAT to CAlite conversion: FAILED",'red'))
			print("Missing executable: jeffersonize\n")
		# Indenting the CA file
		cmd_indent = shellCommands['indentCA'].format(CAfilename)
		val = indent(item[0]['outputDir'],CAfilename[CAfilename.rfind('/')+1:])
		if not val: return []
		# Renaming the files
		try:
			os.remove(CAfilename)
			os.rename(indentFilename,CAfilename)
		except: pass
	return infoList


# Function that writes all the different kinds of CSV files.
# Input: list of lists containing dictionaries.
# Output : list of lists containing dictionaries.
def writeCSVs(infoList):
	for item in infoList:
		currItem = item[0]
		csvName = currItem['CHATfilename'][:currItem['CHATfilename'].find('.')]+'.csv'
		currItem['jsonListCombined'].insert(0,CSVfields)
		try: writer = csv.writer(open(csvName, 'w'))
		except FileNotFoundError:
			print(colored("\nCHAT file generation FAILED",'red'))
			print("Directory or file not found\n")
			return False
		writer.writerows(currItem['jsonListCombined'])
	return infoList



# Dictionary of functions used to create a CHAT file
CHAT_actions = {
	'1' : commentMarkers,
	'2' : constructTurn,
	'3' : groupDictionaries,
	'4' : combineTranscripts,
	'5' : overlaps,
	'6' : pauses,
	'7' : combineSameSpeakerTurns,
	'8' : transcribeFTO,
	'9' : gaps,
	'10' : CHATList,
	'11' : buildCHAT,
	'12' : buildCA,
	'13' : writeCSVs
}

# *** Helper functions for various tasks ***

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
				#if len(choice) == 0:continue
				if choice == type(0): return None
				else: 
					dic[key] = choice
					return True
		except ValueError: print("Error: Value must be of type: {}".format(type))

# Function that determines the positions for overlap markers.
# Input: current and next turn list
# Returns: Dictionary defining the x and y overlap marker positions for both turn
def overlapPositions(curr,nxt):
	startDifference = nxt[1]-curr[1] ; endDifference = curr[2] - nxt[2]
	currLen = curr[2] - curr[1] ; nxtLen = nxt[2] - nxt[1]
	sD = startDifference ; eD = endDifference ; cL = currLen ; nL = nxtLen
	# In this case, the overlap is at nxt start and pos x of curr turn.
	if startDifference > 0:
		posXnxt = 0 ; posXcurr = overlapPos(sD,cL,len(curr[3]))
		# Case-1a: In this case, overlap ends at pos y of curr turn and end of nxt turn
		if endDifference > 0:
			posYcurr = len(curr[3])- overlapPos(eD,cL,len(curr[3])) ; posYnxt = len(nxt[3])
		# Case-1b: In this case, overlap ends at curr turn end and pos y from turn 2 end.
		elif endDifference < 0:
			posYcurr = len(curr[3]) ; posYnxt = len(nxt[3])-overlapPos(eD,nL,len(nxt[3]))
		# Case-1c: In this case, overlap ends at both turn ends.
		elif endDifference == 0:
			posYcurr = len(curr[3]) ; posYnxt = len(nxt[3])
	# In this case, overlap is from start of curr turn to pos x of nxt turn.
	elif startDifference < 0:
		posXcurr = 0 ; posXnxt = overlapPos(sD,nL,len(nxt[3]))
		# Case-2a: In this case, overlap ends at posY from curr turn start and end of nxt turn
		if endDifference > 0:
			posYcurr = len(curr[3])-overlapPos(eD,cL,len(curr[3])) ; posYnxt = len(nxt[3])
		# Case-2b: In this case, overlap ends at curr turn ends and posY from nxt turn end.
		elif endDifference < 0:
			posYcurr = len(curr[3]) ; posYnxt = len(nxt[3])-overlapPos(eD,nL,len(nxt[3]))
		# Case-2c: In this case, overlap ends at the end of both turns
		elif endDifference == 0:
			posYcurr = len(curr[3]) ; posYnxt = len(nxt[3])
	# In this case, overlap is from start of both turns.
	elif startDifference == 0:
		posXcurr = 0 ; posXnxt = 0
		# Case-3a: In this case, overlap ends at posY from curr turn start and end of nxt turn
		if endDifference > 0:
			posYcurr = len(curr[3])-overlapPos(eD,cL,len([3])) ; posYnxt = len(nxt[3])
		# Case-3b: In this case, overlap ends at curr turn ends and posY from nxt turn end.
		elif endDifference < 0:
			posYcurr = len(curr[3]) ; posYnxt = len(nxt[3])-overlapPos(eD,nL,len(nxt[3]))
		# Case-3c: In this case, overlap ends at the end of both turns
		elif endDifference == 0:
			posYcurr = len(curr[3]) ; posYnxt = len(nxt[3])
	# Moving values to start or end of individual turns
	if posXcurr >= len(curr[3]): posXcurr=len(curr[3])-1
	if posXnxt >= len(nxt[3]): posXnxt = len(nxt[3])-1
	if posYcurr >= len(curr[3]): posYcurr = len(curr[3])-1
	if posYnxt >= len(nxt[3]):posYnxt = len(nxt[3])-1
	while curr[3][posXcurr] != ' ' and posXcurr > 0: posXcurr-=1
	while curr[3][posYcurr] != ' ' and posYcurr < len(curr[3])-1: posYcurr+=1
	while nxt[3][posXnxt] != ' ' and posXnxt > 0: posXnxt-=1
	while nxt[3][posYnxt] != ' ' and posYnxt < len(nxt[3])-1: posYnxt +=1
	if abs(posYcurr - len(curr[3])) == 1: posYcurr+=1
	if abs(posYnxt - len(nxt[3])) == 1: posYnxt+=1
	posYcurr+=3 ; posYnxt +=3						# Adding to accomodate new marker(s) in string.
	# Returning position values Dictionary
	return {"posXcurr": posXcurr,"posYcurr":posYcurr,"posXnxt":posXnxt,"posYnxt":posYnxt}

# Lambda function to calculate the pverlap positions
overlapPos =lambda diff,Len,transLen : int(round((((abs(diff)/Len))*transLen)))

# Function that copies the indent script to the generated folder and runs it
# Used because Talkbank's indent script does NOT work for subdirectories.
# Returns None if exe is not found.
def indent(outputDir,CAfilename):
	shutil.copy('indent',outputDir)
	cmd_indent = shellCommands['indentCA'].format(CAfilename)
	devnull = open(os.devnull, 'w')
	try: 
		subprocess.check_call(cmd_indent,shell=True,cwd=outputDir,stderr=devnull,
			stdout=devnull) ; os.remove(outputDir+'/indent')
	except subprocess.CalledProcessError: 
		print(colored("\nCA file indentation: FAILED",'red'))
		print("Missing executable: indent\n")
		os.remove(outputDir+'/indent')
		return False
	return True








