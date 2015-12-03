# -*- coding: utf-8 -*-
"""
filename: AgentHotel

Agent que es registra com a agent de hotels i espera peticions

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

from AgentUtil.APIKeys import EANCID, EANKEY

# Configuration stuff
hostname = "localhost"
port = 9003

# Flask stuff
app = Flask(__name__)

# Configuration constants and variables
agn = Namespace("http://www.agentes.org#")
hotel = Namespace("http://www.package.org/hotels#")
paquet = Namespace("http://www.package.org/paquet#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente
InfoAgent = Agent('AgentHotel',
                  agn.Hotel,
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

city_center_coords = {
    "BCN": {
        'lat': '041.40000',
        'long': '002.16000'
    },
    "MAD": {
        'lat': '040.416788',
        'long': '-003.703791'
    },
    "CDG": {
        'lat': '048.857480',
        'long': '002.351447'
    }
}

def buscar_hotels(destination, departureDate, returnDate, numAdults, numChildren, centric, category, minStars):
    EAN_END_POINT = 'http://dev.api.ean.com/ean-services/rs/hotel/v3/list'
    # Hacemos la peticion GET a la entrada del servicio REST
    # Horteles en coordenadas de Barcelona en un radio de 2Km a la redonda
    # 10 resultados con fecha de llegada 1 de febrero y salida 5 de febrero
    # La fecha esta en formato ingles MM/DD/YYYY
    # No se pueden hacer consultas con mas de un mes de antelacio

    r = requests.get(EAN_END_POINT,
             params={'apiKey': EANKEY, 'cid': EANCID, 'numberOfResults': 50,
                     'latitude': city_center_coords[str(destination)]['lat'], 'longitude': city_center_coords[str(destination)]['long'],
                     'searchRadius': 2, 'searchRadiusUnit': 'KM',
                     'arrivalDate': departureDate, 'departureDate': returnDate,
                     'numberOfAdults': numAdults, 'numberOfChildren': numChildren,
                     'includeSurrounding': not(centric), 'propertyCategory': category,
                     'minStarRating': minStars
                     })

    #Property Category -> 1: hotel  4: vacation rental/condo  5: bed & breakfast

    # Generamos un diccionario python de la respuesta en JSON
    dic = r.json()

    ghot = Graph()

    ghot.bind('hotel', hotel)
    # Imprimimos la informacion del nombre de los hores de los resultados
    for hot in dic['HotelListResponse']['HotelList']['HotelSummary']:

        h = hot['hotelId']
        hot_obj = hotel.id + str(h)

        ghot.add((hot_obj, hotel.subj, hotel.obj))
        ghot.add((hot_obj, hotel.id, Literal(h)))
        ghot.add((hot_obj, hotel.name, Literal(hot['name'])))
        ghot.add((hot_obj, hotel.rating, Literal(hot['hotelRating'], datatype=XSD.float)))
        ghot.add((hot_obj, hotel.total_rate, Literal(hot['RoomRateDetailsList']['RoomRateDetails']['RateInfo']['ChargeableRateInfo']['@total'], datatype=XSD.float)))
        ghot.add((hot_obj, hotel.rate_per_night, Literal(hot['RoomRateDetailsList']['RoomRateDetails']['RateInfo']['ChargeableRateInfo']['@averageRate'], datatype=XSD.float)))
        ghot.add((hot_obj, hotel.currency_code, Literal(hot['RoomRateDetailsList']['RoomRateDetails']['RateInfo']['ChargeableRateInfo']['@currencyCode'])))
        ghot.add((hot_obj, hotel.address, Literal(hot['address1'])))
        ghot.add((hot_obj, hotel.description, Literal(hot['shortDescription'])))
        ghot.add((hot_obj, hotel.proximity, Literal(hot['proximityDistance'], datatype=XSD.float)))

    #print ghot.serialize(format='xml')
    return ghot

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
    gmess.add((reg_obj, DSO.AgentType, DSO.HotelsAgent))

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

            #Extraiem els parametres necessaris per realitzar la busqueda
            paq = paquet["vacances"]

            destination = gm.value(subject= paq, predicate= paquet.desti)
            departureDate = gm.value(subject= paq, predicate= paquet.dep_date)
            returnDate = gm.value(subject= paq, predicate= paquet.ret_date)
            numAdults = gm.value(subject= paq, predicate= paquet.num_adults)
            numChildren = gm.value(subject= paq, predicate= paquet.num_child)
            centric = gm.value(subject= paq, predicate = paquet.centric)
            category = gm.value(subject= paq, predicate = paquet.category)
            minStars = gm.value(subject= paq, predicate = paquet.min_stars)

            gh = buscar_hotels(destination, departureDate, returnDate, numAdults, numChildren, centric, category, minStars)

            # Por ahora simplemente retornamos un Inform-done
            gr = build_message(gh,
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
