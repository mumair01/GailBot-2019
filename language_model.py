'''
	Script that provides an interface between the user and IBM Watson's STT
	API's custom langage model.

	Please see IBM's documentation here:
	https://cloud.ibm.com/apidocs/speech-to-text#create-a-custom-language-model

	Part of the Gailbot-3 development project.

	Developed by:

		Muhammad Umair								
		Tufts University
		Human Interaction Lab at Tufts

	Initial development: 5/20/19	

	Changelog:
	
'''


import requests
import json
import sys, time, os
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from termcolor import colored

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Global variables / invariants.
base_model = "en-US_BroadbandModel"							# Default base model
headers = {'Content-Type' : "application/json"}				# Type of API data
customization_id_length = 36								# Length of custom ID
original = {"base-model": base_model, "custom-model" : None} # Default model values.
output = {"base-model": base_model, "custom-model" : None}	# Output for the script.


# User interface function
def interface(username,password):
	main_menu(username,password,{})
	return output


# Main menu function
def main_menu(username,password,closure):
	while True:
		os.system('clear')
		print("Welcome to Gailbot's custom " + colored('language model','red') + " interface!\n")
		print('Use options 1 through 8 to select the model(s) that you would like to use.\n'
			'Press 9 to proceed once all changes are made.\n'
			'\nCurrent default model: ' + output['base-model'] + '\n'
			'Current custom model: ' + str(output["custom-model"]) + '\n' )
		print("Please choose one of the following options:")
		print("1. Select a custom language model")
		print("2. Delete a custom language model")
		print("3. Create a custom language model")
		print("4. Select a base language model")
		print("5. Obtain information for a specific base model")
		print("6. Train an existing custom language model")
		print("7. Advanced options")
		print("8. Reset selections to default values")
		print(colored("9. Proceed / Confirm selection",'green'))
		print(colored("10. Quit",'red'))
		choice = input(" >>  ")
		if choice == '9' : return
		exec_menu(choice,menu_actions,username,password,closure)


# Custom model menu function
def custom_menu(username,password,closure):
	while True:
		os.system('clear')
		print("1. Train custom model using a single text corpus file")
		print("2. Train custom model using individual words")
		print("3. Return to main menu")
		choice = input(" >>  ")
		if choice == '3' : return
		exec_menu(choice,custom_menu_actions,username,password,closure)
		if choice == '1' or choice == '2': return

# Advanced options menu function
def advanced_menu(username,password,closure):
	while True:
		os.system('clear')
		print(colored("Advanced options\n",'red'))
		print("1. Reset a custom language model")
		print("2. Upgrade base model of an existing custom language model")
		print("3. List all corpus words used to train a custom language model")
		print("4. List all individual words used to train a custom language model")
		print("5. Return to main menu")
		choice = input(" >>  ")
		if choice == '5': return
		exec_menu(choice,advanced_menu_actions,username,password,closure)

# *** Helper functions ***

# Function that gets custom ID input. (Helper Function)
def get_ID():
	customID = input("Enter customization ID from list\nPress 0 to go back to options\n")
	if customID == '0' : return '0'
	while len(customID) != 36:
		customID = input("\nERROR: Input must be 36 characters\nEnter customization ID from list\n"
			"Press 0 to go back to options\n")
		if customID == '0' : return '0'
	return customID

# *** Definitions for functions used in the main menu ***	

# Exit program
def exit(username,password,closure):
    sys.exit()
 
# Select the custom language model
def select_custom(username,password,closure):
	customID = ''
	get_model_list(username,password)
	print("NOTE: The custom language model's base model must be the same as",
	 "the selected base model\nCurrent base model: " + output['base-model'])
	customID = get_ID()
	if customID == '0': return
	output["custom-model"] = customID
	input('\nSelected!\nPress any key to return to main menu...')
 
# Function that delets a custom model.	
def delete_custom(username,password,closure):
	get_model_list(username,password)
	customID = get_ID()
	if customID == '0': return
	delete_model(username,password,customID)
	input('Press any key to return to main menu...')

# Function that creates and trians a new custom model.
def create_custom(username,password,closure):
	closure = {}
	try:
		name, description = input("Enter custom model name and description\n"
			"Press 0 to go back to options\n").split()
	except ValueError: return
	customID = create_model(username = username, password = password, name = name, description = description)
	closure["customID"] = customID
	custom_menu(username,password,closure)
	
# Chooses the default base model.
def default(username,password,closure):
	return output

# Function that lists all the base models.
def list_base_models(username,password,closure):
	list_models(username,password)
	base_name = input("Enter base model name\nPress 0 to go back to options\n")
	if base_name == '0': return											
	while((base_name[base_name.find('_')+1:] != 'BroadbandModel')
		and (base_name[base_name.find('_')+1:] != 'NarrowbandModel')):
		base_name = input("Enter base model name\nPress 0 to go back to options\n")	
		if base_name == '0': return
	output["base-model"] = base_name

# Function that provides information for a base model.
def model_info(username,password,closure):
	base_name = input("Enter base model name\nPress 0 to go back to options\n")
	if base_name == '0': return
	while((base_name[base_name.find('_')+1:] != 'BroadbandModel')
		and (base_name[base_name.find('_')+1:] != 'NarrowbandModel')):
		base_name = input("Enter base model name\nPress 0 to go back to options\n")	
		if base_name == '0': return
	get_basemodel_info(username,password,base_name)
	input('Press any key to return to main menu...')

# Function that allows user to train an untrained custom language model.
def train_existing(username,password,closure):
	closure = {}
	get_model_list(username,password)
	customID = get_ID()
	if customID == '0': return
	closure["customID"] = customID
	custom_menu(username,password,closure)

# Function that resets the model selections to their default values
def reset(username,password,closure):
	output["custom-model"] = original["custom-model"]
	output ["base-model"] = original["base-model"]
	input('Values reset!\nPress any key to return to main menu...')

# Executes the appropriate function based on user input.
def exec_menu(choice,function_list,username,password,closure):
    os.system('clear')
    choice = choice.lower()
    if choice == '': return
    else:
        try: function_list[choice](username,password,closure)
        except KeyError: print("Invalid selection, please try again.\n")
    return


# Actions for the main menu
menu_actions = {
    'main_menu': main_menu,
    '1': select_custom,
    '2': delete_custom,
    '3': create_custom,
    '4': list_base_models,
    '5': model_info,
    '6': train_existing,
    '7': advanced_menu,
    '8': reset,
    '10': exit
}

# *** Definitions for functions used in the custom menu ***

# Function that trains the model on a text corpus file
def single_file(username,password,closure):
	customID = closure["customID"]
	filename = input("Enter name of corpus file\n")
	while not os.path.isfile(filename):
		filename = input("ERROR: The specified file does not exist\nRe-enter corpus filename\n")
	add_corpus(username,password,filename,customID)
	train_model(username,password,customID)
	input('Press any key to return to main menu...')

# Function that trains the model on multiple individual words.
def words(username,password,closure):
	customID = closure["customID"]
	final = []
	while True:
		data = {"word":"","sound":"","display":""}
		try:
			word,sound,display = input("Enter word, the" 
				" sound of the word, and word spellings\nPress 0 to stop adding words\n").split()
		except ValueError: break
		data.update({"word":word,"sound":sound,"display":display}) 
		final.append(data)
	add_multiple_words(username,password,final,customID)
	train_model(username,password,customID)
	input('Press any key to return to main menu...')


# Actions for the new custom model menu
custom_menu_actions = {
	'1': single_file,
	'2': words
}

# *** Definitions for functions used in the advanced menu ***

# Function that resets a custom language model
def reset_custom(username,password,closure):
	get_model_list(username,password)
	customID = get_ID()
	if customID == '0': return
	reset_model(username,password,customID)
	input('Press any key to return to main menu...')

# Function that upgrades the base model of a custom language model.
def upgrade_base_custom(username,password,closure):
	get_model_list(username,password)
	customID = get_ID()
	if customID == '0': return
	upgrade_base_model(username,password,customID)
	input('Press any key to return to main menu...')

# Function that lists the corpora details for a custom model
def list_corpora_custom(username,password,closure):
	get_model_list(username,password)
	customID = get_ID()
	if customID == '0': return
	list_corpora(username,password,customID)
	input('Press any key to return to main menu...')

# Function that lists the custom words that a custom model is using
def list_custom_words(username,password,closure):
	get_model_list(username,password)
	customID = get_ID()
	if customID == '0': return
	list_custom(username,password,customID)
	input('Press any key to return to main menu...')

# Actions for the new advanced menu
advanced_menu_actions = {
	'1': reset_custom,
	'2': upgrade_base_custom,
	'3': list_corpora_custom,
	'4': list_custom_words
}

# *** Functions that interact with Watson's STT API ***

# Function that lists the custom words being used by a custom model.
def list_custom(username,password,customID):
	print("Listing custom words...")
	uri = "https://stream.watsonplatform.net/speech-to-text/api/v1/customizations/{}/words?sort=%2Balphabetical".format(customID)
	r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
	if r.status_code == 200: print(r.text)
	else : print("Unable to list custom word information")

# Function that lists the corpora information for a custom model.
def list_corpora(username,password,customID):
	print("Listing corpora information for custom model...")
	uri = "https://stream.watsonplatform.net/speech-to-text/api/v1/customizations/{}/corpora".format(customID)
	r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
	if r.status_code == 200: print(r.text)
	else : print("Unable to list corpora information")

# Function that upgrades the base model of the given custom model
def upgrade_base_model(username,password,customID):
	print("Upgrading base model...")
	uri = "https://stream.watsonplatform.net/speech-to-text/api/v1/customizations/{}/upgrade_model".format(customID)
	r = requests.post(uri, auth=(username,password), verify=False, headers=headers)
	if r.status_code == 200: print("Base model successfully upgraded")
	else: print("Base model failed to upgrade")

# Function that resets the training of the given custom model.
def reset_model(username,password,customID):
	print("Resetting custom model...")
	uri = "https://stream.watsonplatform.net/speech-to-text/api/v1/customizations/{}/reset".format(customID)
	r = requests.post(uri, auth=(username,password), verify=False, headers=headers)
	if r.status_code == 200: print("Model successfully reset")
	else: print("Model failed to reset")

# Function that returns a list of all available custom models
def get_model_list(username,password):
	print("\nGetting custom models...")
	uri = "https://stream.watsonplatform.net/speech-to-text/api/v1/customizations"
	r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
	print("Get models returns: ", r.status_code)
	print(r.text)

# Function that deletes the model corresponding to the given model ID.
def delete_model(username,password,customID):
	print("\nDeleting custom model...")
	uri = "https://stream.watsonplatform.net/speech-to-text/api/v1/customizations/"+customID
	r = requests.delete(uri, auth=(username,password), verify=False, headers=headers)
	respJson = r.json()

# Function that lists all the base models available within the API.
def list_models(username,password):
	uri = "https://stream.watsonplatform.net/speech-to-text/api/v1/models"
	r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
	respJson = r.json()
	print("List models returns: ", r.status_code)
	print(r.text)

# Function that gets information for a specific base model
def get_basemodel_info(username,password,modelinfo):
	uri = "https://stream.watsonplatform.net/speech-to-text/api/v1/models/"+modelinfo
	r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
	respJson = r.json()
	print("List models returns: ", r.status_code)
	print(r.text)

# Function that creates a new model
def create_model(username,password, description,name):
	print("\nCreating custom model...")
	data = {"name" : name, "base_model_name" : "en-US_BroadbandModel", "description" : description}
	uri = "https://stream.watsonplatform.net/speech-to-text/api/v1/customizations"
	jsonObject = json.dumps(data).encode('utf-8')
	resp = requests.post(uri, auth=(username,password), verify=False, headers=headers, data=jsonObject)

	print("Model creation returns: ", resp.status_code)
	if resp.status_code != 201:
	   print("Failed to create model")
	   print(resp.text)
	   sys.exit(-1)

	respJson = resp.json()
	customID = respJson['customization_id']
	print("Model customization_id: ", customID)
	return customID

# Function that sends a corpus to the server to be analyzed into the new custom model.
def add_corpus(username, password, filename,customID):
	corpus_file = filename
	corpus_name = filename[:filename.rfind(".")]

	print("\nAdding corpus file...")
	uri = "https://stream.watsonplatform.net/speech-to-text/api/v1/customizations/"+customID+"/corpora/"+corpus_name
	with open(corpus_file, 'rb') as f:
	   r = requests.post(uri, auth=(username,password), verify=False, headers=headers, data=f)

	print("Adding corpus file returns: ", r.status_code)
	if r.status_code != 201:
	   print("Failed to add corpus file")
	   print(r.text)
	   sys.exit(-1)


# Function that trains the model with the input data provided.
def train_model(username,password,customID):
	print("\nTraining custom model...")
	uri = "https://stream.watsonplatform.net/speech-to-text/api/v1/customizations/"+customID+"/train"
	data = {}
	jsonObject = json.dumps(data).encode('utf-8')
	r = requests.post(uri, auth=(username,password), verify=False, data=jsonObject)

	print("Training request returns: ", r.status_code)
	if r.status_code != 200:
	   print("Training failed to start - exiting!")
	   sys.exit(-1)

	uri = "https://stream.watsonplatform.net/speech-to-text/api/v1/customizations/"+customID
	r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
	respJson = r.json()
	status = respJson['status']
	time_to_run = 10
	while (status != 'available'):
	    time.sleep(10)
	    r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
	    respJson = r.json()
	    status = respJson['status']
	    print("status: ", status, "(", time_to_run, ")")
	    time_to_run += 10
	print("Training complete!")

# Function that adds a single word to the model
def add_word(username,password,word,sounds_like,display_as,customID):
	print("\nAdding single word...")
	data = {"sounds_like" : [sounds_like], "display_as" : display_as}
	wordToAdd = word
	u = wordToAdd
	uri = "https://stream.watsonplatform.net/speech-to-text/api/v1/customizations/"+customID+"/words/"+u
	jsonObject = json.dumps(data).encode('utf-8')
	r = requests.put(uri, auth=(username,password), verify=False, headers=headers, data=jsonObject)

	print("Adding single word returns: ", r.status_code)
	print("Single word added!")

# Function that adds multiple words to a model to be analyzed
def add_multiple_words(username,password,interim_data,customID):
	print("\nAdding multiple words...")
	print(interim_data)
	data = {"words": interim_data}
	uri = "https://stream.watsonplatform.net/speech-to-text/api/v1/customizations/"+customID+"/words"
	jsonObject = json.dumps(data).encode('utf-8')
	r = requests.post(uri, auth=(username,password), verify=False, headers=headers, data=jsonObject)

	print("Adding multiple words returns: ", r.status_code)

	# Get status of model - only continue to training if 'ready'
	uri = "https://stream.watsonplatform.net/speech-to-text/api/v1/customizations/"+customID
	r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
	respJson = r.json()
	status = respJson['status']
	print("Checking status of model for multiple words...")
	time_to_run = 10
	while (status != 'ready'):
	    time.sleep(10)
	    r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
	    respJson = r.json()
	    status = respJson['status']
	    print("status: ", status, "(", time_to_run, ")")
	    time_to_run += 10

	print("Multiple words added!")


if __name__ == '__main__':
 	output = interface('7af17e06-b9dc-4fc0-bcfe-ec5dfe9a17ed','1GJceSXy7mbQ')
 	print(output)









