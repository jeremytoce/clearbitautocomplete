from flask import Flask
import requests
import json
import keys
import suffixes
from py_bing_search import PyBingWebSearch
from fuzzywuzzy import fuzz, process
from flask_restful import Resource, Api


##################
### Configuration
##################

app = Flask(__name__) 
api = Api(app)

clearbit_key = keys.clearbit_key
bing_key = keys.bing_key

#######################################
### New Clearbit Autocomplete Endpoint
#######################################

def autocompleteNew(company):

	r = requests.get('https://company.clearbit.com/v1/domains/find?name='+company, auth=(clearbit_key, ''))
	if (len(r.json()) > 0):
		return (r.json()['domain'])
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

def autocompleteFuzzy(company):

	search_term = str.lower(company).split(' ')

	for word in search_term: 
		if word in suffixes.suffixes:
			search_term.remove(word)

	companyScrubbed = ' '.join(search_term)

	bing_web = PyBingWebSearch(bing_key, companyScrubbed, web_only=False) 
	r = bing_web.search(limit=25, format='json')
	flag = False
	i = 0

	while (i <= 25):
		try:
			rawURL = r[i].url
			if ('https://' in rawURL):
				modURL = rawURL.replace('https://','').split('/')
			if ('http://' in rawURL):
				modURL = rawURL.replace('http://','').split('/')
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
	return ({'domain': result, 'score': str(fuzz.partial_ratio(company, result))})

def selector(company, f):
	r = f(company)
	if r != None:
		return output(company, r)
	return ({'domain': None, 'score': 0})


#################################
### Endpoint WIP
#################################

class Old(Resource):
    def get(self, company):
    	return selector(company, autocompleteOld)

class New(Resource):
    def get(self, company):
    	return selector(company, autocompleteNew)

class Fuzzy(Resource):
    def get(self, company):
    	return selector(company, autocompleteFuzzy)

class All(Resource):
    def get(self, company):
    	r = autocompleteOld(company)
    	if r != None:
    		return output(company, r)
    	r = autocompleteFuzzy(company)
    	if r:
    		return output(company, r)
    	r = autocompleteNew(company)
    	if r != None:
    		return output(company, r)
    	return  ({'domain': None})

api.add_resource(Old, '/domainlookup/old/<string:company>')
api.add_resource(New, '/domainlookup/new/<string:company>')
api.add_resource(Fuzzy, '/domainlookup/fuzzy/<string:company>')
api.add_resource(All, '/domainlookup/all/<string:company>')

app.run(debug=True)