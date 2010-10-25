from google.appengine.ext import db


class Artist(db.Model):
	name = db.StringProperty()
	gac_id = db.StringProperty()
	dates = db.StringProperty()
	biography = db.TextProperty()
	wikipedia_url = db.StringProperty()
	wikipedia_tested = db.BooleanProperty(default=False)
	wikipedia_scraped = db.BooleanProperty(default=False)
	hitlist_tested = db.BooleanProperty(default=False)
	onwikipedia = db.BooleanProperty(default=False)
	onhitlist = db.BooleanProperty(default=False)
	surname = db.StringProperty()
	letter = db.StringProperty()
	worklist = db.StringListProperty()



class Work(db.Model):
	artist = db.ReferenceProperty()
	name = db.StringProperty()
	gac_id = db.StringProperty()
	dates = db.StringProperty()
	medium = db.StringProperty()
	dimensions = db.StringProperty()
	provenance = db.StringProperty()
	description = db.TextProperty()
	featuredwork_tested = db.BooleanProperty(default=False)
	featuredwork = db.BooleanProperty(default=False)
	multiple_artists = db.BooleanProperty(default=False)
	century = db.IntegerProperty()
	decade = db.IntegerProperty()
	sortyear = db.IntegerProperty()
