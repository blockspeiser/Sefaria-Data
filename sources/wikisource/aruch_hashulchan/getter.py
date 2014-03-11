# -*- coding: utf-8 -*-

import urllib
import urllib2
import json
import os
import time

def wikiGet(url, name):
	"""
	Takes a url and saves it to ./page/name
	"""

	ls = os.listdir("./pages")
	if name in ls:
		print "Already have %s" % (name)
		return
	print "Getting %s" % (name)
	
	request = urllib2.Request(url)
	request.add_header("User-Agent", "Ari Hebrew book grabber 1.0 ari@elias-bachrach.com") #wikimedia said to do this
	request.add_header("Host", "he.wikisource.org")
	request.add_header("Accept", "text/html,text/json")
	resp = urllib2.urlopen(request)


	#print resp.getCode()
	f = open("./pages/%s" %(name), "w")
	f.write(resp.read())
	f.close()

index = open("nnn", "r")
for line in index:
	line = line.rstrip()
	title = urllib.unquote(line).decode('utf8')
	wikiGet("http://he.wikisource.org/w/api.php?format=json&action=query&prop=revisions&rvprop=content&titles=%s" %(line), title)
	
index.close()


