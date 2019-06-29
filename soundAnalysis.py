'''
	Post-processing script that implements beat analysis on Gailbot transcripts.

	Developed by:

		Muhammad Umair								
		Tufts University
		Human Interaction Lab at Tufts

	Initial development: 6/25/19
'''

import os,sys
import numpy 					# Library to have multi-dimensional homogenous arrays.
import copy 					# Copying module.
import operator					# Sorting library
from termcolor import colored	# Coloring library
import pyaudio 					# Audio signal processing library
import wave 					# Library to read audio
from pydub import AudioSegment
from scipy.io.wavfile import read
import matplotlib.pyplot as plt
import rateAnalysis
import CHAT

# *** Definitions for beat transcription functions ***







# *** Helper functions ***





def analyzeSound(infoList):
	return infoList
	infoListCopy = copy.deepcopy(infoList)
	# Removing hesitation markers from list
	infoListCopy = rateAnalysis.removeHesitation(infoListCopy)
	# Constructing turns for all files in infoList.
	infoListCopy = CHAT.constructTurn(infoListCopy)
	# Finding the syllable rate.
	for infoDic in infoListCopy:
		dictionaryList = rateAnalysis.findSyllables(infoDic['jsonListTurns'][1:])
		# Getting stats values.
		statsDic = rateAnalysis.stats(dictionaryList)
		for elem in dictionaryList:print(elem)
		print(statsDic)
	sys.exit()















