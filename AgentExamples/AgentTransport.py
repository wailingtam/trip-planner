# -*- coding: utf-8 -*-
"""
filename: AgentTransport

Agent que es registra com a agent de transport i espera peticions

"""

from  multiprocessing import Process, Queue
import socket

from flask import Flask, render_template, request, url_for
from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import FOAF, RDF, XSD
import requests

from AgentUtil.OntoNamespaces import ACL, DSO
from AgentUtil.AgentUtil import shutdown_server
from AgentUtil.ACLMessages import build_message, send_message, get_message_properties
from AgentUtil.Agent import Agent

import json
from AgentUtil.APIKeys import QPX_API_KEY

# Configuration stuff
hostname = "localhost"
port = 9004

# Flask stuff
app = Flask(__name__)

# Configuration constants and variables
agn = Namespace("http://www.agentes.org#")
viatge = Namespace("http://www.package.org/viatge#")
vol = Namespace("http://www.package.org/vol#")
paquet = Namespace("http://www.package.org/paquet#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente
InfoAgent = Agent('AgentTransport',
                  agn.Transport,
                  'http://%s:%d/comm' % (hostname, port),
                  'http://%s:%d/Stop' % (hostname, port))

# Directory agent address
AgentDirectori = Agent('AgentDirectori',
                       agn.Directori,
                       'http://%s:9000/Register' % hostname,
                       'http://%s:9000/Stop' % hostname)

# Global dsgraph triplestore
dsgraph = Graph()

# Cola de comunicacion entre procesos
cola1 = Queue()

def buscar_transport(gm):

    #Extraiem els parametres necessaris per realitzar la busqueda
    paq = paquet["vacances"]

    origin = gm.value(subject= paq, predicate= paquet.origin)
    desti = gm.value(subject= paq, predicate= paquet.desti)
    dd = gm.value(subject= paq, predicate= paquet.dep_date)
    departureDate = dd[6:] + '-' + dd[:2] + '-' + dd[3:5]
    rd = gm.value(subject= paq, predicate= paquet.ret_date)
    returnDate = rd[6:] + '-' + rd[:2] + '-' + rd[3:5]
    numAdults = gm.value(subject= paq, predicate= paquet.num_adults)
    numChildren = gm.value(subject= paq, predicate= paquet.num_child)
    preferredCabin = gm.value(subject= paq, predicate= paquet.cabin)
    maxPrice = gm.value(subject=paq, predicate= paquet.flight_max_price)

    QPX_END_POINT = 'https://www.googleapis.com/qpxExpress/v1/trips/search'
    headers = {'content-type': 'application/json'}

    #Introduim les dades de la peticio en un diccionari
    peticio = {
        "request": {
            "passengers": {
                "adultCount": int(numAdults),
                "childCount": int(numChildren)
            },
            "slice": [
                {
                    "origin": origin,
                    "destination": desti,
                    "date": departureDate,
                    "maxStops": 0,
                    "preferredCabin": preferredCabin
                },
                {
                    "origin": desti,
                    "destination": origin,
                    "date": returnDate,
                    "maxStops": 0,
                    "preferredCabin": preferredCabin
                }
            ],
            "maxPrice": "EUR"+maxPrice,
            "saleCountry": "ES",
            "solutions": 20
        }
    }

    #PreferredCabin: COACH, PREMIUM_COACH, BUSINESS and FIRST
    r = requests.post(QPX_END_POINT, params={'key': QPX_API_KEY}, data=json.dumps(peticio), headers=headers)

    dic = r.json()

    gtransp = Graph()

    gtransp.bind('viatge', viatge)
    gtransp.bind('vol', vol)

    #Extraiem la informacio d'importancia
    for trip in dic['trips']['tripOption']:
        trip_obj = viatge.id + str([trip['id']])
        gtransp.add((trip_obj, viatge.subj, viatge.obj))
        gtransp.add((trip_obj, viatge.id, Literal(trip['id'])))
        gtransp.add((trip_obj, viatge.price, Literal(trip['saleTotal'][3:], datatype=XSD.float)))

        #Departure flight
        dep_obj = vol.anada_id + str(trip['slice'][0]['segment'][0]['id'])
        gtransp.add((trip_obj, viatge.departure_flight, dep_obj))
        gtransp.add((trip_obj, viatge.dep_id, Literal(trip['slice'][0]['segment'][0]['id'])))
        gtransp.add((dep_obj, vol.dep_subj, vol.obj))
        gtransp.add((dep_obj, vol.carrier,  Literal(trip['slice'][0]['segment'][0]['flight']['carrier'])))
        gtransp.add((dep_obj, vol.number,  Literal(trip['slice'][0]['segment'][0]['flight']['number'])))
        gtransp.add((dep_obj, vol.orig,  Literal(trip['slice'][0]['segment'][0]['leg'][0]['origin'])))
        gtransp.add((dep_obj, vol.dest,  Literal(trip['slice'][0]['segment'][0]['leg'][0]['destination'])))
        gtransp.add((dep_obj, vol.duration_min,  Literal(trip['slice'][0]['segment'][0]['leg'][0]['duration'])))
        gtransp.add((dep_obj, vol.dep_time,  Literal(trip['slice'][0]['segment'][0]['leg'][0]['departureTime'])))
        gtransp.add((dep_obj, vol.arr_time,  Literal(trip['slice'][0]['segment'][0]['leg'][0]['arrivalTime'])))

        #Return flight
        ret_obj = vol.tornada_id + str(trip['slice'][1]['segment'][0]['id'])
        gtransp.add((trip_obj, viatge.return_flight, ret_obj))
        gtransp.add((trip_obj, viatge.ret_id, Literal(trip['slice'][1]['segment'][0]['id'])))
        gtransp.add((ret_obj, vol.ret_subj, vol.obj))
        gtransp.add((ret_obj, vol.carrier,  Literal(trip['slice'][1]['segment'][0]['flight']['carrier'])))
        gtransp.add((ret_obj, vol.number,  Literal(trip['slice'][1]['segment'][0]['flight']['number'])))
        gtransp.add((ret_obj, vol.orig,  Literal(trip['slice'][1]['segment'][0]['leg'][0]['origin'])))
        gtransp.add((ret_obj, vol.dest,  Literal(trip['slice'][1]['segment'][0]['leg'][0]['destination'])))
        gtransp.add((ret_obj, vol.duration_min,  Literal(trip['slice'][1]['segment'][0]['leg'][0]['duration'])))
        gtransp.add((ret_obj, vol.dep_time,  Literal(trip['slice'][1]['segment'][0]['leg'][0]['departureTime'])))
        gtransp.add((ret_obj, vol.arr_time,  Literal(trip['slice'][1]['segment'][0]['leg'][0]['arrivalTime'])))

    #print gtransp.serialize(format='xml')
    return gtransp

def register_message():
    """
    Envia un mensaje de registro al servicio de registro
    usando una performativa Request y una accion Register del
    servicio de directorio

    :param gmess:
    :return:
    """
    global mss_cnt

    gmess = Graph()

    # Construimos el mensaje de registro
    gmess.bind('foaf', FOAF)
    gmess.bind('dso', DSO)
    reg_obj = agn[InfoAgent.name+'-Register']
    gmess.add((reg_obj, RDF.type, DSO.Register))
    gmess.add((reg_obj, DSO.Uri, InfoAgent.uri))
    gmess.add((reg_obj, FOAF.Name, Literal(InfoAgent.name)))
    gmess.add((reg_obj, DSO.Address, Literal(InfoAgent.address)))
    gmess.add((reg_obj, DSO.AgentType, DSO.TransportAgent))

    # Lo metemos en un envoltorio FIPA-ACL y lo enviamos
    gr = send_message(
            build_message(gmess, perf= ACL.request,
                      sender= InfoAgent.uri,
                      receiver= AgentDirectori.uri,
                      content= reg_obj,
                      msgcnt= mss_cnt),
            AgentDirectori.address)
    mss_cnt += 1

    return gr

@app.route("/iface", methods=['GET','POST'])
def browser_iface():
    """
    Permite la comunicacion con el agente via un navegador
    via un formulario
    """
    return 'Nothing to see here'

@app.route("/Stop")
def stop():
    """
    Entrypoint que para el agente

    :return:
    """
    tidyup()
    shutdown_server()
    return "Parando Servidor"


@app.route("/comm")
def comunicacion():
    """
    Entrypoint de comunicacion del agente
    Simplementet retorna un objeto fijo que representa una
    respuesta a una busqueda de hotel

    Asumimos que se reciben siempre acciones que se refieren a lo que puede hacer
    el agente (buscar con ciertas restricciones, reservar)
    Las acciones se mandan siempre con un Request
    Prodriamos resolver las busquedas usando una performativa de Query-ref
    """
    global dsgraph
    global mss_cnt

    #Extraemos el mensaje y creamos un grafo con el
    message= request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)

    # Comprobamos que sea un mensaje FIPA ACL
    if msgdic is None:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = build_message(Graph(), ACL['not-understood'], sender=InfoAgent.uri, msgcnt=mss_cnt)
    else:
        # Obtenemos la performativa
        perf = msgdic['performative']

        if perf != ACL.request:
            # Si no es un request, respondemos que no hemos entendido el mensaje
            gr = build_message(Graph(), ACL['not-understood'], sender=InfoAgent.uri, msgcnt=mss_cnt)
        else:
            #Extraemos el objeto del contenido que ha de ser una accion de la ontologia de acciones del agente
            # de registro

            # Averiguamos el tipo de la accion
            if 'content' in msgdic:
                content = msgdic['content']
                accion = gm.value(subject=content, predicate= RDF.type)

            # Aqui realizariamos lo que pide la accion

            gt = buscar_transport(gm)
            # Por ahora simplemente retornamos un Inform-done
            gr = build_message(gt,
                               ACL['inform-done'],
                               sender=InfoAgent.uri,
                               msgcnt=mss_cnt,
                               receiver=msgdic['sender'],)
    mss_cnt += 1
    return gr.serialize(format='xml')


def tidyup():
    """
    Acciones previas a parar el agente

    """
    global cola1
    cola1.put(0)


def agentbehavior1(cola):
    """
    Un comportamiento del agente

    :return:
    """
    # Registramos el agente
    gr = register_message()

    # Escuchando la cola hasta que llegue un 0
    fin = False
    while not fin:
        while cola.empty():
            pass
        v = cola.get()
        if v == 0:
            fin = True
        else:
            print v

    # Selfdestruct
    #requests.get(InfoAgent.stop)

if __name__ == '__main__':
    # Ponemos en marcha los behaviors
    ab1=Process(target=agentbehavior1, args=(cola1,))
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=port)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print 'The End'
