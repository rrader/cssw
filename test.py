import json
import warnings
from staticsched.graph_analytics.cpu_priorities import CohesionCPUPrioritizationPolicy
from staticsched.graph_analytics.gantt import System
from staticsched.graph_analytics.raw_graph import Graph, DAG
from staticsched.graph_analytics.router import DFSRouter
from staticsched.graph_analytics.scheduler.schedulers import AdvanceNeighbourScheduler, ModellingNeighbourScheduler
from staticsched.graph_analytics.task_queues import QueueGenerationPolicy3, QueueGenerationPolicy4, \
    QueueGenerationPolicy16


def test(scale, connectivity, queue, scheduler_class, duplex, io_cpu, count=50):
    system_graph = get_grid_system()
    count = len(system_graph.nodes) * scale

    system = System(system_graph,
                    duplex=duplex,
                    has_io_cpu=io_cpu)
    router = DFSRouter(system_graph)

    k_accels = []
    k_efs = []
    for i in range(count):
        task_dag = DAG.generate(min_weight=5, max_weight=20,
                                count=count, connectivity=connectivity,
                                connections_percent=30)
        scheduler = scheduler_class(
            task_dag, system_graph, queue(), CohesionCPUPrioritizationPolicy(),
            system, router)
        scheduler.schedule_dag()
        k_accel = task_dag.duration_on_one_cpu() / system.duration()
        k_accels.append(k_accel)
        k_ef = k_accel / len(system._cpus)
        k_efs.append(k_ef)
    k_accel_avg = sum(k_accels) / len(k_accels)
    k_ef_avg = sum(k_efs) / len(k_efs)
    return k_accel_avg, k_ef_avg


def get_thor_system():
    system_graph = Graph()
    with open("saved/thor") as thor_file:
        system_graph_file = json.load(thor_file)
        Graph.deserialize(system_graph, system_graph_file)
    return system_graph


def get_grid_system():
    system_graph = Graph()
    with open("saved/grid") as thor_file:
        system_graph_file = json.load(thor_file)
        Graph.deserialize(system_graph, system_graph_file)
    return system_graph


def loop(scale, queue, scheduler_class, duplex, io_cpu, count=50):
    print(queue.__name__ + " ", end='')
    print(scheduler_class.__name__ + " ", end='')
    if duplex:
        print("duplex; ", end='')
    else:
        print("no duplex; ", end='')
    if io_cpu:
        print("io_cpu; ", end='')
    else:
        print("no io_cpu; ", end='')
    print("scale %d:1" % scale)

    connectivity = 0.1
    data = []
    while connectivity < 1:
        # print(">>", connectivity)
        accel, ef = test(scale=scale, connectivity=connectivity,
                         queue=queue,
                         scheduler_class=scheduler_class,
                         duplex=duplex, io_cpu=io_cpu,
                         count=count)
        data.append("%s, %s" % (accel, ef))

        connectivity += 0.1
    print("\n".join(data))


def main():
    warnings.simplefilter("ignore")
    scheduler_class = ModellingNeighbourScheduler
    duplex = True
    scale = 1
    # loop(scale, queue=QueueGenerationPolicy3, scheduler_class=scheduler_class,
    #      duplex=duplex, io_cpu=True)
    # print("================")
    # loop(scale, queue=QueueGenerationPolicy4, scheduler_class=scheduler_class,
    #      duplex=duplex, io_cpu=True)
    # print("================")
    # loop(scale, queue=QueueGenerationPolicy16, scheduler_class=scheduler_class,
    #      duplex=duplex, io_cpu=True)
    # print("================")

    accel, ef = test(scale=scale, connectivity=0.7,
                     queue=QueueGenerationPolicy3,
                     scheduler_class=scheduler_class,
                     duplex=duplex, io_cpu=True,
                     count=1)


if __name__ == "__main__":
    main()