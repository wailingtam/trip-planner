# -*- coding: utf-8 -*-
"""
File: SimpleAgent

Created on 30/01/2014 11:32

Agente Simple que llama al agente de registro, envia al agente de registro
el mensaje para que pare y acaba su ejecucion

@author: bejar

"""

__author__ = 'bejar'

from  multiprocessing import Process
import socket

from flask import Flask, render_template, request, url_for
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import FOAF, RDF
import requests

from OntoNamespaces import ACL, OWLSProfile, OWLSService
from AgentUtil import shutdown_server
from ACLMessages import build_message



# Configuration stuff
hostname = socket.gethostname()
port = 9001

# Flask stuff
app = Flask(__name__)

# Configuration constants and variables
agn = Namespace("http://www.agentes.org#")
mss_cnt = 0
agentname = 'Agente1'
servuri = agn.Agente1
ra_address = "http://" + hostname + ":9000/Register"
ra_stop = 'http://' + hostname + ':9000/Stop'
self_stop = 'http://' + hostname + ':9001/Stop'

dsgraph = Graph() # Global dsgraph triplestore


def register_message(gmess):
    """
    Envia un mensaje como una performativa FIPA acl

    :param gmess:
    :return:
    """
    global mss_cnt

    servuriprof = URIRef('http://agentes.com/agente1profile')
    gmess.bind('owlsp', OWLSProfile)
    gmess.bind('owlss', OWLSService)
    gmess.add((servuri, RDF.type, OWLSService.Service))
    gmess.add((servuriprof, RDF.type, OWLSProfile.Profile))
    gmess.add((servuri, OWLSService.presents, servuriprof))
    gmess.add((servuri, OWLSProfile.serviceName, Literal(agentname)))
    gmess.bind('foaf', FOAF)

    gmess.add((servuri, FOAF.name, Literal(agentname)))

    gr = build_message(gmess, perf= ACL.request, address=ra_address, sender= servuri)
    mss_cnt += 1

    return gr


@app.route("/iface", methods=['GET','POST'])
def browser_iface():
    """
    Permite la comunicacion con el agente via un navegador
    via un formulario
    """
    if request.method == 'GET':
        return render_template('iface.html')
    else:
        user = request.form['username']
        mess = request.form['message']
        return render_template('riface.html', user= user, mess= mess)

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
    #dsgraph.close()


def agentbehavior1():
    """
    Un comportamiento del agente

    :return:
    """
    gr = register_message(Graph())

    print gr.serialize(format='turtle')

    # r = requests.get(ra_stop)
    # print r.text

    # Seldestruct
    requests.get(self_stop)



if __name__ == '__main__':
    # Ponemos en marcha los behaviors
    ab1=Process(target=agentbehavior1)
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=port)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print 'The End'
