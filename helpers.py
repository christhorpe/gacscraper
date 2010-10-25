import os

from google.appengine.ext.webapp import template

import yql


def do_yql(query):
	y = yql.Public()
	result = y.execute(query)
	return result


def render_template(self, end_point, template_values):
	path = os.path.join(os.path.dirname(__file__), "templates/" + end_point)
	response = template.render(path, template_values)
	self.response.out.write(response)


def get_highlights(url):
	query = "select a, p from html where url=\"%s\" and xpath=\"//table[@id='resultsarea']//td[@valign='baseline']\"" % url
	results = do_yql(query)['query']['results']['td']
	return results


def get_featured(url):
	query = "select p, alt, src, content from html where url = \"%s\" and (xpath=\"//table/tbody//img[@src!='images/transparent.gif\']\" or xpath=\"//table/tbody//td[@class='detail']/p\" or xpath=\"//table/tbody//td[@class='detail']/a\")" % url
	results = do_yql(query)['query']['results']
	return results

