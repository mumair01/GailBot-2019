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
import matplotlib.pyplot as plt 				# Library to visualize data
from statsmodels import robust 					# Statistics library.
import tensorflow as tf 						# Deep neural network library
import logging

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

def analyzeSyllableRate(infoList):
	turnList = constructTurn(infoList)
	for dic in turnList:
		# Finding the syllable rate.
		dictionaryList = findSyllables(dic['jsonListTurns'])
		# Getting stats values.
		statsDic = stats(dictionaryList)
		# Adding slow / fast speech delims to the transcript.
		dic['jsonListTurns'] = addDelims(dictionaryList,statsDic)
		# Visualizing the data.
		#visualize(dictionaryList)
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
def addDelims(dictionaryList,statsDic):
	jsonListTurns = []
	for elem in dictionaryList:
		if elem['syllRate'] <= statsDic['lowerLimit']: 
			elem['elem'][3] = delims['slowSpeech'] + elem['elem'][3] + delims['slowSpeech']
		elif elem['syllRate'] >= statsDic['upperLimit']: 
			elem['elem'][3] = delims['fastSpeech'] + elem['elem'][3] + delims['fastSpeech']
		jsonListTurns.append(elem['elem'])
	return jsonListTurns

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










	