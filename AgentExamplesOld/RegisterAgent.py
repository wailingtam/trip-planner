# -*- coding: utf-8 -*-
"""
Created on 30/1/2014

Agente que guarda un registro de otros agentes

Guarda los registros como tripletas RDF
Usa OWL-S profile como ontologia

@author: bejar
"""

__author__ = 'bejar'

from  multiprocessing import Process, Queue
import socket

from flask import Flask, request, render_template
from rdflib import Graph, RDF, Namespace, Literal, RDFS
from rdflib.namespace import FOAF

from OntoNamespaces import ACL
from AgentUtil import shutdown_server

# Configuration stuff
hostname = socket.gethostname()
port = 9000

dsgraph = Graph()
dsgraph.bind('acl', ACL)
dsgraph.bind('rdf', RDF)
dsgraph.bind('rdfs', RDFS)
dsgraph.bind('foaf', FOAF)
#dsgraph = Graph('Sleepycat')

# first time create the store:
#dsgraph.open('./myRDFLibStore', create = True)
#dsgraph.close()

sa = ACL.SpeechAct
agn = Namespace("http://www.agentes.org#")
app = Flask(__name__)
mss_cnt = 0

cola1 = Queue() # Cola de comunicacion entre procesos


@app.route("/Register")
def register():
    """
    Entry point del agente que recibe los mensajes de registro

    :return:
    """
    global dsgraph
    global mss_cnt
    #cola1.put('zzz')
    message= request.args['content']
    gm = Graph()
    gr = Graph()
    gr.bind('acl',ACL)
    gm.parse(data=message)
    print gm.serialize(format='turtle')
    perf = gm.triples( (None,  RDF.type, sa)) # Obtenemos la performativa
    if perf is None:
        gr.add((ACL['not-understood'], RDF.type, sa))
    else:
        aresp= gm.subject_objects(FOAF.name)
        a,n = aresp.next()
        print a, n
        ms = ACL['message{:{fill}4d}'.format(mss_cnt, fill='0')]
        mss_cnt += 1
        gr.add((ms, RDF.type, sa))
        gr.add((ms, ACL.performative, ACL.confirm))
        gm.add((agn.juan, FOAF.name, Literal('RegisterAgent')))
        gm.add((ms, ACL.sender, agn.RegisterAgent))
        #dsgraph.open('./myRDFLibStore')
        dsgraph += gm
    return gr.serialize(format='xml')


@app.route('/info')
def info():
    """
    Entrada que da informacion sobre el agente
    """
    global dsgraph
    global mss_cnt

    return render_template('info.html', nmess= mss_cnt, graph= dsgraph.serialize(format='turtle'))


@app.route("/Stop")
def stop():
    """
    Entrada que para el agente
    """
    print 'Parando Servidor'
    tidyup()

    shutdown_server()
    return "Parando Servidor"

def tidyup():
    pass
    #dsgraph.close()

def agentbehavior1(cola):
    fin = False
    while not fin:
        while cola.empty():
            pass
        v = cola.get()
        print v

if __name__ == '__main__':
    # Ponemos en marcha los behaviours como procesos
    ab1=Process(target=agentbehavior1,args=(cola1,))
    ab1.start()

    print hostname
    # Ponemos en marcha el servidor Flask
    app.run(host= hostname, port=port)

    # Cerramos los procesos
    ab1.terminate()

    print 'The End'


