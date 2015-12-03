# -*- coding: utf-8 -*-
"""
Created on Fri Dec 27 15:58:13 2013

Agente que realiza peticiones

Demo de agente que utiliza las performativas FIPA para comunicación entre agentes
Las performativas estan definidas en la ontologia fipa-acl.owl

@author: javier
"""

__author__ = 'javier'

import requests
from  multiprocessing import Process, Queue
import multiprocessing
from rdflib import Namespace, URIRef, Graph, ConjunctiveGraph, Literal
from rdflib.namespace import FOAF, RDF
from OntoNamespaces import ACL
from flask import Flask, render_template, request, url_for
import socket
from AgentUtil import shutdown_server


# Configuration stuff
hostname = socket.gethostname()
port = 9010

agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente
agentname = 'AgenteAsk'
agn_uri = agn.AgenteAsk
agn_addr = 'http://' + hostname + ':'+str(port)+'/comm'
self_stop = 'http://' + hostname + ':'+str(port)+'/Stop'

# Directory agent address
rq_address = "http://" + hostname + ":9011/comm"
rq_uri = agn.AgentRespond


# Global triplestore graph
manager = multiprocessing.Manager()
shared_store = manager.Namespace()
shared_store.dsgraph = Graph()

cola1 = Queue()

# Flask stuff
app = Flask(__name__)

@app.route("/comm")
def comunicacion():
    """
    Entrypoint de comunicacion
    """
    global shared_store
    global mss_cnt

    graph = shared_store.dsgraph
    g = Graph()
    ns = Namespace('zz/')
    g.add((ns['a'+str(mss_cnt)],ns['a'+str(mss_cnt)],ns['a'+str(mss_cnt)]))
    graph += g

    shared_store.dsgraph = graph
    mss_cnt += 1
    return 'ok'


@app.route("/Stop")
def stop():
    """
    Entrypoint que para el agente

    :return:
    """
    tidyup()
    shutdown_server()
    return "Parando Servidor"


def tidyup():
    """
    Acciones previas a parar el agente

    """
    pass

def agentbehavior1(shared):
    """
    Un comportamiento del agente

    :return:
    """
    ns = Namespace('aa/')
    i = 0
    while True:
        graph = shared.dsgraph
        if len(graph) > i:
            graph.add((ns['a'+str(i)],ns['a'+str(i)],ns['a'+str(i)]))
            shared.dsgraph = graph
            print(len(graph))
            i += 2


if __name__ == '__main__':
    # Ponemos en marcha los behaviors
    ab1=Process(target=agentbehavior1,args=(shared_store,))
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=port)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print 'The End'


