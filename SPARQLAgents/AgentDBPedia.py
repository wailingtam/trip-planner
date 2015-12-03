# -*- coding: utf-8 -*-
"""
File: SPARQLQueries

Created on 01/02/2014 11:32

Programa python para enviar queries SPARQL


@author: bejar

"""
__author__ = 'javier'

from SPARQLWrapper import SPARQLWrapper, JSON

from SPARQLPoints import DBPEDIA


sparql = SPARQLWrapper(DBPEDIA)


sparql.setQuery("""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT  DISTINCT *
    WHERE { <http://dbpedia.org/resource/American_Airlines> ?prop ?val.
          }
    LIMIT 1000
""")

sparql.setReturnFormat(JSON)
results = sparql.query()
results.print_results()

# Wikipedia Airlines
# sparql.setQuery("""
#     PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
#     PREFIX foaf: <http://xmlns.com/foaf/0.1/>
#     PREFIX dbpedia2: <http://dbpedia.org/property/>
#     SELECT  DISTINCT *
#     WHERE { ?subject rdf:type <http://dbpedia.org/ontology/Airline>.
#             ?subject <http://dbpedia.org/property/iata> ?IATA.
#             ?subject <http://dbpedia.org/property/icao> ?ICAO.
#             ?subject <http://dbpedia.org/property/airline> ?name.
#             ?subject <http://dbpedia.org/property/callsign> ?cs
#             FILTER (lang(?name) = "en" or lang(?name) = "" )
#           }
# """)

# Wikipedia Airports
# sparql.setQuery("""
#     PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
#     PREFIX dbpedia2: <http://dbpedia.org/property/>
#     SELECT  DISTINCT *
#     WHERE { ?subject rdf:type <http://dbpedia.org/ontology/Airport>.
#             ?subject <http://dbpedia.org/ontology/iataLocationIdentifier> ?IATA.
#             ?subject <http://dbpedia.org/property/cityServed> ?city.
#             ?subject <http://dbpedia.org/property/name> ?name.
#             ?subject <http://www.w3.org/2003/01/geo/wgs84_pos#long> ?long.
#             ?subject <http://www.w3.org/2003/01/geo/wgs84_pos#lat> ?lat.
#             FILTER (lang(?name) = "en" or lang(?name) = "" )
#           }
# """)