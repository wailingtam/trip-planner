# -*- coding: utf-8 -*-
"""
File: MultiprocessingTest

Created on 11/02/2014 8:46 

@author: bejar

"""

__author__ = 'bejar'

from multiprocessing import Process, Manager
from rdflib import Graph, URIRef, Namespace
import time

def thread1(nspace):
    graph = nspace.graph
    ns = Namespace('http://ms.org/')

    graph.add((ns.at1,ns.prop,ns.b))
    nspace.graph = graph
    time.sleep(2)


def thread2(nspace):
    graph = nspace.graph

    ns = Namespace('http://ms.org/')

    graph.add((ns.at2,ns.prop,ns.c))
    nspace.graph = graph
    time.sleep(2)



if __name__ == '__main__':
    ns = Namespace('http://ms.org/')
    manager = Manager()
    graphman = manager.Namespace()

    graphman.graph = Graph()

    ab1=Process(target=thread1,args=(graphman,))
    ab1.start()
    graph = graphman.graph
    graph.add((ns.ap1,ns.prop,ns.g))
    graphman.graph = graph

    ab2=Process(target=thread2,args=(graphman,))
    ab2.start()
    time.sleep(2)
    ab2.join()
    graph = graphman.graph
    graph.add((ns.ap2,ns.prop,ns.i))
    graphman.graph = graph


    ab1.join()

    graph = graphman.graph
    graph.add((ns.ap3,ns.prop,ns.e))
    graphman.graph = graph

    time.sleep(2)
    for a,b,c in graphman.graph.triples((None,None,None)):
        print a,b,c




