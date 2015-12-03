# -*- coding: utf-8 -*-
"""
filename: Cuenta

Dos procesos contando numeros

Created on 12/02/2014

@author: javier
"""

__author__ = 'javier'

from multiprocessing import Process

def cuenta(li,ls):
    for i in range(li,ls):
      print i,'\n'

if __name__ == '__main__':
    p1 = Process(target=cuenta, args=(10,20,))
    p2 = Process(target=cuenta, args=(20,30,))
    p1.start()
    p2.start()
    p1.join()
    p2.join()