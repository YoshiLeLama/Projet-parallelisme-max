import random
import parmax as pm
import time

import matplotlib.pyplot as plt
import networkx as nx


variables = {'V1': 0, 'V2': 0, 'V3': 0, 'V4': 0, 'V5': 0, 'V6': 0}


def m1(v: dict):
    pass


def m2(v: dict):
    pass


def m3(v: dict):
    pass


def m4(v: dict):
    pass


def m5(v: dict):
    pass


def m6(v: dict):
    pass


M1 = pm.Task("M1", {"V1"}, {"V4"}, m1)
M2 = pm.Task("M2", {"V3", "V4"}, {"V1"}, m2)
M3 = pm.Task("M3", {"V3", "V4"}, {"V5"}, m3)
M4 = pm.Task("M4", {"V4"}, {"V2"}, m4)
M5 = pm.Task("M5", {"V5"}, {"V5"}, m5)
M6 = pm.Task("M6", {"V1", "V2"}, {"V4"}, m6)

try:
    s1 = pm.TaskSystem(
        [M1, M2, M3, M4, M5, M6],
        {
            "M1": [],
            "M2": ["M1"],
            "M3": ["M1"],
            "M4": ["M2", "M3"],
            "M5": ["M3"],
            "M6": ["M4", "M5"]
        }, variables)
    s1.algo_para_max()
except pm.TaskValidationException as e:
    print(e)
