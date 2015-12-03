# -*- coding: utf-8 -*-
"""
Created on Fri Dec 27 15:58:13 2013

@author: javier
"""

from multiprocessing import Process
import requests
from rdflib import Namespace, URIRef, Graph, ConjunctiveGraph
from rdflib.plugins.memory import IOMemory
import urllib

#r=requests.get('http://api.hotelsbase.org/search.php?longitude=-3.42&latitude=40.28')
#print r.text
#
g = Graph()
store = IOMemory()
ns = Namespace("http://love.com#")

mary = URIRef("http://love.com/lovers/mary#")
john = URIRef("http://love.com/lovers/john#")

g = ConjunctiveGraph(store=store)
g.bind("loves",ns)
g.add((mary, ns['loves'], john))



#
#g.parse(data=r, format="xml")
#
import pprint
#for stmt in g:
#    pprint.pprint(stmt)

rdfm = g.serialize(format='xml')

r=requests.post('http://127.0.0.1:5000/agent1',params={'content':rdfm})
print r.text

# g=rdflib.Graph()
# g.parse(data=r.text, format="xml")
#
# print g.serialize(format='n3')

