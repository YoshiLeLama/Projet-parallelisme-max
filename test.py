import parmax as pm
import time

import matplotlib.pyplot as plt
import networkx as nx

X = 0
Y = 0
Z = 0


def runT1():
    global X

    X = 1


def runT2():
    global Y

    Y = 2


def runTsomme():
    global X, Y, Z

    Z = X + Y


def runTmulti():
    global Z

    print(Z * 3)


t1 = pm.Task("T1", [], ["X"], runT1)

t2 = pm.Task("T2", [], ["Y"], runT2)

tSomme = pm.Task("somme", ["X", "Y"], ["Z"], runTsomme)

try:
    s1 = pm.TaskSystem([t1, t2, tSomme], {
                       "T1": [], "T2": [], "somme": ["T1", "T2"]})
    s1.detTestRnd()
    s1.parCost()
except pm.TaskValidationException as e:
    print(e)
else:
    s1.run()
    print(X, Y, Z)
    s1.run()
    print(X, Y, Z)
    s1.run()
    print(X, Y, Z)
