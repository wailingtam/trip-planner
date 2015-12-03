# -*- coding: utf-8 -*-
"""
Created on Fri Dec 27 15:58:13 2013

@author: javier
"""

from multiprocessing import Process
import requests
import rdflib
import urllib

#r=requests.get('http://api.hotelsbase.org/search.php?longitude=-3.42&latitude=40.28')
#print r.text
#
#g=rdflib.Graph()
#
#g.parse(data=r, format="xml")
#
import pprint
#for stmt in g:
#    pprint.pprint(stmt)


#r=requests.post('http://127.0.0.1:5000/agent1')
#
#
#print r.text

#params = { }
#params[ 'key' ] = "AIzaSyDAUWYjXBR-Tu8zhdKdRB7nKAa8pSHv988"
#params[ 'location' ] = "41.2,2.09"
#params = urllib.urlencode( params )
#print "http://maps.googleapis.com/maps/api/geocode/xml?%s" % params
#
#try:
#    f = urllib.urlopen( "https://maps.googleapis.com/maps/api/place/nearbysearch/xml?%s" % params )
#except e:
#    print "Error %d: %s" % (e.args[0],e.args[1])
#print f.read()

from googleplaces import GooglePlaces, types, lang
from APIKeys import GOOGLEAPI_KEY

google_places = GooglePlaces(GOOGLEAPI_KEY)


query_result = google_places.nearby_search(
        location='Barcelona, España',keyword='metro',
        radius=300, types=['bus_station'])

if query_result.has_attributions:
    print query_result.html_attributions


for place in query_result.places:
    # Returned places from a query are place summaries.
    print place.name
    print place.geo_location
    print place.reference

    # The following method has to make a further API call.
    place.get_details()
    # Referencing any of the attributes below, prior to making a call to
    # get_details() will raise a googleplaces.GooglePlacesAttributeError.
    pprint.pprint(place.details) # A dict matching the JSON response from Google.
    print place.local_phone_number
#    print place.international_phone_number
#    print place.website
#    print place.url
