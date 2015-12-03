# -*- coding: utf-8 -*-
"""
filename: CominicacionTuberia


Dos procesos que se comunican entre si a traves de una tuberia

Created on 12/02/2014

@author: javier
"""

__author__ = 'javier'

from multiprocessing import Process, Pipe

def proceso1(conn):
    for i in range(10):
        conn.send(i)
        print conn.recv(), 'P1:'
    conn.close()

def proceso2(conn):
    for i in range(10):
        print conn.recv(),'P2:'
        conn.send(i)
    conn.close()

if __name__ == '__main__':
    conn1, conn2 = Pipe()
    p1 = Process(target=proceso1, args=(conn1,))
    p1.start()
    p2 = Process(target=proceso2, args=(conn2,))
    p2.start()
    p1.join()
    p2.join()
