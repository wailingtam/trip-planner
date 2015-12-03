# -*- coding: iso-8859-15 -*-
__author__ = 'javier'

from googleplaces import GooglePlaces, types, lang
from APIKeys import GOOGLEAPI_KEY
import pprint


google_places = GooglePlaces(GOOGLEAPI_KEY)

#print google_places.geocode_location('Barcelona, España')
query_result = google_places.nearby_search(
        location=u'Barcelona, España', keyword='metro',
        radius=300, types=['bus_station'])

print query_result
# query_result = google_places.nearby_search(
#         location='Barcelona, España', keyword='metro',
#         radius=300, types=['bus_station'])
#
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

