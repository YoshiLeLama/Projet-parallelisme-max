import time
from typing import Callable
from threading import Thread
import graphviz
import statistics
import networkx as nx
import matplotlib.pyplot as plt
import random


class Task:
    name: str
    reads: set[str]
    writes: set[str]
    run: Callable[[dict], None]

    def __init__(self, name: str, reads: set[str], writes: set[str], run: Callable[[dict], None]) -> None:
        self.name = name
        self.reads = reads.copy()
        self.writes = writes.copy()
        self.run = run


class TaskValidationException(Exception):
    ...


class TaskSystem:
    precedencies: dict[str, set[str]]
    tasks: dict[str, Task]
    finished_tasks: set[str]
    variables: dict[str, int]
    seq_exec_queue: list[Task]

    def __init__(self, tasks: list[Task], prec: dict, variables: dict):
        self.tasks = {t.name: t for t in tasks}
        self.precedencies = prec.copy()
        self.variables = variables.copy()
        self.finished_tasks = set()
        self.seq_exec_queue = []

        self.check_entry_validity(tasks, prec)

        self.algo_para_max(shouldDraw=False)

    def algo_para_max(self, shouldDraw: bool = True):
        # {"T1": [], "T2": ["T1"], "somme": ["T2", "T1"]}
        precedencies: dict[str, set[str]] = dict()
        for t in self.tasks.keys():
            precedencies[t] = set()

        # On créer un chemin entre 2 tâches T1 et T2 si les conditions de bernstein
        # L1 ∩ E2 = ∅ et L2 ∩ E1 = ∅ et E1 ∩ E2 = ∅ ne sont pas respecter.
        for tDestName, tDest in self.tasks.items():
            precs = self.get_precedencies(tDestName)
            for tOriginName in precs:
                tOrigin = self.tasks[tOriginName]
                if len(tOrigin.reads.intersection(tDest.writes)) != 0 or len(tDest.reads.intersection(tOrigin.writes)) != 0 or len(tOrigin.writes.intersection(tDest.writes)) != 0:
                    precedencies[tDestName].add(tOriginName)

        # 1 -> 2 -> 6
        # |---------|
        # On veut suppr le liens de 1 à 6
        new_precedencies = {name: precs.copy()
                            for name, precs in precedencies.items()}

        # Fonction récursive pour retirer les précédences redondantes de la tâche tDest
        def removeRedundancy(tDest: str, tOrigin: str, tDestPrecs: set[str]):
            new_precedencies[tDest].difference_update(
                precedencies[tOrigin].intersection(tDestPrecs))
            # print(precedencies, new_precedencies)
            for newOrigin in precedencies[tOrigin]:
                removeRedundancy(tDest, newOrigin, tDestPrecs)

        # Pour chaque tâche, on enlève les précédences redondantes en remontant jusqu'à la racine et en testant si tDest a des précédences communes avec des tâches la précédant
        for tDest, tDestPrecs in precedencies.items():
            for tOrigin in tDestPrecs:
                removeRedundancy(tDest, tOrigin, tDestPrecs)

        self.precedencies = new_precedencies.copy()

        if shouldDraw:
            self.draw_pydot()

    def get_precedencies(self, task_name: str):
        """permet de récupérer toutes les précédences de la tâche évaluer. Utilisé pour vérifier qu'une liste de tâche est déterminer.
        Par exemple si on a A->B->C et qu'on étudie C la focntion nous retournera A,B

        Args:
            task_name (str): tâche considéré

        Returns:
            set(str): un set de toutes les précédences de la tâche.
        """
        precedencies_list = self.precedencies[task_name]

        if len(precedencies_list) == 0:
            return set()

        new_precedencies = set(precedencies_list)

        for t in precedencies_list:
            new_precedencies = new_precedencies.union(self.get_precedencies(t))

        return new_precedencies

    def generate_task_closure(self, task: Task):
        """
        permet de respecter les contraintes de précédence pour l'exécution // de notre liste de tâche à exécuter.

        Args:
            task (Task): tâche à exécuter

        Returns:
            function: la fonction permettant de respecter les contrainte de précédence.
        """
        precedence_tasks = set(self.precedencies[task.name])
        # on attends que toutes les conditions de précédences soit vérifiés de la tâche mis en paramètre.

        def run_task():
            while True:
                if precedence_tasks.issubset(self.finished_tasks):
                    break

            task.run(self.variables)

            self.finished_tasks.add(task.name)

        return run_task

    #  exécuter les tâches du système de façon séquentielle en respectant l’ordre imposé par la relation de précédence,

    def runSeq(self) -> None:
        """
        exécute notre liste de tâche de manière séquentiel en respectant les contraintes de précédence.
        """
        if len(self.seq_exec_queue) != len(self.tasks):
            self.seq_exec_queue = []
            added_tasks: set[str] = set()
            # On récupère toutes les tâches racine (elles n'ont pas de relation de dépendance)
            for task_name in (k for (k, v) in self.precedencies.items() if len(v) == 0):
                self.seq_exec_queue.append(self.tasks[task_name])
                added_tasks.add(task_name)

            new_queue = self.seq_exec_queue.copy()
            # tant que tous les éléments ne sont pas dans exec_queue on continue.
            while len(self.seq_exec_queue) != len(self.tasks):
                for (name, task) in self.tasks.items():
                    dep = self.precedencies[name]
                    # on recherche une tache qui n'est n'est pas déjà dans la file d'exécution et pour laquellle toute c taches sont dans la file d"exécution.
                    if all(elem in (t.name for t in self.seq_exec_queue) for elem in dep) and name not in added_tasks:
                        new_queue.append(task)
                        added_tasks.add(name)

                self.seq_exec_queue = new_queue.copy()
        # On exécute les taches.
        for task in self.seq_exec_queue:
            task.run(self.variables)

    def run(self, shuffle: bool = False) -> None:
        """
        lance notre liste de tâche de manière // en respectant les contraintes de précédence.
        """
        self.finished_tasks = set()
        threads: list[Thread] = []
        # On créer des threads pour toutes les tâches.
        for task in self.tasks.values():
            threads.append(Thread(target=self.generate_task_closure(task)))

        # Si shuffle est True, alors on mélange aléatoirement l'ordre d'exécution des threads
        if shuffle:
            random.shuffle(threads)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

    def check_entry_validity(self, tasks: list[Task], prec: dict[str, list[str]]) -> bool:
        """fonctoin qui permet de vérifier que la liste de tâche fournie par l'utilisateur est valide. Pour cela on va faire plusieurs tests.

        Args:
            tasks (list[Task]): liste des tâches
            prec (dict[str, list[str]]): la dépendence de précédence des différentes tâches

        Erreurs:
            TaskValidationException

        Returns:
            bool: l'entrée fournie est valide.
        """
        # un nom de tâche est dupliqué
        tasks_set: set[str] = set()
        for x in tasks:
            if x.name in tasks_set:
                raise TaskValidationException(
                    "Le nom de tâche {} est dupliqué".format(x.name))
            tasks_set.add(x.name)
        # contien un nom de tache invalide
        for (t_name, names) in prec.items():
            for name in names:
                if name not in tasks_set:
                    raise TaskValidationException(
                        "La liste de précédence de {} contient un nom de tâche invalide".format(t_name))

        # Au moins une des tâche est la racine
        if len(list(t for t in tasks if len(prec[t.name]) == 0)) == 0:
            raise TaskValidationException("Il n'y a pas de racine")

        # on vérifie s'il y a une boucle par ex :
        # T1->T2->T3
        #  |<|----|
        for (k, v) in prec.items():
            stage = v[:]
            new_stage = []
            while len(stage) != 0:
                for t in stage:
                    if k == t:
                        raise TaskValidationException(
                            "{} est au sein d'une boucle".format(k))
                    new_stage += prec[t]
                stage = new_stage[:]
                new_stage = []

        # déterminisme
        # L'objectif  est de vérifier que pour toutes les tâche si 2 tâches qui n'ont pas de relation de précédence, alors il faut vérif que t1.read not in t2.write and t2.read not in t1.write and t2.write not in t1.write.
        # à vérifié. Pas sûr que cela fonctionne

        for k, v in prec.items():
            for ele in tasks:
                # la condition permet de vérif qu'on a pas : A->B ou A->B->C
                if ele.name == k or ele.name in self.get_precedencies(k) or k in self.get_precedencies(ele.name):
                    continue
                # On regarde si les 2 éléments ne écrivent pas au même endroit
                if len(ele.writes.intersection(self.tasks[k].writes)) != 0:
                    raise TaskValidationException(
                        "{0} et {1} écrivent au même endroit sans contrainte de précédence.".format(ele.name, k))
                # on regarde si k ne lit pas dans ce que ele écrit
                elif len(ele.writes.intersection(self.tasks[k].reads)) != 0:
                    raise TaskValidationException(
                        "{0} écrit dans ce que lit {1} sans contrainte de précédance.".format(ele.name, k))
                # on regarde si k n'écrit pas dans ce que ele lit.
                elif len(ele.reads.intersection(self.tasks[k].writes)) != 0:
                    raise TaskValidationException(
                        "{0} écrit dans ce que lit {1} sans contrainte de précédance.".format(k, ele.name))

        if not self.detTestRnd():
            raise TaskValidationException(
                "Le test randomisé de déterminisme montre que le système est indéterminé")

        return True

    def detTestRnd(self):
        """
        Fonction pour tester si le système est effectivement déterministe
        """
        results = []
        initialVariables = self.variables.copy()
        for _ in range(5):
            for k in initialVariables.keys():
                self.variables[k] = random.randint(-1000, 1000)
            initialVariablesRandomize = self.variables.copy()
            # On récupère l'états des variables après 5 (nombre arbitraire) exécutions parallèles randomisées
            for _ in range(0, 5):
                self.run(shuffle=True)
                results.append(self.variables.copy())
                self.variables = initialVariablesRandomize.copy()

            # On vérifie que l'état des variables est le même pour chaque exécution
            for varName in self.variables:
                baseValue = results[0][varName]
                for i in range(1, len(results)):
                    if results[i][varName] != baseValue:
                        return False
        self.variables = initialVariables.copy()
        return True

    def parCost(self):
        """
        fonction qui permet de comparer le temps d'exécution des 2 fonctions en utilisant perf_conter
        """
        self.run()
        self.runSeq()
        resultRun = []
        resultRunSeq = []
        for _ in range(10):
            start = time.perf_counter_ns()
            self.run()
            end = time.perf_counter_ns() - start
            resultRun.append(end)
            start = time.perf_counter_ns()
            self.runSeq()
            end = time.perf_counter_ns() - start
            resultRunSeq.append(end)
        print(
            "temps moyen d'execution // : {0}ns".format(statistics.median(resultRun)))
        print(
            "temps médian d'execution // : {0}ns".format(statistics.mean(resultRun)))
        print("temps moyen d'execution séquentielle : {0}ns".format(
            statistics.median(resultRunSeq)))
        print("temps médian d'execution séquentielle : {0}ns".format(
            statistics.mean(resultRunSeq)))

    def draw_graphviz(self):
        """
        permet de générer l'arbre d'exécution en utilisant graphviz.
        """
        dot = graphviz.Digraph(directory=None)
        # genération de tous les noeuds
        for task in self.tasks:
            dot.node(task)
        for task, dependecies in self.precedencies.items():
            for dependece in dependecies:
                # lien entre les noeuds pour les dépendances.
                dot.edge(dependece, task)

        dot.format = 'png'
        dot.render('Graph', view=True)

    def draw_pydot(self):
        precedence_graph = nx.DiGraph()

        for task in self.tasks:
            precedence_graph.add_node(task)
        for task, dependecies in self.precedencies.items():
            for dependence in dependecies:
                # lien entre les noeuds pour les dépendances.
                precedence_graph.add_edge(dependence, task)

        plt.subplot(111)
        nx.draw_networkx(precedence_graph, pos=nx.nx_pydot.pydot_layout(precedence_graph, prog="dot"),
                         with_labels=True, node_size=2000, node_shape="o",
                         font_family="JetBrains Mono", font_size=12,
                         node_color="#FFEEDD", edgecolors="#000000")

        plt.show()
