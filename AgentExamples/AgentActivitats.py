# -*- coding: utf-8 -*-
"""
filename: AgentActivitats

Agent que es registra com a agent de activitats i espera peticions

"""

from  multiprocessing import Process, Queue
import socket

from flask import Flask, render_template, request, url_for
from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import FOAF, RDF
import requests

from AgentUtil.OntoNamespaces import ACL, DSO
from AgentUtil.AgentUtil import shutdown_server
from AgentUtil.ACLMessages import build_message, send_message, get_message_properties
from AgentUtil.Agent import Agent

from googleplaces import GooglePlaces, types, lang
from AgentUtil.APIKeys import GOOGLEAPI_KEY

import time

# Configuration stuff
hostname = "localhost"
port = 9002

# Flask stuff
app = Flask(__name__)

# Configuration constants and variables
agn = Namespace("http://www.agentes.org#")
activitat = Namespace("http://www.package.org/activitats#")
paquet = Namespace("http://www.package.org/paquet#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente
InfoAgent = Agent('AgentActivitats',
                  agn.Activitats,
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

locations = {
    'BCN': 'Barcelona, Spain',
    'MAD': 'Madrid, Spain',
    'CDG': 'Paris, France'
}

def buscar_activitats(destination, actTypes):
    google_places = GooglePlaces(GOOGLEAPI_KEY)
    types_list = actTypes.split(",")

    gact = Graph()
    gact.bind('activitat', activitat)

    #Realitzem la peticio d'activitats al servei extern
    query_result = google_places.nearby_search(
            location= locations[str(destination)], keyword='',
            radius=2000, types=types_list)

    #Afegim els resultats en un graf de resposta
    for place in query_result.places:
        act_obj = activitat.id + str(place.place_id)
        # Returned places from a query are place summaries.
        gact.add((act_obj, activitat.name, Literal(place.name)))
        # The following method has to make a further API call.
        place.get_details()
        # Referencing any of the attributes below, prior to making a call to
        # get_details() will raise a googleplaces.GooglePlacesAttributeError.
        gact.add((act_obj, activitat.subj, activitat.obj))
        gact.add((act_obj, activitat.rating, Literal(place.rating)))
        gact.add((act_obj, activitat.address, Literal(place.formatted_address)))
        gact.add((act_obj, activitat.phone, Literal(place.local_phone_number)))
        gact.add((act_obj, activitat.website, Literal(place.website)))

    #Obtenim el pagetoken de la peticio
    pt = query_result.next_page_token

    #Si no es null obtenim els seguents 20 resultats(maxim) de la query anterior
    if (pt is not None):
        #Es fa una parada de 2 segons perque no es pot realitzar una segona query de manera immediata
        time.sleep(2)

        query_result2 = google_places.nearby_search(
                location='Barcelona, Spain', keyword='',
                radius=2000, types=types_list, pagetoken = pt)

        pt = query_result2.next_page_token

        for place in query_result2.places:
            act_obj = activitat.id + str(place.place_id)
            gact.add((act_obj, activitat.name, Literal(place.name)))
            place.get_details()
            gact.add((act_obj, activitat.rating, Literal(place.rating)))
            gact.add((act_obj, activitat.address, Literal(place.formatted_address)))
            gact.add((act_obj, activitat.phone, Literal(place.local_phone_number)))
            gact.add((act_obj, activitat.website, Literal(place.website)))

    #Igual que abans, obtenim mes activitats si existeix una tercera pagina amb resultats
    if (pt is not None):
        #Es fa una parada de 2 segons perque no es pot realitzar una segona query de manera immediata
        time.sleep(2)

        query_result3 = google_places.nearby_search(
                location='Barcelona, Spain', keyword='',
                radius=2000, types=types_list, pagetoken = pt)

        for place in query_result3.places:
            act_obj = activitat.id + str(place.place_id)
            gact.add((act_obj, activitat.name, Literal(place.name)))
            place.get_details()
            gact.add((act_obj, activitat.rating, Literal(place.rating)))
            gact.add((act_obj, activitat.address, Literal(place.formatted_address)))
            gact.add((act_obj, activitat.phone, Literal(place.local_phone_number)))
            gact.add((act_obj, activitat.website, Literal(place.website)))

    return gact



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
    gmess.add((reg_obj, DSO.AgentType, DSO.ActivitatsAgent))

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
            paq = paquet["vacances"]
            actTypes = gm.value(subject= paq, predicate= paquet.act_types)
            destination = gm.value(subject= paq, predicate= paquet.desti)

            ga = buscar_activitats(destination, actTypes)
            # Por ahora simplemente retornamos un Inform-done
            gr = build_message(ga,
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
