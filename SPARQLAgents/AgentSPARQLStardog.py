__author__ = 'javier'

from SPARQLWrapper import SPARQLWrapper, JSON, POST

from SPARQLPoints import OPENLINK

endpoint = 'http://localhost:5820/Pruebas2/query/'
#endpoint = 'http://localhost:3030/ds/query'

sparql = SPARQLWrapper(endpoint)

# Museos en un radio de 20Km alrededor de Barcelona
# sparql.setQuery("""
#     prefix tio:<http://purl.org/tio/ns#>
#     prefix geo:<http://www.w3.org/2003/01/geo/wgs84_pos#>
#     prefix dbp:<http://dbpedia.org/ontology/>
#     prefix rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
#     prefix xsd:<http://www.w3.org/2001/XMLSchema#>
#
#     Select ?f
#     where {
#         ?f rdf:type dbp:Airport .
#         ?f geo:lat ?lat .
#         ?f geo:long ?lon .
#         Filter ( ?lat < "41.7"^^xsd:float &&
#                  ?lat > "41.0"^^xsd:float &&
#                  ?lon < "2.3"^^xsd:float &&
#                  ?lon > "2.0"^^xsd:float)
#         }
#     LIMIT 30
# """
# )
#
# sparql.setReturnFormat(JSON)
# results = sparql.query()
# print results.print_results()
#
sparql.setMethod(POST)


q = """
prefix mionto:<http://mionto.org/>

INSERT DATA {
    mionto:servivo rdfs:subClassOf owl:Thing.
}
"""

sparql.setQuery(q)
results = sparql.query()
