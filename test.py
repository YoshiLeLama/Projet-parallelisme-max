import random
import parmax as pm
import time

import matplotlib.pyplot as plt
import networkx as nx

X = 0
Y = 0
Z = 0


def runT1():
    global X, Y
    Y = 6

    X = 1
    print(X)


def runT2():
    global Y

    Y = 2
    print(Y)


def runTsomme():
    global X, Y, Z
    Z = X + Y
    print(X, Y, Z)


def runTmulti():
    global Z

    print(Z * 3)


t1 = pm.Task("T1", [], ["X"], runT1)

t2 = pm.Task("T2", [], ["Y"], runT2)

tSomme = pm.Task("somme", ["X", "Y"], ["Z"], runTsomme)

tMulti = pm.Task("multi", ["Z"], ["Z"], runTmulti)

try:
    s1 = pm.TaskSystem([t1, t2, tSomme, tMulti], {
                       "T1": [], "T2": [], "somme": ["T1", "T2"], "multi": ["somme"]})
    # s1.parCost()
except pm.TaskValidationException as e:
    print(e)
else:
    s1.detTestRnd()
    # s1.run()
    # print(X, Y, Z)
    # s1.run()
    # print(X, Y, Z)
    # s1.run()
    # print(X, Y, Z)
