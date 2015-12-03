# -*- coding: utf-8 -*-
"""
filename: AgentSistema

Ejemplo de agente que busca en el directorio y llamma al agente obtenido
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

import json
import pprint
import datetime

# Configuration stuff
hostname = "localhost"
port = 9001

# Flask stuff
app = Flask(__name__)

# Configuration constants and variables
agn = Namespace("http://www.agentes.org#")
paquet = Namespace("http://www.package.org/paquet#")
hotel = Namespace("http://www.package.org/hotels#")
viatge = Namespace("http://www.package.org/viatge#")
vol = Namespace("http://www.package.org/vol#")
activitat = Namespace("http://www.package.org/activitats#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente
AgentSistema = Agent('AgentSistema',
                       agn.Sistema,
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


def directory_search_message(type):
    """
    Busca en el servicio de registro mandando un
    mensaje de request con una accion Seach del servicio de directorio

    Podria ser mas adecuado mandar un query-ref y una descripcion de registo
    con variables

    :param gmess:
    :return:
    """
    global mss_cnt

    gmess = Graph()

    gmess.bind('foaf', FOAF)
    gmess.bind('dso', DSO)
    reg_obj = agn[AgentSistema.name+'-search']
    gmess.add((reg_obj, RDF.type, DSO.Search))
    gmess.add((reg_obj, DSO.AgentType,type))

    msg = build_message(gmess, perf= ACL.request,
                      sender=AgentSistema.uri,
                      receiver=AgentDirectori.uri,
                      content=reg_obj,
                      msgcnt=mss_cnt)
    gr = send_message(msg,AgentDirectori.address)
    mss_cnt += 1
    return gr


def infoagent_search_message(addr, ragn_uri, gmess):
    """
    Envia una accion a un agente de informacion
    """
    global mss_cnt

    """gmess = Graph()

    # Supuesta ontologia de acciones de agentes de informacion
    IAA = Namespace('IAActions')

    gmess.bind('foaf', FOAF)
    gmess.bind('iaa', IAA)
    reg_obj = agn[AgentSistema.name+'-info-search']
    gmess.add((reg_obj, RDF.type, IAA.Search))"""

    msg = build_message(gmess, perf=ACL.request,
                      sender=AgentSistema.uri,
                      receiver=ragn_uri,
                      msgcnt=mss_cnt)
    gr = send_message(msg, addr)
    mss_cnt += 1
    return gr


def buscar_hotel(gmess):
    """
    Es realitza la peticio d'allotjaments i la seleccio d'una entre les resultants
    """

    # Buscamos en el directorio
    # un agente de hoteles
    gr = directory_search_message(DSO.HotelsAgent)

    # Obtenemos la direccion del agente de la respuesta
    # No hacemos ninguna comprobacion sobre si es un mensaje valido
    msg = gr.value(predicate=RDF.type, object=ACL.FipaAclMessage)
    content = gr.value(subject=msg, predicate=ACL.content)
    ragn_addr = gr.value(subject=content, predicate=DSO.Address)
    ragn_uri = gr.value(subject=content, predicate=DSO.Uri)

    # Ahora mandamos un objeto de tipo request mandando una accion de tipo Search
    # que esta en una supuesta ontologia de acciones de agentes
    grhotel = infoagent_search_message(ragn_addr, ragn_uri, gmess)

    #Eliminem els hotels que havia sortit a una peticio anterior
    f = open('hotelsid.txt', 'r')
    hotels_list = f.read()
    hotels_list = hotels_list[:-1].split(',')
    f.close()

    for h in hotels_list:
        hot_obj = hotel.id + str(h)
        grhotel.remove((hot_obj, None, None))

    paq = paquet["vacances"]
    centric = gmess.value(subject= paq, predicate = paquet.centric)

    #Si l'usuari havia demanat un allotjament centric, es tria per proximitat, sino per puntuacio i preu
    if centric:
        hotel_escollit = grhotel.query("""
                            PREFIX hotel: <http://www.package.org/hotels#>
                            SELECT DISTINCT ?a ?id
                            WHERE {
                                ?a hotel:id ?id .
                                ?a hotel:proximity ?proximity
                            }
                            ORDER BY ASC(?proximity)
                            LIMIT 1
            """
        )
    else:
        hotel_escollit = grhotel.query("""
                            PREFIX hotel: <http://www.package.org/hotels#>
                            SELECT DISTINCT ?a ?id
                            WHERE {
                                ?a hotel:id ?id .
                                ?a hotel:rating ?rating .
                                ?a hotel:total_rate ?total_rate
                            }
                            ORDER BY DESC(?rating) ASC(?total_rate)
                            LIMIT 1
            """
        )

    f = open('hotelsid.txt', 'a')

    hotelid = ""

    for h, id in hotel_escollit:
        hotelid = h
        f.writelines(id+",")

    f.close()

    grhot = Graph()
    grhot.bind('hotel', hotel)

    grhot += grhotel.triples((hotelid, None, None))

    return grhot


def buscar_transport(gmess):
    """
    Es realitza la peticio i la seleccio del transport
    """
    gr = directory_search_message(DSO.TransportAgent)

    msg = gr.value(predicate=RDF.type, object=ACL.FipaAclMessage)
    content = gr.value(subject=msg, predicate=ACL.content)
    ragn_addr = gr.value(subject=content, predicate=DSO.Address)
    ragn_uri = gr.value(subject=content, predicate=DSO.Uri)

    grtransport = infoagent_search_message(ragn_addr, ragn_uri, gmess)
    #print grtransport.serialize(format='xml')

    f = open('flightnumbers.txt', 'r')
    flights_list = f.read()
    flights_list = flights_list[:-1].split(',')
    f.close()

    #Eliminem els viatges que tenen vols d'anada que ja s'havien ofert a l'usuari
    for f in flights_list:
        grt_gen = grtransport.triples((None, viatge.dep_id, Literal(f)))
        for a, b, c in grt_gen:
            grtransport.remove((a, None, None))


    #El transport es tria pel preu mes economic
    transport_escollit = grtransport.query("""
                            PREFIX viatge: <http://www.package.org/viatge#>
                            SELECT DISTINCT ?a ?dep_flight ?ret_flight ?dep_id ?ret_id
                            WHERE {
                                ?a viatge:departure_flight ?dep_flight .
                                ?a viatge:return_flight ?ret_flight .
                                ?a viatge:dep_id ?dep_id .
                                ?a viatge:ret_id ?ret_id .
                                ?a viatge:price ?price
                            }
                            ORDER BY (?price)
                            LIMIT 1
            """
        )

    grtransp = Graph()
    grtransp.bind('viatge', viatge)
    grtransp.bind('vol', vol)

    f = open('flightnumbers.txt', 'a')

    viatgeid = ""
    dfid = ""
    rfid = ""

    for v, df, rf, did, rid in transport_escollit:
        viatgeid = v
        dfid = df
        rfid = rf
        f.writelines(did+",")
    f.close()

    grtransp += grtransport.triples((viatgeid, None, None))
    grtransp += grtransport.triples((dfid, None, None))
    grtransp += grtransport.triples((rfid, None, None))

    return grtransp


def buscar_activitats(gmess):
    """
    Es realitza la peticio d'activitats i les assignacions d'aquestes en els dies del viatge
    """
    gr = directory_search_message(DSO.ActivitatsAgent)

    msg = gr.value(predicate=RDF.type, object=ACL.FipaAclMessage)
    content = gr.value(subject=msg, predicate=ACL.content)
    ragn_addr = gr.value(subject=content, predicate=DSO.Address)
    ragn_uri = gr.value(subject=content, predicate=DSO.Uri)

    gractivitats = infoagent_search_message(ragn_addr, ragn_uri, gmess)

    paq = paquet["vacances"]

    #Calcul dels dies que duren les vacances
    dep_date = gmess.value(subject= paq, predicate= paquet.dep_date)
    ret_date = gmess.value(subject= paq, predicate= paquet.ret_date)
    dep = datetime.datetime.strptime(str(dep_date), "%m/%d/%Y")
    ret = datetime.datetime.strptime(ret_date, "%m/%d/%Y")
    date = ret - dep
    dies = date.days

    #Les activitats s'assignen aleatoriament en les tres franges horaries
    acts_list = gractivitats.triples((None, activitat.name, None))
    i = 0
    dia = 0
    for a, b, c in acts_list:
        if i < (dies*3):
            if i % 3 == 0:
                dia += 1
                gractivitats.add((a, activitat.torn, Literal("mati")))
            elif i % 3 == 1:
                gractivitats.add((a, activitat.torn, Literal("tarda")))
            elif i % 3 == 2:
                gractivitats.add((a, activitat.torn, Literal("nit")))
            gractivitats.add((a, activitat.dia, Literal(str(dia))))
        else:
            gractivitats.remove((a, None, None))
        i += 1

    #print gractivitats.serialize(format='xml')
    return gractivitats


def crear_paquet(gm):
    """
    Es fan les peticions individuals i s'ajunten tots els resultats en un mateix graf
    """
    grpaq = Graph()
    grpaq.bind('hotel', hotel)
    grpaq.bind('viatge', viatge)
    grpaq.bind('vol', vol)
    grpaq.bind('activitat', activitat)

    grh = buscar_hotel(gm)
    grpaq += grh
    grt = buscar_transport(gm)
    grpaq += grt
    gra = buscar_activitats(gm)
    grpaq += gra
    return grpaq


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
        return render_template('riface.html', user=user, mess=mess)


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
        gr = build_message(Graph(), ACL['not-understood'],AgentSistemanfoAgent.uri, msgcnt=mss_cnt)
    else:
        # Obtenemos la performativa
        perf = msgdic['performative']

        if perf != ACL.request:

            # Si no es un request, respondemos que no hemos entendido el mensaje
            gr = build_message(Graph(), ACL['not-understood'],AgentSistemanfoAgent.uri, msgcnt=mss_cnt)
        else:
            #Extraemos el objeto del contenido que ha de ser una accion de la ontologia de acciones del agente
            # de registro
            # Averiguamos el tipo de la accion
            if 'content' in msgdic:
                content = msgdic['content']
                accion = gm.value(subject=content, predicate= RDF.type)

            # Aqui realizariamos lo que pide la accion
            gp = crear_paquet(gm)
            # Por ahora simplemente retornamos un Inform-done
            gr = build_message(gp,
                               ACL['inform-done'],
                               sender=AgentSistema.uri,
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
    #pass
    #dsgraph.close()

def agentbehavior1(cola):
    """
    Un comportamiento del agente

    :return:
    """

    # r = requests.get(ra_stop)
    # print r.text

    # Selfdestruct

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
    requests.get(AgentSistema.stop)

if __name__ == '__main__':
    # Ponemos en marcha los behaviors
    ab1=Process(target=agentbehavior1, args=(cola1,))
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=port)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print 'The End'

