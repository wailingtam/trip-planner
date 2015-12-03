__author__ = 'javier'

import foursquare
from APIKeys import FQCLIENT_ID, FQCLIENT_SECRET

CLIENT_ID = FQCLIENT_ID
CLIENT_SECRET = FQCLIENT_SECRET

client = foursquare.Foursquare(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)



v = client.venues.search(params={'ll': '41.4,2.14','intent':'browse','radius':'4000','query':'museo'})
#v = client.venues('522a3fa411d2dbee969a35d3')

print len(v['venues'])

for vn in v['venues']:
    print vn['name'],
    if len(vn['categories']) != 0:
        print vn['categories'][0]['name']

