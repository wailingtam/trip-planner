# -*- coding: utf-8 -*-
"""
File: AgentFlights

Created on 07/02/2014 9:00 

@author: bejar

"""

__author__ = 'bejar'

from rdflib import Namespace, URIRef, Graph, ConjunctiveGraph
from AgentUtil.OntoNamespaces import TIO, GEO
import time
import gzip

g = Graph()
print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

ontofile = gzip.open('../FlightData/FlightRoutes.ttl.gz')
g.parse(ontofile, format='turtle')

print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
qres = g.query(
    """
    prefix tio:<http://purl.org/tio/ns#>
    prefix geo:<http://www.w3.org/2003/01/geo/wgs84_pos#>
    prefix dbp:<http://dbpedia.org/ontology/>

    Select ?f
    where {
        ?f rdf:type dbp:Airport .
        ?f geo:lat ?lat .
        ?f geo:long ?lon .
        Filter ( ?lat < "41.7"^^xsd:float &&
                 ?lat > "41.0"^^xsd:float &&
                 ?lon < "2.3"^^xsd:float &&
                 ?lon > "2.0"^^xsd:float)
        }
    LIMIT 30
    """,
   initNs= dict(tio=TIO))

print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

for r in qres:
    ap = r['f']

airquery = """
    prefix tio:<http://purl.org/tio/ns#>
    Select *
    where {
        ?f rdf:type tio:Flight.
        ?f tio:to <%s>.
        ?f tio:from ?t.
        ?f tio:operatedBy ?o.
        }
    """ % ap

print airquery

qres = g.query(airquery, initNs=dict(tio=TIO))
print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

for row in qres.result:
    print row
