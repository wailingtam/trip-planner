# -*- coding: utf-8 -*-
"""
Created on Thu Dec 26 10:47:57 2013

@author: javier
"""


import rdflib
#import rdfextras
from rdflib import OWL
import pprint
from rdflib import plugin
from rdflib import Namespace, BNode, Literal, URIRef
from rdflib.graph import Graph, ConjunctiveGraph
from rdflib.plugins.memory import IOMemory
from  multiprocessing import Process
from flask import Flask,request
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"
    
    
@app.route("/agent1", methods=['GET', 'POST'])
def agent1():
    if request.method == 'GET':
        a= g.serialize(format='xml')
        return a
    else:
        message= request.args['content']
        gm = Graph()
        gm.parse(data=message)
        print gm.serialize(format='n3')
        a= gjohn.serialize(format='xml')
        return a

def webservices():
    app.run()
    
def mainloop():
    while True:
        pass
    

if __name__ == "__main__":
    
    ns = Namespace("http://love.com#")
    
    mary = URIRef("http://love.com/lovers/mary#")
    john = URIRef("http://love.com/lovers/john#")
    
    cmary=URIRef("http://love.com/lovers/mary#")
    cjohn=URIRef("http://love.com/lovers/john#")
    
    store = IOMemory()
    
    g = ConjunctiveGraph(store=store)
    g.bind("loves",ns)
    
    gmary = Graph(store=store, identifier=cmary)
    
    gmary.add((mary, ns['hasName'], Literal("Mary")))
    gmary.add((mary, ns['loves'], john))
    
    gjohn = Graph(store=store, identifier=cjohn)
    gjohn.add((john, ns['hasName'], Literal("John")))
    
    
    p1=Process(target=webservices)
    p2=Process(target=mainloop)
    p1.start()
    p2.start()