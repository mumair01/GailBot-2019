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

# Gailbot scripts
import CHAT										# Script to produce CHAT files.
import rateAnalysis  							# Script to analyze speech rate.
import laughAnalysis 							# Scropt to analyze laughter.


# *** Global variables / invariants. ***

# List containing separate CSV headings.
CSVfields = ['Speaker Label','Start Time','End Time','Transcript','Confidence',
			'Periodic','Recieved Audio', 'Result Index']

# *** Menu functions ***

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
		infoDic['csv'] = filename                   # Adding individual csv filename.
		infoDic['jsonList'] = jsonList				# Adding transcribed data to dictionary 					
	return infoList


# *** Post-Processing actions ***

# Dictionary of post-processing functions
# input: InfoDic dictionary per output / input file.
processingActions = {
	'1' : jsonToCSV, 										# Converts json to csv
	'2' : rateAnalysis.analyzeSyllableRate,					# Analyzing syllable rate
	'3' : laughAnalysis.analyzeLaugh, 						# Analyzing laughter.
	'4' : CHAT.formatCHAT	           						# Formatting and creating CHAT file.
}

# *** Helper functions ****

# Wrapper function that calls all processing functions
# Input : List passed to main/postProcess
def processWrapper(infoList):
	for action in processingActions.values(): infoList = action(infoList)

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
	with open(infoDic['jsonFile']) as f: jsonObject = json.load(f)
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
	# Changing labels to provided names
	jsonList = assignSpeakers(jsonList,infoDic['names'])
	return jsonList




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

	sampleInfo = [dic,dic2]
	postProcess(sampleInfo)




























