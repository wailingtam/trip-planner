# -*- coding: utf-8 -*-
"""
filename: AgentUsuari

Agent que busca en el directori i crida a l'agent obtingut

"""

from  multiprocessing import Process
import socket

from flask import Flask, render_template, request, url_for
from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import FOAF, RDF, XSD
import requests

from AgentUtil.OntoNamespaces import ACL, DSO
from AgentUtil.AgentUtil import shutdown_server
from AgentUtil.ACLMessages import build_message, send_message
from AgentUtil.Agent import Agent

import json
import datetime

# Configuration stuff
hostname = "localhost"
port = 9005

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
AgentUsuari = Agent('AgentUsuari',
                       agn.Usuari,
                       'http://%s:%d/comm' % (hostname, port),
                       'http://%s:%d/Stop' % (hostname, port))

AgentSistema = Agent('AgentSistema',
                       agn.Sistema,
                       'http://%s:%d/comm' % (hostname, 9001),
                       'http://%s:%d/Stop' % (hostname, 9001))

# Global dsgraph triplestore
dsgraph = Graph()


def demanar_paquet (gmess):
    """
    Envia la peticio d'un paquet vacances amb les preferencies de l'usuari
    """
    global mss_cnt
    msg = build_message(gmess, perf=ACL.request,
                      sender=AgentUsuari.uri,
                      receiver=AgentSistema.uri,
                      msgcnt=mss_cnt)
    gr = send_message(msg, AgentSistema.address)
    mss_cnt += 1
    return gr

def processar_paquet(gpaquet, dies):

    """
    A partir del graf que conte tot el contingut del paquet es crea el fitxer que es mostrara a l'usuari
    """
    paq_hotel_gen = gpaquet.subjects(predicate=hotel.subj, object=hotel.obj)
    paq_hotel = ""

    for hid in paq_hotel_gen:
        paq_hotel = hid

    paq_transp_gen = gpaquet.subjects(predicate=viatge.subj, object=viatge.obj)
    paq_viatge = ""

    for vid in paq_transp_gen:
        paq_viatge = vid

    dep_flight_gen = gpaquet.subjects(predicate=vol.dep_subj, object=vol.obj)
    dep_flight = ""

    for df in dep_flight_gen:
        dep_flight = df

    ret_flight_gen = gpaquet.subjects(predicate=vol.ret_subj, object=vol.obj)
    ret_flight = ""

    for rf in ret_flight_gen:
        ret_flight = rf


    currency_code = gpaquet.value(subject= paq_hotel, predicate= hotel.currency_code)


    paquetInfo = {
        "Hotel": {
            "Name": gpaquet.value(subject= paq_hotel, predicate= hotel.name),
            "Description": gpaquet.value(subject= paq_hotel, predicate= hotel.description),
            "Rating": gpaquet.value(subject= paq_hotel, predicate= hotel.rating),
            "Rate per night": gpaquet.value(subject= paq_hotel, predicate= hotel.rate_per_night) + currency_code,
            "Total rate": gpaquet.value(subject= paq_hotel, predicate= hotel.total_rate) + currency_code,
            "Address": gpaquet.value(subject= paq_hotel, predicate= hotel.address),
            "Distance to city center": gpaquet.value(subject= paq_hotel, predicate= hotel.proximity) + "KM"
        },
        "Transport": {
            "Departure flight": {
                "Flight number": gpaquet.value(subject= dep_flight, predicate= vol.number),
                "Carrier": gpaquet.value(subject= dep_flight, predicate= vol.carrier),
                "Origin": gpaquet.value(subject= dep_flight, predicate= vol.orig),
                "Destination": gpaquet.value(subject= dep_flight, predicate= vol.dest),
                "Departure time": gpaquet.value(subject= dep_flight, predicate= vol.dep_time),
                "Arrival time": gpaquet.value(subject= dep_flight, predicate= vol.arr_time),
                "Duration": gpaquet.value(subject= dep_flight, predicate= vol.duration_min) + "min"
            },
            "Return flight": {
                "Flight number": gpaquet.value(subject= ret_flight, predicate= vol.number),
                "Carrier": gpaquet.value(subject= ret_flight, predicate= vol.carrier),
                "Origin": gpaquet.value(subject= ret_flight, predicate= vol.orig),
                "Destination": gpaquet.value(subject= ret_flight, predicate= vol.dest),
                "Departure time": gpaquet.value(subject= ret_flight, predicate= vol.dep_time),
                "Arrival time": gpaquet.value(subject= ret_flight, predicate= vol.arr_time),
                "Duration": gpaquet.value(subject= ret_flight, predicate= vol.duration_min) + "min"
            },
            "Preu total": gpaquet.value(subject= paq_viatge, predicate= viatge.price) + "EUR"
        },
        "Activities": {

        }
    }

    paquet_act = {}

    for day in range(1, dies+1):
        acts_dia = gpaquet.triples((None, activitat.dia, Literal(str(day))))
        paquetet_act = {
            "Dia " + str(day): {}
        }
        for subj, pred, obj in acts_dia:
            paquetetet_act = {
                "Torn " + str(gpaquet.value(subject= subj, predicate= activitat.torn)): {
                    "Name": gpaquet.value(subject= subj, predicate= activitat.name),
                    "Address": gpaquet.value(subject= subj, predicate= activitat.address),
                    "Phone": gpaquet.value(subject= subj, predicate= activitat.phone),
                    "Website": gpaquet.value(subject= subj, predicate= activitat.website),
                    "Rating": gpaquet.value(subject= subj, predicate= activitat.rating)
                }
            }
            paquetet_act['Dia '+str(day)].update(paquetetet_act)
        paquet_act.update(paquetet_act)

    paquetInfo['Activities'].update(paquet_act)

    f = open('paquet.txt', 'w')
    json.dump(paquetInfo, f, indent=4)

    f.close()


@app.route("/", methods=['GET','POST'])
def browser_iface():
    """
    Permite la comunicacion con el agente via un navegador
    via un formulario
    """
    if request.method == 'GET': #False:
        return render_template('iface.html')
    else:
        origin = request.form['origin']
        destination = request.form['destination']
        departureDate = request.form['departureDate']
        returnDate = request.form['returnDate']
        numAdults = request.form['numAdults']
        numChildren = request.form['numChildren']
        preferredCabin = request.form['preferredCabin']
        flightMaxPrice = request.form['flightMaxPrice']
        centric = request.form['centric']
        category = request.form['category']
        minStars = request.form['minStars']
        activi = request.form.getlist('activities')

        activities = ""
        primer = True
        for a in activi:
            if primer:
                activities += a
                primer = False
            else:
                activities += ","+ a

        '''print origin
        print destination
        print departureDate
        print returnDate
        print numAdults
        print numChildren
        print preferredCabin
        print flightMaxPrice
        print centric
        print category
        print minStars
        print activities'''

        gmess = Graph()

        gmess.bind('paquet', paquet)

        paq = paquet["vacances"]
        gmess.add((paq, paquet.dep_date, Literal(departureDate)))
        gmess.add((paq, paquet.ret_date, Literal(returnDate)))
        gmess.add((paq, paquet.num_adults, Literal(numAdults, datatype=XSD.integer)))
        gmess.add((paq, paquet.num_child, Literal(numChildren, datatype=XSD.integer)))
        gmess.add((paq, paquet.centric, Literal(centric, datatype=XSD.boolean)))
        gmess.add((paq, paquet.category, Literal(category)))
        gmess.add((paq, paquet.min_stars, Literal(minStars, datatype=XSD.float)))

        gmess.add((paq, paquet.origin, Literal(origin)))
        gmess.add((paq, paquet.desti, Literal(destination)))
        gmess.add((paq, paquet.cabin, Literal(preferredCabin)))
        gmess.add((paq, paquet.flight_max_price, Literal(flightMaxPrice, datatype=XSD.integer)))
        gmess.add((paq, paquet.act_types, Literal(activities)))

        gr = demanar_paquet (gmess)
        #Calcul dels dies que duren les vacances
        #return gr.serialize(format="xml")
        dep = datetime.datetime.strptime(departureDate, "%m/%d/%Y")
        ret = datetime.datetime.strptime(returnDate, "%m/%d/%Y")
        date = ret - dep
        dies = date.days


        paq_hotel_gen = gr.subjects(predicate=hotel.subj, object=hotel.obj)
        paq_hotel = ""

        for hid in paq_hotel_gen:
            paq_hotel = hid

        paq_transp_gen = gr.subjects(predicate=viatge.subj, object=viatge.obj)
        paq_viatge = ""

        for vid in paq_transp_gen:
            paq_viatge = vid

        dep_flight_gen = gr.subjects(predicate=vol.dep_subj, object=vol.obj)
        dep_flight = ""

        for df in dep_flight_gen:
            dep_flight = df

        ret_flight_gen = gr.subjects(predicate=vol.ret_subj, object=vol.obj)
        ret_flight = ""

        for rf in ret_flight_gen:
            ret_flight = rf


        currency_code = gr.value(subject= paq_hotel, predicate= hotel.currency_code)
        resultat = '''<!DOCTYPE html>
                    <html>
                    <head lang="en">
                        <meta charset="UTF-8">
                        <title>Resultat</title>
                        <link rel="stylesheet" href="http://netdna.bootstrapcdn.com/bootstrap/3.0.0/css/bootstrap.min.css">
                    </head>
                    <style>
                        h1.titol {
                            text-align: center;
                        }
                        h1,h2,h3,p {
                            color: white;
                        }
                        html {
                            /*background-image: url("http://www.barcelonacomedyfestival.com/uploads/1/1/0/5/11055535/8950828.png");
                            /*"http://www.joug.net/images/full/2014/11/29/exotic-holiday-beach-hd-wallpaper-Exotic-Holiday-Beach-Hd-Wallpaper.jpg");

                            background-size: auto;
                            background-repeat: no-repeat;*/
                            background: url("http://www.barcelonacomedyfestival.com/uploads/1/1/0/5/11055535/8950828.png") no-repeat center center fixed;
                            -webkit-background-size: cover;
                            -moz-background-size: cover;
                            -o-background-size: cover;
                            background-size: cover;
                        }
                        .contingut{
                            background: rgba(0,0,0,0.7);
                            padding: 20px;
                            border-radius: 35px 35px 35px 35px;
                            -moz-border-radius: 35px 35px 35px 35px;
                            -webkit-border-radius: 35px 35px 35px 35px;
                        }
                        label {
                            color: white;
                        }
                        td {
                            vertical-align: 50%;
                            text-align: left;
                            padding: 0px 50px 0px 50px;
                        }
                        td+td,td+td+td {
                            text-align: center;
                        }
                        .container{
                            background: rgba(0,0,0,0) ;
                        }
                        .enFila{
                            /*display: inline;*/
                            text-align: center;
                        }
                        .box {
                            display: flex;
                        }
                        .margeDret {
                            margin-left: 50px;
                        }
                        .torn {
                            padding: 0px 75px 0px 50px;
                        }


                    </style>
                    <body class="container">
                        <h1 class = "titol">Vacances</h1>
                        <div class ="contingut">
                            <div class = "box">
                                <div class = "enFila">
                                    <h2>H</h2>
                                    <h2>O</h2>
                                    <h2>T</h2>
                                    <h2>E</h2>
                                    <h2>L</h2>
                                </div>

                                <div class = "margeDret">
                                    <h3>''' + gr.value(subject= paq_hotel, predicate= hotel.name) + '''</h3>
                                    <p>'''+ gr.value(subject= paq_hotel, predicate= hotel.description).replace("&lt;p&gt;&lt;b&gt;Property Location&lt;/b&gt; &lt;br /&gt;", "")+'''</p>
                                    <p><b>Ratingt: </b>''' + gr.value(subject= paq_hotel, predicate= hotel.rating)+'''</p>
                                    <p><b>Rate per night: </b>''' + (gr.value(subject= paq_hotel, predicate= hotel.rate_per_night) + currency_code)+'''</p>
                                    <p><b>Total rate: </b>''' + (gr.value(subject= paq_hotel, predicate= hotel.total_rate) + currency_code)+'''</p>
                                    <p><b>Address: </b>''' + gr.value(subject= paq_hotel, predicate= hotel.address)+'''</p>
                                    <p><b>Distance  to city: </b>''' + gr.value(subject= paq_hotel, predicate= hotel.proximity) + "KM" +'''</p>
                                </div>
                            </div>
                            <hr>'''
        resultat +=     '''<div class = "box">

                                <div class = "enFila">
                                    <h2>T</h2>
                                    <h2>R</h2>
                                    <h2>A</h2>
                                    <h2>N</h2>
                                    <h2>S</h2>
                                    <h2>P</h2>
                                    <h2>O</h2>
                                    <h2>R</h2>
                                    <h2>T</h2>
                                </div>
                                <div class = "enFila margeDret">
                                    <table>
                                        <thead>
                                            <td></td>
                                            <td><h3>Departure flight</h3></td>
                                            <td><h3>Return flight</h3></td>
                                        </thead>
                                        <tbody>
                                            <tr>
                                                <td><h3>Flight number</h3></td>
                                                <td><p>'''+gr.value(subject= dep_flight, predicate= vol.number)+'''</p></td>
                                                <td><p>'''+gr.value(subject= ret_flight, predicate= vol.number)+'''</p></td>
                                            </tr>
                                            <tr>
                                                <td><h3>Carrier</h3></td>
                                                <td><p>'''+gr.value(subject= dep_flight, predicate= vol.carrier)+'''</p></td>
                                                <td><p>'''+gr.value(subject= ret_flight, predicate= vol.carrier)+'''</p></td>
                                            </tr>
                                            <tr>
                                                <td><h3>Origin</h3></td>
                                                <td><p>'''+gr.value(subject= dep_flight, predicate= vol.orig)+'''</p></td>
                                                <td><p>'''+gr.value(subject= ret_flight, predicate= vol.orig)+'''</p></td>
                                            </tr>
                                            <tr>
                                                <td><h3>Destination</h3></td>
                                                <td><p>'''+gr.value(subject= dep_flight, predicate= vol.dest)+'''</p></td>
                                                <td><p>'''+gr.value(subject= ret_flight, predicate= vol.dest)+'''</p></td>
                                            </tr>
                                            <tr>
                                                <td><h3>Departure time</h3></td>
                                                <td><p>'''+gr.value(subject= dep_flight, predicate= vol.dep_time)+'''</p></td>
                                                <td><p>'''+gr.value(subject= ret_flight, predicate= vol.dep_time)+'''</p></td>
                                            </tr>
                                            <tr>
                                                <td><h3>Arrival time</h3></td>
                                                <td><p>'''+gr.value(subject= dep_flight, predicate= vol.arr_time)+'''</p></td>
                                                <td><p>'''+gr.value(subject= ret_flight, predicate= vol.arr_time)+'''</p></td>
                                            </tr>
                                            <tr>
                                                <td><h3>Duration</h3></td>
                                                <td><p>'''+gr.value(subject= dep_flight, predicate= vol.duration_min)+'''</p></td>
                                                <td><p>'''+gr.value(subject= dep_flight, predicate= vol.duration_min)+'''</p></td>
                                            </tr>
                                        </tbody>
                                    </table>
                                    <h3>Preu Total:  '''+gr.value(subject= paq_viatge, predicate= viatge.price) + " EUR" +'''</h3>
                                </div>
                            </div>
                            <hr>'''
        resultat +=     '''<div class = "box">
                                <div class = "enFila">
                                    <h2>A</h2>
                                    <h2>C</h2>
                                    <h2>T</h2>
                                    <h2>I</h2>
                                    <h2>V</h2>
                                    <h2>I</h2>
                                    <h2>T</h2>
                                    <h2>A</h2>
                                    <h2>T</h2>
                                    <h2>S</h2>
                                </div>
                                <div class = " margeDret">'''
        linia = False
        for day in range(1, dies+1):
            if linia:
                resultat += '''<hr>'''
            else:
                linia = True
            acts_dia = gr.triples((None, activitat.dia, Literal(str(day))))
            resultat += '''<h3>DIA '''+ str(day) + '''</h3>'''
            resultat += '''<div class="torn">'''
            for subj, pred, obj in acts_dia:
                resultat += '''<h3>''' + gr.value(subject= subj, predicate= activitat.torn) + '''</h3>'''
                resultat += '''<p><b>Name: </b>''' + gr.value(subject= subj, predicate= activitat.name) + '''</p>'''
                resultat += '''<p><b>Address: </b>''' + gr.value(subject= subj, predicate= activitat.address) + '''</p>'''
                resultat += '''<p><b>Phone: </b>''' + gr.value(subject= subj, predicate= activitat.phone) + '''</p>'''
                resultat += '''<p><b>Website: </b>''' + gr.value(subject= subj, predicate= activitat.website) + '''</p>'''
                resultat += '''<p><b>Rating: </b>''' + gr.value(subject= subj, predicate= activitat.rating) + '''</p>'''
            resultat += '''</div>'''
        resultat +=     '''    </div>
                            </div>
                        </div>
                    </body>
                    </html>'''
        return resultat
        #return "<!DOCTYPE html><html><head><title>Page Title</title></head><body><h1>Fet.</h1></body></html>"


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
    return "Hola"

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

    #L'usuari dona les seves preferencies del paquet de vacances
    '''
    f = open('testfile.txt', 'r')
    pref = json.load(f)
    origin = pref['origin']
    desti = pref['destination']
    departureDate = pref['departureDate']
    returnDate = pref['returnDate']
    numAdults = pref['numAdults']
    numChildren = pref['numChildren']
    preferredCabin = pref['preferredCabin']
    flightMaxPrice = pref['flightMaxPrice']
    centric = pref['centric']
    minStars = pref['minStars']
    category = pref['category']
    actTypes = pref['activities']
    f.close()

    #Es col·loquen les preferencies en un graf
    gmess = Graph()

    gmess.bind('paquet', paquet)

    paq = paquet["vacances"]
    gmess.add((paq, paquet.dep_date, Literal(departureDate)))
    gmess.add((paq, paquet.ret_date, Literal(returnDate)))
    gmess.add((paq, paquet.num_adults, Literal(numAdults, datatype=XSD.integer)))
    gmess.add((paq, paquet.num_child, Literal(numChildren, datatype=XSD.integer)))
    gmess.add((paq, paquet.centric, Literal(centric, datatype=XSD.boolean)))
    gmess.add((paq, paquet.category, Literal(category)))
    gmess.add((paq, paquet.min_stars, Literal(minStars, datatype=XSD.float)))

    gmess.add((paq, paquet.origin, Literal(origin)))
    gmess.add((paq, paquet.desti, Literal(desti)))
    gmess.add((paq, paquet.cabin, Literal(preferredCabin)))
    gmess.add((paq, paquet.flight_max_price, Literal(flightMaxPrice, datatype=XSD.integer)))
    gmess.add((paq, paquet.act_types, Literal(actTypes)))

    gr = demanar_paquet (gmess)

    #Calcul dels dies que duren les vacances
    dep = datetime.datetime.strptime(departureDate, "%m/%d/%Y")
    ret = datetime.datetime.strptime(returnDate, "%m/%d/%Y")
    date = ret - dep
    dies = date.days

    processar_paquet(gr, dies)

    #print gr.serialize(format='xml')

    #Selfdestruct
    requests.get(AgentUsuari.stop)
    '''

if __name__ == '__main__':
    # Ponemos en marcha los behaviors
    ab1=Process(target=agentbehavior1)
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=port)

    # Esperamos a que acaben los behaviors
    ab1.join()
    print 'The End'
