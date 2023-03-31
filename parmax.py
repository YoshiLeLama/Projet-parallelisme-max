from typing import Callable
from threading import Thread


class Task:
    name: str
    reads: list[str]
    writes: list[str]
    run: Callable[[], None]

    def __init__(self, name: str, reads: list[str], writes: list[str], run: Callable[[], None]) -> None:
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

    def __init__(self, tasks: list[Task], prec: dict) -> None:
        self.tasks = {t.name: t for t in tasks}
        self.check_entry_validity(tasks, prec)

        self.precedencies = prec.copy()
        self.finished_tasks = set()

    def get_dependencies(self, nom_tache: str) -> list[str]:
        return self.precedencies[nom_tache]

    def generate_task_closure(self, task: Task):
        precedence_tasks = set(self.get_dependencies(task.name))
        # on attends que toutes les conditions de précédences soit vérifiés.

        def run_task():
            while True:
                if precedence_tasks.issubset(self.finished_tasks):
                    break

            task.run()

            print(task.name)

            self.finished_tasks.add(task.name)

        return run_task

    #  exécuter les tâches du système de façon séquentielle en respectant l’ordre imposé par la relation de précédence,

    def runSeq(self) -> None:
        exec_queue: list[Task] = []
        added_tasks: set[str] = set()
        # On récupère toutes les tâches racine (elles n'ont pas de relation de dépendance)
        for task_name in (k for (k, v) in self.precedencies.items() if len(v) == 0):
            exec_queue.append(self.tasks[task_name])
            added_tasks.add(task_name)

        new_queue = exec_queue.copy()
        # tant que tous les éléments ne sont pas dans exec_queue on continue.
        while len(exec_queue) != len(self.tasks):
            for (name, task) in self.tasks.items():
                dep = self.get_dependencies(name)
                # on recherche une tache qui n'est n'est pas déjà dans la file d'exécution et pour laquellle toute c taches sont dans la file d"exécution.
                if all(elem in (t.name for t in exec_queue) for elem in dep) and name not in added_tasks:
                    new_queue.append(task)
                    added_tasks.add(name)

            exec_queue = new_queue.copy()
        # On exécute les taches.
        for task in exec_queue:
            print(task.name)
            task.run()

    def run(self) -> None:
        self.finished_tasks = set()
        threads: list[Thread] = []
        # On créer des threads pour toutes les tâches.
        for task in self.tasks.values():
            threads.append(Thread(target=self.generate_task_closure(task)))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

    def check_entry_validity(self, tasks: list[Task], prec: dict[str, list[str]]) -> bool:
        tasks_set: set[str] = set()
        for x in tasks:
            if x.name in tasks_set:
                raise TaskValidationException(
                    "Le nom de tâche {} est dupliqué".format(x.name))
            tasks_set.add(x.name)

        for (t_name, names) in prec.items():
            for name in names:
                if name not in tasks_set:
                    raise TaskValidationException(
                        "La liste de précédence de {} contient un nom de tâche invalide".format(t_name))

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
                if ele.name not in v:
                    # On regarde si les 2 éléments ne lisent pas au même endroit
                    if any(lecture in self.tasks[ele.name].reads for lecture in self.tasks[k].reads):
                        raise TaskValidationException(
                            "2 taches sans contrainte de précédence lisent au même endroit. Le système de tâche est donc indéterminé.")
                    # on regarde si k ne lit pas dans ce que ele écrit
                    elif any(lecture in self.tasks[ele.name].writes for lecture in self.tasks[k].reads):
                        raise TaskValidationException(
                            "une tâches écrties dans ce que lie une autre tache sans contrainte de précédance.Le système de tâche est donc indéterminé.")

                    # on regarde si k n'écrit pas dans ce que ele ecrit.
                    elif (ecriture in self.tasks[ele.name].reads for lecture in self.tasks[k].writes):
                        raise TaskValidationException(
                            "une tâches écrties dans ce que lie une autre tache sans contrainte de précédance.Le système de tâche est donc indéterminé.")

        return True
