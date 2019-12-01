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
from prettytable import PrettyTable				# Table printing library
import inquirer 								# Selection interface library.

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Global variables / invariants.
IBM_host_apiKey = "gateway-wdc.watsonplatform.net"	# Use this host is username is apikey
IBM_host = "stream.watsonplatform.net"				# Name of the IBM host / service.


base_model = "en-US_BroadbandModel"							# Default base model
headers = {'Content-Type' : "application/json"}				# Type of API data
customization_id_length = 36								# Length of custom ID
original = {"base-model": base_model, "custom-model" : None} # Default model values.
output = {"base-model": base_model, "custom-model" : None}	# Output for the script.


# User interface function
def interface(username,password):
	if username == 'apikey': global IBM_host ; IBM_host = IBM_host_apiKey
	main_menu(username,password,{})
	return output


# Main menu function
def main_menu(username,password,closure):
	while True:
		os.system('clear')
		x = PrettyTable()
		x.title = colored("Language Model Interface Settings",'red')
		x.field_names = [colored('Setting','blue'),colored('Value','blue')]
		x.add_row(["Current default model",output['base-model']])
		x.add_row(["Current custom model",str(output["custom-model"])])
		print("Welcome to Gailbot's custom " + colored('language model','red') + " interface!\n")
		print('Use options 1 through 8 to select the model(s) that you would like to use.\n'
			'Press 9 to proceed once all changes are made.\n')
		print(x)
		print("\nPlease choose one of the following options:")
		print("1. Select a custom language model")
		print("2. Delete a custom language model")
		print("3. Create a custom language model")
		print("4. Select a base language model")
		print("5. Obtain information for a specific base model")
		print("6. Train an existing custom language model")
		print("7. Advanced options")
		print("8. Reset selections to default values")
		print(colored("9. Proceed / Confirm selection\n",'green'))
		choice = input(" >>  ")
		if choice == '9' : return
		exec_menu(choice,menu_actions,username,password,closure)


# Custom model menu function
def custom_menu(username,password,closure):
	while True:
		os.system('clear')
		print("1. Train custom model using a single text corpus file")
		print("2. Train custom model using individual words")
		print(colored("3. Return to main menu\n",'red'))
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
		print(colored("5. Return to main menu\n",'red'))
		choice = input(" >>  ")
		if choice == '5': return
		exec_menu(choice,advanced_menu_actions,username,password,closure)

# Executes the appropriate function based on user input.
def exec_menu(choice,function_list,username,password,closure):
    os.system('clear')
    choice = choice.lower()
    if choice == '': return
    else:
    	#function_list[choice](username,password,closure)
        try: function_list[choice](username,password,closure)
        except KeyError: print("Invalid selection, please try again.\n")
    return

# *** Definitions for functions used in the main menu ***	

# Select the custom language model
def select_custom(username,password,closure):
	customID = ''
	customID,base = getCustom(username,password,closure)
	if customID == None: return
	output["custom-model"] = customID ; output['base-model'] = base
	input('\nSelected!\nPress any key to return to main menu...')


# Function that delets a custom model.	
def delete_custom(username,password,closure):
	customID,base = getCustom(username,password,closure)
	if customID == None: return
	print(colored("\nDeleting custom model: {}\nPress any key to proceed\nPress 0 to cancel\n".format(customID),'red'))
	verify = input(" >> ")
	if verify != '0' : delete_model(username,password,customID)
	input(colored('\nPress any key to return to main menu...','red'))

# Function that creates and trians a new custom model.
def create_custom(username,password,closure):
	closure = {}
	print("Enter custom model name\nPress 0 to go back to options\n") ;name = input(" >> ")
	if str(name) == '0': return
	os.system('clear')
	print("Enter custom model description\nPress 0 to go back to options\n")
	description = input(" >> ")
	if str(description) == '0' : return
	os.system('clear')
	customID = create_model(username = username, password = password, name = name, description = description)
	if customID == None: return
	closure["customID"] = customID
	custom_menu(username,password,closure)

# Function that lists all the base models.
def list_base_models(username,password,closure):
	list_models(username,password)
	modelJsonObject = list_models(username,password)
	modelList = formatBaseModels(modelJsonObject)
	val = generalInquiry(modelList,colored("Selected base model",'red'))
	if val == colored('Return','red'): return None
	output["base-model"] = val[:val.find(':')]
	output['custom-model'] = None

# Function that provides information for a base model.
def model_info(username,password,closure):
	list_models(username,password)
	modelJsonObject = list_models(username,password)
	modelList = formatBaseModels(modelJsonObject)
	val = generalInquiry(modelList,colored("Selected base model",'red'))
	base_name = val[:val.find(':')] ; os.system('clear')
	get_basemodel_info(username,password,base_name)
	input(colored('\nPress any key to return to main menu...','red'))

# Function that allows user to train an untrained custom language model.
def train_existing(username,password,closure):
	closure = {}
	customID,base = getCustom(username,password,closure)
	if customID == None: return
	closure["customID"] = customID
	custom_menu(username,password,closure)

# Function that resets the model selections to their default values
def reset(username,password,closure):
	output["custom-model"] = original["custom-model"]
	output ["base-model"] = original["base-model"]

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
}


# *** Functions that interact with Watson's STT API ***

# Function that returns a list of all available custom models
def get_model_list(username,password):
	uri = "https://{}/speech-to-text/api/v1/customizations".format(IBM_host)
	r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
	return json.loads(r.text)

# Function that deletes the model corresponding to the given model ID.
def delete_model(username,password,customID):
	print("\nDeleting custom model...")
	uri = "https://{}/speech-to-text/api/v1/customizations/".format(IBM_host)+customID
	r = requests.delete(uri, auth=(username,password), verify=False, headers=headers)
	respJson = r.json()
	if 'code' in respJson and respJson['code'] == 409: print(colored(respJson['error'],'red')) 


# Function that creates a new model
def create_model(username,password, description,name):
	modelJsonObject = list_models(username,password)
	modelList = formatBaseModels(modelJsonObject)
	val = generalInquiry(modelList,colored("Base model to train on",'red'))
	if val == colored('Return','red'): return None
	else: trainBase = val[:val.find(":")]
	print(colored("\nCreating custom language model...",'blue'))
	data = {"name" : name, "base_model_name" : trainBase, "description" : description}
	uri = "https://{}/speech-to-text/api/v1/customizations".format(IBM_host)
	jsonObject = json.dumps(data).encode('utf-8')
	resp = requests.post(uri, auth=(username,password), verify=False, headers=headers, data=jsonObject)

	print("Model creation returns: ", resp.status_code)
	if resp.status_code != 201:
	   print("Failed to create model")
	   print(resp.text)
	   return

	respJson = resp.json()
	customID = respJson['customization_id']
	print("Model customization_id: ", customID)
	return customID

# Function that lists all the base models available within the API.
def list_models(username,password):
	uri = "https://{}/speech-to-text/api/v1/models".format(IBM_host)
	r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
	respJson = r.json()
	return respJson["models"]

# Function that gets information for a specific base model
def get_basemodel_info(username,password,modelinfo):
	uri = "https://{}/speech-to-text/api/v1/models/".format(IBM_host) +modelinfo
	r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
	respJson = r.json()
	print("List models returns: ", r.status_code)
	print(r.text)

# Function that sends a corpus to the server to be analyzed into the new custom model.
def add_corpus(username, password, filename,customID):
	corpus_file = filename
	corpus_name = filename[:filename.rfind(".")]

	print("\nAdding corpus file...")
	uri = "https://{}/speech-to-text/api/v1/customizations/"+customID+"/corpora/".format(IBM_host) +corpus_name
	with open(corpus_file, 'rb') as f:
	   r = requests.post(uri, auth=(username,password), verify=False, headers=headers, data=f)

	print("Adding corpus file returns: ", r.status_code)
	if r.status_code != 201:
	   print(colored("\nFailed to add corpus file",'red'))
	   print(json.loads(r.text)["error"])
	   return

# Function that trains the model with the input data provided.
def train_model(username,password,customID):
	print(colored("\nTraining custom model...\n",'blue'))
	uri = "https://{}/speech-to-text/api/v1/customizations/".format(IBM_host) +customID+"/train"
	data = {}
	jsonObject = json.dumps(data).encode('utf-8')
	r = requests.post(uri, auth=(username,password), verify=False, data=jsonObject)

	print("Training request returns: ", r.status_code)
	if r.status_code != 200:
		print(r.text)
		print(colored(json.loads(r.text)["error"],'red'))
		return


	uri = "https://{}/speech-to-text/api/v1/customizations/".format(IBM_host) +customID
	r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
	respJson = r.json()
	status = respJson['status']



	time_to_run = 10
	while (status != 'available'):
	    time.sleep(10)
	    r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
	    respJson = r.json()
	    status = respJson['status']
	    # Suspend training if failed
	    if status == 'failed':
	    	error = json.loads(respJson['error'])
	    	print(colored("\n"+error['warnings'][0]['message'],'red'))
	    	delete_model(username,password,respJson['customization_id']) ; return
	    print("status: ", status, "(", time_to_run, ")")
	    time_to_run += 10
	print(colored("\nTraining complete!",'green'))

# Function that adds a single word to the model
def add_word(username,password,word,sounds_like,display_as,customID):
	print("\nAdding single word...")
	data = {"sounds_like" : [sounds_like], "display_as" : display_as}
	wordToAdd = word
	u = wordToAdd
	uri = "https://{}/speech-to-text/api/v1/customizations/".format(IBM_host) +customID+"/words/"+u
	jsonObject = json.dumps(data).encode('utf-8')
	r = requests.put(uri, auth=(username,password), verify=False, headers=headers, data=jsonObject)

	print("Adding single word returns: ", r.status_code)
	print("Single word added!")

# Function that adds multiple words to a model to be analyzed
def add_multiple_words(username,password,interim_data,customID):
	print(colored("\nAdding multiple words...\n",'blue'))
	print(interim_data)
	data = {"words": interim_data}
	uri = "https://{}/speech-to-text/api/v1/customizations/".format(IBM_host) +customID+"/words"
	jsonObject = json.dumps(data).encode('utf-8')
	r = requests.post(uri, auth=(username,password), verify=False, headers=headers, data=jsonObject)

	print("\nAdding multiple words returns: ", r.status_code)

	# Get status of model - only continue to training if 'ready'
	uri = "https://{}/speech-to-text/api/v1/customizations/".format(IBM_host) +customID
	r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
	respJson = r.json()
	status = respJson['status']
	print("\nChecking status of model for multiple words...")
	time_to_run = 10
	while (status != 'ready'):
	    time.sleep(10)
	    r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
	    respJson = r.json()
	    status = respJson['status']
	    print("status: ", status, "(", time_to_run, ")")
	    time_to_run += 10

	print(colored("Multiple words added!",'green'))

# Function that lists the custom words being used by a custom model.
def list_custom(username,password,customID):
	os.system('clear')
	print(colored("Listing custom words...",'blue'))
	uri = "https://{0}/speech-to-text/api/v1/customizations/{1}/words?sort=%2Balphabetical".format(IBM_host,customID)
	r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
	if r.status_code == 200: print(r.text)
	else : print(colored("\nUnable to list custom word information",'red'))

# Function that lists the corpora information for a custom model.
def list_corpora(username,password,customID):
	os.system('clear')
	print(colored("Listing corpora information for custom model...",'blue'))
	uri = "https://{0}/speech-to-text/api/v1/customizations/{1}/corpora".format(IBM_host,customID)
	r = requests.get(uri, auth=(username,password), verify=False, headers=headers)
	if r.status_code == 200: print(r.text)
	else : print(colored("\nUnable to list corpora information",'red'))

# Function that upgrades the base model of the given custom model
def upgrade_base_model(username,password,customID):
	print(colored("Upgrading base model...",'blue'))
	uri = "https://{0}/speech-to-text/api/v1/customizations/{1}/upgrade_model".format(IBM_host,customID)
	r = requests.post(uri, auth=(username,password), verify=False, headers=headers)
	if r.status_code == 200: print("Base model successfully upgraded")
	else: print(colored("\nBase model failed to upgrade",'red'))

# Function that resets the training of the given custom model.
def reset_model(username,password,customID):
	print(colored("Resetting custom model...",'blue'))
	uri = "https://{0}/speech-to-text/api/v1/customizations/{1}/reset".format(IBM_host,customID)
	r = requests.post(uri, auth=(username,password), verify=False, headers=headers)
	if r.status_code == 200: print("Model successfully reset")
	else: print(colored("\nModel failed to reset",'red'))


# *** Definitions for functions used in the custom menu ***

# Function that trains the model on a text corpus file
def single_file(username,password,closure):
	customID = closure["customID"]
	filename = input("Enter name of corpus file\n\n >> ")
	while not os.path.isfile(filename):
		print(colored("\nERROR: The specified file does not exist\nRe-enter corpus filename\n",'red'))
		filename = input(" >> ") ; os.system('clear')
	add_corpus(username,password,filename,customID)
	time.sleep(30)
	train_model(username,password,customID)
	input(colored('\nPress any key to return to main menu...','red'))

# Function that trains the model on multiple individual words.
def words(username,password,closure):
	customID = closure["customID"]
	final = []
	while True:
		data = {"word":"","sound":"","display":""}
		try:
			print("Enter word, the" 
				" sound of the word, and word spellings\nPress 0 to stop adding words\n")
			word,sound,display = input().split()
		except ValueError: break
		data.update({"word":word,"sound":sound,"display":display}) 
		final.append(data)
	add_multiple_words(username,password,final,customID)
	train_model(username,password,customID)
	input(colored('\nPress any key to return to main menu...','red'))


# Actions for the new custom model menu
custom_menu_actions = {
	'1': single_file,
	'2': words
}


# *** Definitions for functions used in the advanced menu ***

# Function that resets a custom language model
def reset_custom(username,password,closure):
	customID,base = getCustom(username,password,closure)
	if customID == None: return
	reset_model(username,password,customID)
	input('Press any key to return to main menu...')

# Function that upgrades the base model of a custom language model.
def upgrade_base_custom(username,password,closure):
	customID,base = getCustom(username,password,closure)
	if customID == None: return
	upgrade_base_model(username,password,customID)
	input('Press any key to return to main menu...')

# Function that lists the corpora details for a custom model
def list_corpora_custom(username,password,closure):
	customID,base = getCustom(username,password,closure)
	if customID == None: return
	list_corpora(username,password,customID)
	input('Press any key to return to main menu...')

# Function that lists the custom words that a custom model is using
def list_custom_words(username,password,closure):
	customID,base = getCustom(username,password,closure)
	if customID == None: return
	list_custom(username,password,customID)
	input('Press any key to return to main menu...')

# Actions for the new advanced menu
advanced_menu_actions = {
	'1': reset_custom,
	'2': upgrade_base_custom,
	'3': list_corpora_custom,
	'4': list_custom_words
}


# *** Helper functions  ***


# Function that formats custom models to allow easy selection
def getCustom(username,password,closure):
	x = PrettyTable() ; choiceList = []
	x.title = colored("Available custom acoustic models",'red')
	x.field_names = [colored("Language Model",'blue'),colored("Description",'blue'),
		colored("Customization ID",'blue'),colored('Status','blue')]
	models = get_model_list(username,password)
	for dic in models["customizations"]:
		x.add_row([dic['name'],dic['description'],dic['customization_id'],dic['status']])
		choiceList.append(dic['name'] +" :" +dic['customization_id'])
	print(x)
	res = generalInquiry(choiceList,colored("Selected acoustic model",'red'))
	if res == colored('Return','red'):return None,None
	base = None
	for dic in models["customizations"]: 
		if dic['customization_id'] == res[res.find(":")+1:]: base = dic['base_model_name']
	return res[res.find(":")+1:], base


# Function that allows user to select one option
def generalInquiry(choiceList,message):
	choiceList.append(colored("Return",'red'))
	options = [
			inquirer.List('inputVal',
				message=message,
				choices=choiceList,
				),
		]
	print(colored("Use arrow keys to navigate\n",'blue'))
	print(colored("Proceed --> Enter / Return key\n",'green'))
	return inquirer.prompt(options)['inputVal']

# Function that formats obtained base models into a name list
# Returns: List of all the names of thew base models.
def formatBaseModels(jsonObject):
	modelList = []
	for model in jsonObject: modelList.append(model["name"] + ": "+
		model["description"])
	return modelList


if __name__ == '__main__':
 	interface(sys.argv[1],sys.argv[2])











