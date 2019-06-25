'''
	Post-processing script that implements different audio analysis techniques
	to determine characteristics of speech that can be transcribed.

	Developed by:

		Muhammad Umair								
		Tufts University
		Human Interaction Lab at Tufts

	Initial development: 6/25/19
'''

import os,sys
import numpy 				# Library to have multi-dimensional homogenous arrays.
import copy 				# Copying module.
import operator				# Sorting library
from termcolor import colored


# *** Definitions for audio characteristics analysis functions ***

# Main driver function
def analyzeSound(infoList):
	print(colored("\nAnalyzing sound characteristics...",'blue'))
	for dic in infoList:
		print(dic['jsonFile'])
	print(colored("Sound characteristics analysis completed\n",'green'))
	return infoList
	



# *** Helper functions ***