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
    reads: list[str]
    writes: list[str]
    run: Callable[[dict], None]

    def __init__(self, name: str, reads: list[str], writes: list[str], run: Callable[[dict], None]) -> None:
        self.name = name
        self.reads = reads[:]
        self.writes = writes[:]
        self.run = run


class TaskValidationException(Exception):
    ...


class TaskSystem:
    precedencies: dict[str, list[str]]
    tasks: dict[str, Task]
    finished_tasks: set[str]
    variables: dict[str, int]
    seq_exec_queue: list[Task]

    def __init__(self, tasks: list[Task], prec: dict, variables: dict) -> None:

        self.tasks = {t.name: t for t in tasks}
        self.precedencies = prec.copy()
        self.variables = variables
        self.check_entry_validity(tasks, prec)

        self.finished_tasks = set()
        self.seq_exec_queue = []

    def get_dependencies(self, nom_tache: str) -> list[str]:
        return self.precedencies[nom_tache]

    def get_precedencies(self, task_name: str):
        """permet de récupérer toutes les précédences de la tâche évaluer. Sers pour vérifier qu'une liste de tâche est déterminer.
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
        precedence_tasks = set(self.get_dependencies(task.name))
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
                    dep = self.get_dependencies(name)
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

        if shuffle:
            random.shuffle(threads)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        print(self.variables)

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
                # la condition permet de vérif qu'on a pas : A->B
                if ele.name == k or ele.name in self.get_precedencies(k) or k in self.get_precedencies(ele.name):
                    continue
                # On regarde si les 2 éléments ne écrivent pas au même endroit
                if len(set(ele.writes).intersection(set(self.tasks[k].writes))) != 0:
                    raise TaskValidationException(
                        "2 taches sans contrainte de précédence ecrivent au même endroit. Le système de tâche est donc indéterminé.")
                # on regarde si k ne lit pas dans ce que ele écrit
                elif len(set(ele.writes).intersection(set(self.tasks[k].reads))) != 0:
                    raise TaskValidationException(
                        "une tâches écrties dans ce que lie une autre tache sans contrainte de précédance.Le système de tâche est donc indéterminé.")
                # on regarde si k n'écrit pas dans ce que ele lit.
                elif len(set(ele.reads).intersection(set(self.tasks[k].writes))) != 0:
                    raise TaskValidationException(
                        "une tâches écrties dans ce que lie une autre tache sans contrainte de précédance.Le système de tâche est donc indéterminé.")

        if not self.detTestRnd():
            raise TaskValidationException(
                "Le test randomisé de déterminisme montre que le système est indéterminé")

        return True

    def detTestRnd(self):
        """
        fct qui permet d'exécuter notre liste de tâche de manière séquentielle pour voir si une variable ou une dépendence n'a pas été oublié d'être spécifié. 
        """
        results = []
        initialVariables = self.variables.copy()
        for _ in range(0, 5):
            self.run(shuffle=True)
            results.append(self.variables.copy())
            self.variables = initialVariables.copy()

        for varName in self.variables:
            baseValue = results[0][varName]
            for i in range(1, len(results)):
                if results[i][varName] != baseValue:
                    return False

        return True

    def parCost(self):
        """
        fonction qui permet de comparer le temps d'exécution des 2 fonctions en utilisant perf_conter
        """
        self.run()
        self.runSeq()
        resultRun = []
        resultRunSeq = []
        for _ in range(5):
            start = time.perf_counter_ns()
            self.run()
            end = time.perf_counter_ns() - start
            resultRun.append(end)
            start = time.perf_counter_ns()
            self.runSeq()
            end = time.perf_counter_ns() - start
            resultRunSeq.append(end)
        print(
            "temps moyen d'execution // : {0}ns".format(statistics.mean(resultRun)))
        print("temps moyen d'execution séquentielle : {0}ns".format(
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
