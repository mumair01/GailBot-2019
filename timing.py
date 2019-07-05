'''
	Post-processing script that implements pause / gap transcription in terms 
	of both beats and absolute timing.

	Part of the Gailbot-3 development project.

	Developed by:

		Muhammad Umair								
		Tufts University
		Human Interaction Lab at Tufts

	Initial development: 6/6/19	
'''

import sys,os
from termcolor import colored					# Text coloring library.

# Gailbot scripts
import rateAnalysis

# *** Global variables / invariants ***

# Describes how many beats 1 second is equal to.
SECStoBEATS = 4


# *** Main pause / gap transcription functions ***

# Function that adds pause markers to the combined speaker transcripts.
# Pauses added to combined list to prevent end of line pause transcriptions.
# Input: list of lists containing dictionaries.
# 		CHATVals dictionary containing transcription thresholds
# Output : list of lists containing dictionaries.
def pauses(infoList,CHATVals):
	for item in infoList:
		# Getting appropriate transcription function
		pauseFunc,closure = transcriptionFunction(item,CHATVals)
		# Adding pause markers
		newList = []
		jsonListCombined = item[0]['jsonListCombined']
		for count,curr in enumerate(jsonListCombined[:-1]):
			nxt = jsonListCombined[count+1]
			# Only add pauses if current and next speaker is the same.
			if curr[0] != nxt[0]:newList.append(curr);continue
			diff = round(nxt[1] - curr[2],2)
			# In this case, the latch marker is added.
			if diff >= CHATVals['lowerBoundLatch'] and diff <= CHATVals['upperBoundLatch']:
				curr[3] += ' ' + CHATsymbols['latch'] + ' '
			# In this case, the normal pause markers are added.
			elif diff >= CHATVals['lowerBoundPause'] and diff <= CHATVals['upperBoundPause']:
				curr[3] += pauseFunc(diff,closure)
			# In this case, micropause markers are added.
			elif diff >= CHATVals['lowerBoundMicropause']and diff <= CHATVals['upperBoundMicropause']:
				curr[3] += pauseFunc(diff,closure)
			# In this case, very large pause markers are added
			elif diff > CHATVals['LargePause']:
				largePause = ['*PAU',curr[2],nxt[1],pauseFunc(diff,closure)]
				newList.extend([curr,largePause]) ; continue
			newList.append(curr)
		newList.append(jsonListCombined[-1])
		for dic in item: dic['jsonListCombined'] = newList
	return infoList


# Function that adds gaps to the transcript
# Input: list of lists containing dictionaries.
# Output : list of lists containing dictionaries.
def gaps(infoList,CHATVals):
	for item in infoList:
		if CHATVals['beatsMode']: gapFunc = beatsTiming ; closure = item[0]['syllPerSec']
		else: gapFunc = absoluteTiming ; closure = CHATVals['upperBoundMicropause']
		newList = [] ; jsonListCombined = item[0]['jsonListCombined']
		for count,curr in enumerate(jsonListCombined[:-1]):
			nxt = jsonListCombined[count+1]
			diff = round(nxt[1] - curr[2],2)
			if diff >= CHATVals['gap']:
				gap = ['*GAP',curr[2],nxt[1],gapFunc(diff,closure)]
				newList.extend([curr,gap]);
			else:newList.append(curr)
		newList.append(jsonListCombined[-1])
		for dic in item: dic['jsonListCombined'] = newList
	return infoList


# *** Functions involved in calculating pauses / gaps in beat timing ***

# Function to determine beat / abolute and return appropriate function to apply
# Input: Item list containing one or more dictionaries.
# Return: Pause function to apply 
# 		 Sets the syllPerSec parameter.
def transcriptionFunction(item,CHATVals):
	if CHATVals['beatsMode']: 
		syllPerSec = calcSyllPerSec(item[0]['jsonListCombined'])
		pauseFunc = beatsTiming ; closure = syllPerSec
	else: 
		syllPerSec = None ; pauseFunc = absoluteTiming
		closure = CHATVals['upperBoundMicropause']
	for dic in item: dic['syllPerSec'] = syllPerSec
	return pauseFunc,closure


# Function used to calculate the syllable rate per second for a combined conversation.
# Input: Combined conversation jsonList
# Returns: Median Syllable rate per second.
def calcSyllPerSec(jsonListCombined):
	dictionaryList = rateAnalysis.findSyllables(jsonListCombined)
	statsDic = rateAnalysis.stats(dictionaryList)
	syllPerSec = statsDic['median']
	return syllPerSec


# Function that returns pauses / gaps in beats timing format
def beatsTiming(diff,syllPerSec):
	beats = (float(diff*syllPerSec))
	# Converting the beat value to seconds.
	beatsSeconds = float(beats / SECStoBEATS)
	#return ' ( ' + ('.'*beats) +' ) '
	return ' (' +str(round(beatsSeconds,1)) + ')'

# Function that returns pauses / gaps in absolute timing format
def absoluteTiming(diff,upperBoundMicropause):
	if diff <= upperBoundMicropause: return ' (.) '
	return ' (' + str(round(diff,1)) + ')'











