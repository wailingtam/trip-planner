# -*- coding: utf-8 -*-
"""
Created on Fri Dec 27 15:58:13 2013

Demo de consulta del servicio del tiempo de openweathermap.org

Para poder usarlo hay que registrarse y obtener una clave de desarrollador en su web

@author: javier
"""

__author__ = 'javier'


import requests
import pprint


WEATHER_END_POINT = 'http://api.openweathermap.org/data/2.5/forecast'


r = requests.get(WEATHER_END_POINT,
                 params={'q':'Barcelona,es', 'units':'metric',
                         'mode':'json', 'cnt': '3'
                   })

dic = r.json()

for d in dic['list']:
    print d