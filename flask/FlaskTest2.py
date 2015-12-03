__author__ = 'bejar'

from  multiprocessing import Process
from flask import Flask,request
app = Flask(__name__)

@app.route("/agente")
def agent1():
    x = int(request.args['x'])
    y = int(request.args['y'])
    return str(x+y)

if __name__ == '__main__':
    app.run()