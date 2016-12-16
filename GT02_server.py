from flask import Flask
import requests
import json
import keys
import suffixes
import jsonify
from py_bing_search import PyBingWebSearch
from fuzzywuzzy import fuzz, process


##################
### Configuration
##################

from flask import Flask
app = Flask(__name__) 

clearbit_key = keys.clearbit_key
bing_key = keys.bing_key

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
### Helper Functions
#################################

def output(company, result):
	return json.dumps({'domain': result, 'score': str(fuzz.partial_ratio(company, result))})

def selector(company, f):
	r = f(company)
	if r != None:
		return output(company, r)
	return json.dumps({'domain': None})


#################################
### Endpoint WIP
#################################

@app.route('/domainlookup/all/<company>', methods=['GET'])
def autocompleteAll(company):

	r = autocompleteOld(company)
	if r != None:
		return output(company, r)
	r = fuzzyMatch(company)
	if r:
		return output(company, r)
	r = autocompleteNew(company)
	if r != None:
		return output(company, r)
	return json.dumps({'domain': None})
	

@app.route('/domainlookup/old/<company>', methods=['GET'])
def domainLookupOld(company):
	return selector(company, autocompleteOld)

@app.route('/domainlookup/new/<company>', methods=['GET'])
def domainLookupNew(company):
	return selector(company, autocompleteNew)

@app.route('/domainlookup/fuzzymatch/<company>', methods=['GET'])
def domainLookupFuzzy(company):
	return selector(company, fuzzyMatch)