import random
import parmax as pm
import time

import matplotlib.pyplot as plt
import networkx as nx


variables = {'X': 0, 'Y': 0, 'Z': 0}


def runT1(v: dict):
    v['X'] = 1


def runT2(v: dict):
    v['Y'] = 2


def runTsomme(v: dict):
    v['Z'] = v['X'] + v['Y']


t1 = pm.Task("T1", set(), {"X"}, runT1)

t2 = pm.Task("T2", set(), {"Y"}, runT2)

tSomme = pm.Task("somme", {"X", "Y"}, {"Z"}, runTsomme)

try:
    s1 = pm.TaskSystem([t1, t2, tSomme], {
                       "T1": [], "T2": [], "somme": ["T1", "T2"]},
                       variables)

    # s1.algo_para_max()
    # s1.parCost()
    # s1.draw_pydot()
except pm.TaskValidationException as e:
    print(e)
else:
    # print(s1.detTestRnd())
    s1.parCost()
    # s1.draw_pydot()
    # s1.run()
    # print(X, Y, Z)
    # s1.run()
    # print(X, Y, Z)
    # s1.run()
    # print(X, Y, Z)
