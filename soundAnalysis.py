'''
	Post-processing script that implements beat analysis on Gailbot transcripts.

	Developed by:

		Muhammad Umair								
		Tufts University
		Human Interaction Lab at Tufts

	Initial development: 6/25/19
'''

import os,sys
import numpy 						# Library to have multi-dimensional homogenous arrays.
import copy 						# Copying module.
import operator						# Sorting library
from termcolor import colored		# Coloring library
import pyaudio 						# Audio signal processing library
import wave 						# Library to read audio
from pydub import AudioSegment
from scipy.io.wavfile import read
import matplotlib.pyplot as plt


# Gailbot scripts
import rateAnalysis
import CHAT


# *** Definitions for bea:t transcription functions ***
def analyzeSound(infoList):
	return infoList


# *** Helper functions ***
















