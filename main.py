#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import csv

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api.labs import taskqueue
from google.appengine.api import urlfetch
from django.utils import simplejson

import models
import helpers


class MainHandler(webapp.RequestHandler):
	def get(self):
		self.response.out.write("nothing to see here")


class FlatPlanHandler(webapp.RequestHandler):
	def get(self):
		works = models.Work.all()
		for work in works:
			self.response.out.write(work.artist.name + "<br />")
			self.response.out.write(work.artist.gac_id + "<br />")
			self.response.out.write(work.name + "<br />")
			self.response.out.write(work.gac_id + "<br />")
			self.response.out.write(work.medium + "<br />")
			self.response.out.write(work.dates + "<br />")
			self.response.out.write(work.dimensions + "<br /><br />")
			



class ArtistAlphabetHandler(webapp.RequestHandler):
	def get(self):
		artists = models.Artist.all().order("surname")
		letters = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]
		hasartists = []
		firstletter = ""
		i = 0
		artists = models.Artist.all().order("letter")
		for artist in artists:
			if artist.letter != firstletter:
				hasartists.append(artist.letter)
				firstletter = artist.letter
		self.response.out.write("var ALPHABET = {\n")
		for letter in letters:
			self.response.out.write("\""+ letter +"\": ")
			if letter in hasartists:
				self.response.out.write("{\"hasartists\": true}")
			else:
				self.response.out.write("{\"hasartists\": false}")
			i += 1
			if i < len(letters):
				self.response.out.write(",\n")
		self.response.out.write("\n};")


class WorkListHandler(webapp.RequestHandler):
	def get(self):
		works = models.Work.all().order("sortyear")
		firstcentury = 0
		firstdecade = 0
		for work in works:
			if work.century != firstcentury:
				if firstcentury != 0:
					self.response.out.write("]\n},\n")
				self.response.out.write("\"" + str(work.century) + "\": \n{\n")
				firstcentury = work.century
			if work.decade != firstdecade:
				if firstdecade != 0 and work.decade != firstcentury:
					self.response.out.write("],\n")
				self.response.out.write("\"" + str(work.decade) + "\": [")
				firstdecade = work.decade
			else:
				self.response.out.write(",")
			self.response.out.write(work.gac_id)
		self.response.out.write("]\n}")



class ArtistDataHandler(webapp.RequestHandler):
	def get(self):
		artists = models.Artist.all().order("surname")
		firstletter = ""
		artistdict = {}
		artistarray = []
		for artist in artists:
			if artist.letter != firstletter:
				if len(firstletter) > 0:
					artistdict[firstletter] = artistarray
				artistarray = []
				firstletter = artist.letter
			artistarray.append({
				"name":artist.name,
				"dates": "1895-1945",
				"gac_id":artist.gac_id
			})
		artistdict[firstletter] = artistarray
		self.response.out.write(simplejson.dumps(artistdict))



class ArtistListHandler(webapp.RequestHandler):
	def get(self):
		artists = models.Artist.all()
		for artist in artists:
			self.response.out.write(artist.name + ",")
			self.response.out.write(artist.gac_id + ",")
			if artist.wikipedia_url:
				self.response.out.write(artist.wikipedia_url + "\n")
			else:
				self.response.out.write("\n")
			



class CheckWikipediaArtistHandler(webapp.RequestHandler):
	def get(self):
		artists = models.Artist.all().filter("wikipedia_tested =", False).fetch(20)
		for artist in artists:
			try:
				url = "http://en.wikipedia.org/wiki/Special:Search?search=%s&go=Go" % artist.name.replace(" ", "+")
				result = urlfetch.fetch(url, follow_redirects=False)
				self.response.out.write(artist.name + " / " )
				if result.status_code == 200:
					self.response.out.write("searchpage<br />" )
					artist.wikipedia_tested = True
					artist.onwikipedia = False
				else:
					self.response.out.write(str(result.status_code) + "<br />" )
					self.response.out.write(str(result.headers["location"]) + "<br />")
					artist.wikipedia_tested = True
					artist.onwikipedia = True
					artist.wikipedia_url = result.headers["location"]
					artist.wikipedia_scraped = False
				artist.put()
			except:
				problems = True
		if artists:
			taskqueue.add(url="/scrape/wikipediaartists", method="GET")



class CheckTargetArtistsHandler(webapp.RequestHandler):
	def get(self):
		listartists = csv.reader(open('artists.csv'), delimiter=',', quotechar='\"')
		i = 0
		n = 0
		for listartist in listartists:
			if i < 2000:
				try:
					listartistname = listartist[0].strip() +" "+ listartist[1].strip()
				except:
					listartistname = listartist[0].strip() 
				try:
					artist = models.Artist.all().filter("name =", listartistname).get()
					if not artist:
						notfound = True
						#self.response.out.write(" - not there")
					else:
						artist.onhitlist = True
						artist.put()
						self.response.out.write(listartistname)
						works = models.Work.all().filter("artist =", artist)
						j = 0
						for work in works:
							j += 1
						n += j
						self.response.out.write(" - found ("+ str(j) +") works")
						self.response.out.write("<br />")
				except:
					issues = True
					#self.response.out.write(" - issues")
			i += 1
		self.response.out.write("<br />")
		self.response.out.write(str(n) + " works from artists on list in GAC highlights")



class ScrapeHighlightsHandler(webapp.RequestHandler):
	def get(self, page):
		url = "http://www.gac.culture.gov.uk/search/ObjectSearch.asp?title=&name=&lowdate=0&highdate=0&undated=off&mandm=&group=1279111&order=1&listtype=thumbnail&page=" + page
		results = helpers.get_highlights(url)
		j = 0
		i = 0
		for row in results:
			rowtype = ""
			increment = False
			if "Artist.asp?maker_id=" in str(row):
				j = 0
				work = {}
			if j == 0:
				work["maker_gac_id"] = row["a"]["href"].replace("Artist.asp?maker_id=", "")
				work["maker_name"] = row["a"]["content"].replace("\n", "").replace("                          ", " ").replace("                        ", " ")
				increment = True
			if j == 1 and "COLOR: #" in str(row):
				rowtype = "multiple_artists"
				work["multiple_artists"] = True
			elif j == 1 and "COLOR: #" not in str(row):
				work["multiple_artists"] = False
				work["name"] = row["a"]["content"].replace("\n", "").replace("                                ", " ")				
				increment = True
			if j == 2:
				rowtype = "null"
				increment = True
			if j == 3:
				rowtype = "dates"
				work["dates"] = row["p"].replace("\n", "")
				increment = True
			if j == 4:
				rowtype = "medium"
				work["medium"] = row["p"].replace("\n", "").replace("                        ", " ")
				increment = True
			if j == 5:
				rowtype = "dimensions"
				work["dimensions"] = row["p"].replace("\n", "").replace("                          ", " ")
				increment = True
			if j == 6:
				rowtype = "gac_id"
				increment = True
				work["gac_id"] = row["a"]["href"].replace("Object.asp?object_key=", "")
				self.response.out.write(work)
				self.response.out.write("<br />")
				self.response.out.write("<br />")
				artist = models.Artist.get_or_insert(work["maker_gac_id"], gac_id=work["maker_gac_id"], name=work["maker_name"])
				if not artist.letter:
					if "unknown" in artist.name:
						surname = "unknown"
					else:
						if "(" in artist.name:
							name = artist.name.split("(")[0]
						else:
							name = artist.name.strip() 
						nameelements = name.split(" ")
						surname = nameelements[len(nameelements) - 1]
						if len(surname) == 0:
							surname = nameelements[len(nameelements) - 2]
					letter = surname[0].upper()
					artist.surname = surname
					artist.letter = letter
					artist.put()
				rawdates = work["dates"]
				rawdates = rawdates.replace("c.", "").replace("s", "").replace(" (?)", "").replace("?", "")
				if " " in rawdates:
					dateelements = rawdates.split(" ")
					date = dateelements[len(dateelements) - 1]
				else:
					if "-" in rawdates:
						date = rawdates.split("-")[0]
					elif "/" in rawdates:
						date = rawdates.split("/")[0]				
					else:
						date = rawdates
					#FUDGE!	
					if "22/9/1845-25/9/1845" in rawdates:
						date = "1845"
				try:		
					thiswork = models.Work.get_or_insert(work["gac_id"], artist=artist, gac_id=work["gac_id"], name=work["name"], medium=work["medium"], dates=work["dates"], dimensions=work["dimensions"], multiple_artists=work["multiple_artists"], sortyear=int(date), decade=int(date[0:3] + "0"), century=int(date[0:2] + "00"))
					if not work["gac_id"] in artist.worklist:
						artist.worklist.append(work["gac_id"])
						artist.put()
				except:
					self.response.out.write(str(work) + "<br/>")
			i += 1
			if increment:
				j += 1
			if i == 10:
				taskqueue.add(url="/scrape/highlights/"+ str(int(page) + 1), method="GET")



class ScrapeFeaturedHandler(webapp.RequestHandler):
	def get(self, page):
		features = csv.reader(open('featured.csv'), delimiter=',', quotechar='\"')
		i = 0
		for url in features:
			i += 1
			if i == int(page):
				self.response.out.write(url[0] + "<br />")
				results = helpers.get_featured(url[0])
				ps = results["p"]
				for line in ps:
					try:	
						linetext = line.replace("\n", " ").replace("  ", "").strip()
						if len(linetext) > 0:
							self.response.out.write(linetext + "<br />")
					except:
						self.response.out.write("couldn't decode <br />")
				try:
					links = results["a"]
					self.response.out.write(str(links) + "<br />")
				except:
					links = False



class CleanArtistsHandler(webapp.RequestHandler):
	def get(self):
		artists = models.Artist.all()
		for artist in artists:
			name = ""
			surname = ""
			if "unknown" in artist.name:
				surname = "unknown"
			else:
				if "(" in artist.name:
					name = artist.name.split("(")[0]
				else:
					name = artist.name.strip() 
				nameelements = name.split(" ")
				surname = nameelements[len(nameelements) - 1]
				if len(surname) == 0:
					surname = nameelements[len(nameelements) - 2]
			letter = surname[0].upper()
			artist.surname = surname
			artist.letter = letter
			artist.put()
			self.response.out.write(letter.upper() + " <b>" + surname + "</b> [" + name + "]<br />")


def main():
    application = webapp.WSGIApplication([
		('/', MainHandler),
		('/check/artists', CheckTargetArtistsHandler),
		('/clean/artists', CleanArtistsHandler),
		('/list/artists', ArtistListHandler),
		('/scrape/highlights/(.*)', ScrapeHighlightsHandler),
		('/scrape/featured/(.*)', ScrapeFeaturedHandler),
		('/scrape/wikipediaartists', CheckWikipediaArtistHandler),
		('/make/flatplan', FlatPlanHandler),
		('/make/artistlist', ArtistDataHandler),
		('/make/artistalphabet', ArtistAlphabetHandler),
		('/make/worklist', WorkListHandler),

	], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
