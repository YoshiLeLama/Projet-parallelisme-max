import random
import parmax as pm
import time

import matplotlib.pyplot as plt
import networkx as nx

X = 0
Y = 0
Z = 0


variables = {'X': 0, 'Y': 0, 'Z': 0}


def runT1(v: dict):
    v['X'] = 1


def runT2(v: dict):
    v['Y'] = 2
    v['X'] = 2


def runTsomme(v: dict):
    v['Z'] = v['X'] + v['Y']

def runTmulti(v: dict):
    global Z

    Z *= 2


t1 = pm.Task("T1", [], ["X"], runT1)

t2 = pm.Task("T2", [], ["Y"], runT2)

tSomme = pm.Task("somme", ["X", "Y"], ["Z"], runTsomme)

tMulti = pm.Task("multi", ["Z"], ["Z"], runTmulti)

try:
    s1 = pm.TaskSystem([t1, t2, tSomme, tMulti], {
                       "T1": [], "T2": [], "somme": ["T1", "T2"], "multi": ["somme"]},
                       variables)
    # s1.parCost()
    # s1.draw_pydot()
except pm.TaskValidationException as e:
    print(e)
else:
    print(s1.detTestRnd())
    # s1.run()
    # print(X, Y, Z)
    # s1.run()
    # print(X, Y, Z)
    # s1.run()
    # print(X, Y, Z)
