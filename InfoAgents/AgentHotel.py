# -*- coding: utf-8 -*-
"""
Created on Fri Dec 27 15:58:13 2013

Demo de consulta del servicio de hoteles ean.com

Para poder usarlo hay que registrarse y obtener una clave de desarrollador en  la direccion

https://devsecure.ean.com/member/register

@author: javier
"""

__author__ = 'javier'


import requests
import pprint
from APIKeys import EANCID, EANKEY

EAN_END_POINT = 'http://dev.api.ean.com/ean-services/rs/hotel/v3/list'

# r = requests.get(EAN_END_POINT,
#                  params={'apiKey': KEY, 'cid': CID, 'numberOfResults': 5, 'city': 'Barcelona', 'countryCode': 'es'})
#

r = requests.get(EAN_END_POINT,
                 params={'apiKey': EANKEY, 'cid': EANCID, 'numberOfResults': 5,
                         'latitude': '041.40000', 'longitude': '002.16000',
                         'searchRadius': 2, 'searchRadiusUnit': 'KM',
                         'arrivalDate': '03/01/2015', 'departureDate': '03/05/2015'
                 })

dic = r.json()

for hot in dic['HotelListResponse']['HotelList']['HotelSummary']:
    print hot['name']
