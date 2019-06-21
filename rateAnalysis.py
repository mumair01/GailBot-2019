'''
	Post-processing script that implements a speech rate analysis model to 
	determine the relative speed of a turn per speaker.

	Developed by:

		Muhammad Umair								
		Tufts University
		Human Interaction Lab at Tufts

	Initial development: 6/17/19
'''


import os, sys
import matplotlib.pyplot as plt 				# Library to visualize mfcc features.
import librosa.display 							# Library to display signal.
import numpy 									# Library to have multi-dimensional homogenous arrays.
from big_phoney import BigPhoney				# Finds the syllables per word.
from statsmodels import robust 					# Statistics library.
import tensorflow as tf 						# Deep neural network library
import operator									# Sorting library
import copy 									# Copying module.
import logging
from termcolor import colored

# Gailbot scripts
from CHAT import constructTurn 					# Function to construct individual speaker turns.

tf.get_logger().setLevel(logging.ERROR) 		# Turning off tensorflow debugging messages.

# *** Global variables / invariants ***


# The number of deviations above or below the absolute median deviation.
LimitDeviations = 2 			

# Unicode for the delimiters used.
delims = {
	"slowSpeech" :  u'\u25BC',
	"fastSpeech" :  u'\u25B2'
}

# *** Definitions for speech rate analysis functions ***

# Main driver function
def analyzeSyllableRate(infoList):
	# Copying original list so it is not modified.
	infoListCopy = copy.deepcopy(infoList)
	# Removing hesitation markers from list
	infoListCopy = removeHesitation(infoListCopy)
	# Constructing turns for all files in infoList.
	infoListCopy = constructTurn(infoListCopy)
	print(colored("\nAnalyzing syllable rate...",'red'))
	for dic in infoListCopy:
		print("Loading file: {0}\n".format(dic['jsonFile']))
		# Finding the syllable rate.
		dictionaryList = findSyllables(dic['jsonListTurns'])
		# Getting stats values.
		statsDic = stats(dictionaryList)
		# Adding slow / fast speech delims to the transcript.
		# Adds delims to individual word jsonList.
		dic['jsonList'] = addDelims(dictionaryList,statsDic,dic['jsonList'])
		# Visuzlizing the data.
		#visualize(dictionaryList)
	for dicCopy,dic in zip(infoListCopy,infoList):
		# Adding Hesitation markers back.
		dic['jsonList'] = addHesitation(dicCopy,dic)
	print(colored("Syllable rate analysis completed\n",'green'))
	return infoList

# *** Helper functions for speech rate analysis ***

# Function that returns a dictionary including the element, syllables per turn,
# and the syllable rate of the turn
# Returns: A list of dictionaries where each dictionary contains data for one turn.
def findSyllables(jsonListTurns):
	dictionaryList = []
	phoney = BigPhoney()
	for elem in jsonListTurns:
		syllableNum = sum([phoney.count_syllables(word) for word in elem[3].split()])
		dictionaryList.append({"elem" : elem, "syllableNum" : syllableNum,
			"syllRate" : round(syllableNum/(abs(elem[2]-elem[1])),2)})
	return dictionaryList

# Function that calculates the different stats values needed.
# Input: A list of dictionaries where each dictionary contains data for one turn.
# Returns: Dictionary containing the median, median absoulte deviation, 
# upperLimit, and lowerLimit
def stats(dictionaryList):
	allRates = []
	for dic in dictionaryList:
		allRates.append(dic['syllRate'])
	allRates = numpy.sort(numpy.array(allRates))
	median = numpy.median(allRates)
	median_absolute_deviation = round(robust.mad(allRates),2)
	lowerLimit = (median-(LimitDeviations*median_absolute_deviation))
	upperLimit = (median+(LimitDeviations*median_absolute_deviation))
	return {"median" : median, "medianAbsDev" : median_absolute_deviation,
		"upperLimit" : upperLimit, "lowerLimit" : lowerLimit}



# Function that adds fast / slow speech delimiters to the transcript
def addDelims(dictionaryList,statsDic,jsonList):
	jsonListTurns = [] ; words = [] ; fastCount = 0 ; slowCount = 0
	for elem in dictionaryList:
		if elem['syllRate'] <= statsDic['lowerLimit']: 
			elem['elem'][3] = delims['slowSpeech'] + elem['elem'][3] + delims['slowSpeech']
			slowCount+=1
		elif elem['syllRate'] >= statsDic['upperLimit']: 
			elem['elem'][3] = delims['fastSpeech'] + elem['elem'][3] + delims['fastSpeech']
			fastCount+=1
		jsonListTurns.append(elem['elem'])
	print("Fast turns found: {0}\nSlow turns found: {1}".format(slowCount,fastCount))
	for elem in jsonListTurns:
		for word in elem[3].split():words.append(word)
	for word,elem in zip(words,jsonList[1:]): elem[3] = str(word)
	return jsonList


# Function that removes hesitation markers from jsonList
def removeHesitation(infoList):
	for dic in infoList:
		dic['jsonList'] = [elem for elem in dic['jsonList'] if elem[3] != "%HESITATION"]
	return infoList

# Function that adds hesitation markers back
# Input: Two dictionaries in infoList.
# Returns: jsonList
def addHesitation(dicCopy,dic):
	jsonList = []
	for elem in dicCopy['jsonList']:jsonList.append(elem)
	for elem in dic['jsonList']:
		if elem[3] == "%HESITATION":jsonList.append(elem)
	jsonList[1:] = sorted(jsonList[1:], key = operator.itemgetter(1))
	return jsonList

# Function that visualizes the syllable rate to verify predictions
def visualize(dictionaryList):
	allRates = []
	for dic in dictionaryList:
		allRates.append(dic['syllRate'])
	allRates = numpy.sort(numpy.array(allRates))
	median = numpy.median(allRates)
	median_absolute_deviation = round(robust.mad(allRates),2)
	lowerLimit = (median-(LimitDeviations*median_absolute_deviation))
	upperLimit = (median+(LimitDeviations*median_absolute_deviation))
	print(allRates)
	print(median)
	print(median_absolute_deviation)
	print(lowerLimit)
	print(upperLimit)
	plt.figure(figsize=(10, 4))
	plt.hist(allRates,bins=14,color='c', edgecolor='k')
	plt.axvline(median,color='k', linestyle='dashed', linewidth=1)
	plt.axvline(lowerLimit,color='k', linestyle='dashed', linewidth=1)
	plt.axvline(upperLimit,color='k', linestyle='dashed', linewidth=1)
	plt.show()


















