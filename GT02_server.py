from flask import Flask
import requests
import json
import keys
import suffixes
import os
from py_bing_search import PyBingWebSearch
from fuzzywuzzy import fuzz, process
from flask_restful import Resource, Api, reqparse
from parse import *

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

	r = requests.get('https://company.clearbit.com/v1/domains/find?name='+company_scrub(company), auth=(clearbit_key, ''))
	if (len(r.json()) > 0):
		return (r.json()['domain'])
	else: 
		return None

######################################
### Old Clearbit Autocomplete Endpoint
######################################

def autocompleteOld(company):

	print (company_scrub(company))
	r = requests.get('https://autocomplete.clearbit.com/v1/companies/suggest?query='+company_scrub(company))
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
### Bing Search w/ Fuzzy Matching
#################################

def autocomplete_fuzzy_cog(company):

	i = 0
	headers = {'Ocp-Apim-Subscription-Key':'7cbff62212f34854a526ba73583773e0'}
	company_scrubbed = company_scrub(company)
	url = 'https://api.cognitive.microsoft.com/bing/v5.0/search?q='+company+'&count=25&offset=0&mkt=en-us&safesearch=Moderate'
	r = requests.get(url, headers=headers)
	result = (r.json())

	while (i <= 10):

		try: 
			rawURL = (result['webPages']['value'][i]['displayUrl'])
		except:
			return (None)

		try:
			if ('http://' not in rawURL and 'https://' not in rawURL):
				modURL = rawURL.split('/')
			if ('https://' in rawURL):
				modURL = rawURL.replace('https://','').split('/')
			if ('http://' in rawURL):
				modURL = rawURL.replace('http://','').split('/')
			if (fuzz.partial_ratio(modURL[0], company_scrubbed) < 50):	
				i+=1
			else:
				return (modURL[0])
				break
		except Exception as e:
			print(e)
			return (None)
	return (None)

#################################
### Helper Functions
#################################

def output(company, result, source):
	return ({'company': company, 'domain': http_cleaner(result), 'score': str(fuzz.partial_ratio(urlCleaner(result), company)), 'source': source})

def selector(company, f):
	r = f(company)
	if r != None:
		return output(company, r)
	return ({'company': company, 'domain': None, 'score': 0})

def argCleaner(company): ## refactor to regex
	for char in company:
		if (char == '['):
			company = company.replace('[','')
		if (char == ']'):
			company = company.replace(']','')
		if (char == ','):
			company = company.replace(',','')
		if (char == '\''):
			company = company.replace('\'','')	
	# if (' ' in company):
	# 	company = company.replace(' ','')
	if ('/' in company):
		company = company.replace('/', '')
		
	return str.lower(company)

def urlCleaner(url):
	if ('www.' in url):
		url = (url.replace('www.', ''))
	sep = '.'
	url = url.split(sep, 1)[0]
	return http_cleaner(str.lower(url))

def http_cleaner(url):
	if ('https://' in url):
		modURL = url.replace('https://','').split('/')
		return (modURL[0])
	if ('http://' in url):
		modURL = url.replace('http://','').split('/')
		return (modURL[0])
	return url

def company_scrub(company):
	search_term = str.lower(company).split(' ')

	print ('search term: ' + str(search_term), company)

	for word in search_term: 
		if word in suffixes.suffixes:
			search_term.remove(word)

	companyScrubbed = ' '.join(search_term)

	return (companyScrubbed)

#################################
### Endpoints
#################################

class Old(Resource):
    def get(self, company):
    	try:
    		return selector(argCleaner(company), autocompleteOld)
    	except: 
    		return

class New(Resource):
    def get(self, company):
    	return selector(argCleaner(company), autocompleteNew)

class Fuzzy(Resource):
    def get(self, company):	
    	return selector(argCleaner(company), autocompleteFuzzy)

class All(Resource):
    def get(self, company):
    	cleanedCompany = argCleaner(company)
    	r = autocompleteOld(cleanedCompany)
    	if r != None:
    		return output(cleanedCompany, r, 'old')
    	r = autocomplete_fuzzy_cog(cleanedCompany)
    	if r != None:
    		return output(cleanedCompany, r, 'fuzzy')
    	r = autocompleteNew(cleanedCompany)
    	if r != None:
    		return output(cleanedCompany, r, 'new')
    	return  ({'company': company, 'domain': None})

class Clearbit(Resource):
	def get(self, company):
		cleanedCompany = argCleaner(company)
		r = autocompleteNew(cleanedCompany)
		if r != None:
			return output(cleanedCompany, r)
		r = autocompleteOld(cleanedCompany)
		if r != None:
			return output(cleanedCompany, r)
		return  ({'domain': None})

class Cognitive(Resource):
	def get(self, company):
		return selector(argCleaner(company), autocomplete_fuzzy_cog)

api.add_resource(Old, '/domainlookup/old/<string:company>')
api.add_resource(New, '/domainlookup/new/<string:company>')
api.add_resource(Fuzzy, '/domainlookup/fuzzy/<string:company>')
api.add_resource(All, '/domainlookup/all/<string:company>')
api.add_resource(Clearbit, '/domainlookup/clearbit/<string:company>')
api.add_resource(Cognitive, '/domainlookup/cognitive/<string:company>')

port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port, debug=True)

#################################
### TO DO
#################################

### Refactor 
### Clean domain prefixes
### Build feature to detect if fuzzy matches are in Clearbit database
### Use fuzzy matching score on old and new endpoints 