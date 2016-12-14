from flask import Flask
import requests
import json
from py_bing_search import PyBingWebSearch
from fuzzywuzzy import fuzz, process
import suffixes as suffixes

##################
### Configuration
##################

clearbit_key = ''
bing_key = ''


#######################################
### New Clearbit Autocomplete Endpoint
#######################################

def autocompleteNew(company):

	r = requests.get('https://company.clearbit.com/v1/domains/find?name='+company, auth=(clearbit_key, ''))
	if (len(r.json()) > 0):
		return (r.json())
	else: 
		return None

######################################
### Old Clearbit Autocomplete Endpoint
######################################

def autocompleteOld(company):

	r = requests.get('https://autocomplete.clearbit.com/v1/companies/suggest?query='+company)
	if (len(r.json()) > 0):
		return (r.json()[0]['domain'])
	else: 
		return None

#################################
### Bing Search w/ Fuzzy Matching
#################################

def fuzzyMatch(company):

	search_term = str.lower(company).split(' ')

	for word in search_term: 
		if word in suffixes.suffixes:
			search_term.remove(word)

	companyScrubbed = ' '.join(search_term)

	bing_web = PyBingWebSearch(bing_key, companyScrubbed, web_only=False) 
	r = bing_web.search(limit=25, format='json')
	flag = False
	i = 0

	while (i < 25):
		try:
			rawURL = r[i].url
			if ('https://' in rawURL):
				modURL = rawURL.replace('https://','').split('/')
			if ('http://' in rawURL):
				modURL = rawURL.replace('http://','').split('/')
			print('comparing ' + modURL[0] + ' and ' + companyScrubbed + ': ' + str(fuzz.partial_ratio(modURL[0], companyScrubbed)))
			if (fuzz.partial_ratio(modURL[0], companyScrubbed) < 50):
				i+=1		
			else:
				return (modURL[0])
				break
		except:
			return (None)
	return (None)


#################################
### Endpoint WIP
#################################

def autocomplete(company):

	r = autocompleteOld(company)
	if r != None:
		print ('old: ' + str(r))
		return

	r = fuzzyMatch(company)
	if r:
		print (r)
		return
		
	r = autocompleteNew(company)
	if r != None:
		print ('new: ' + str(r))
		return




