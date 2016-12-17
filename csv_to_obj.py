import csv
import requests

companyDict = {}
with open('companies.csv', 'r') as file:
	companies = csv.reader(file, delimiter=' ', quotechar='|')
	for company in companies:
		c = str(company)
		companyDict[c] = c
	print(len(companyDict))

def test():
	count = 0
	for company in companyDict:
		try: 
			url = 'http://127.0.0.1:5000/domainlookup/all/'+company
			r = requests.get(url)
			result = r.json()
			print (result)
			if (result['domain'] != None):
				count = count + 1
		except: 
			continue
	print (count)

test()


		