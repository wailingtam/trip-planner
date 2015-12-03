# -*- coding: utf-8 -*-
"""
File: AgentFlights

Created on 07/02/2014 9:00 

@author: bejar

"""

__author__ = 'bejar'

from rdflib import Namespace, URIRef, Graph, ConjunctiveGraph
from OntoNamespaces import TIO, GEO
import time
import gzip


from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, SKOS
from rdflib.plugins.stores import sparqlstore

#Define the Stardog store
endpoint = 'http://localhost:5820/flights/query/'

store = sparqlstore.SPARQLUpdateStore(postAsEncoded=False)
store.open((endpoint, endpoint))
ng = Graph(store)

rq = """
SELECT ?f
WHERE {?f rdf:type <http://dbpedia.org/ontology/Airport> .}"""

DBP = Namespace("http://dbpedia.org/ontology/")
for s in ng.query(rq):
    print s.n3()



# print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
#
# for r in qres:
#     ap = r['f']
#
# airquery = """
#     prefix tio:<http://purl.org/tio/ns#>
#     Select *
#     where {
#         ?f rdf:type tio:Flight.
#         ?f tio:to <%s>.
#         ?f tio:from ?t.
#         ?f tio:operatedBy ?o.
#         }
#     """ % ap
#
# print airquery
#
# qres = g.query(airquery, initNs=dict(tio=TIO))
# print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
#
# for row in qres.result:
#     print row
