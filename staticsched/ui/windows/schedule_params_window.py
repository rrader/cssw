from tkinter import *
from tkinter.ttk import *
from staticsched.graph_analytics.cpu_priorities import CohesionCPUPrioritizationPolicy
from staticsched.graph_analytics.gantt import System
from staticsched.graph_analytics.router import DFSRouter
from staticsched.graph_analytics.scheduler.schedulers import AdvanceNeighbourScheduler, \
    ModellingNeighbourScheduler
from staticsched.graph_analytics.task_queues import QueueGenerationPolicy3, QueueGenerationPolicy4, \
    QueueGenerationPolicy16
from staticsched.ui.gantt_ui import draw_gantt_diagram


def make_entry(parent, caption, var, widget=Entry, **options):
    Label(parent, text=caption).pack(side=TOP)
    if widget == Checkbutton:
        entry = widget(parent, variable=var, **options)
    else:
        entry = widget(parent, textvariable=var, **options)
    entry.pack(side=TOP)
    return entry


QUEUE_GENERATION_POLICIES = {
    "3": QueueGenerationPolicy3,
    "4": QueueGenerationPolicy4,
    "16": QueueGenerationPolicy16,
}

CPU_PRIORITIZATION_POLICIES = {
    "Cohesion": CohesionCPUPrioritizationPolicy,
}

SCHEDULERS = {
    "5: Advance Neighbour Scheduler": AdvanceNeighbourScheduler,
    "6: Modelling Neighbour Scheduler": ModellingNeighbourScheduler,
}


class SchedulerParamsWindow:
    def __init__(self, root, task_dag, system_graph):
        self.task_dag = task_dag
        self.system_graph = system_graph

        self.queue_generation_policy = StringVar(value=sorted(list(QUEUE_GENERATION_POLICIES.keys()))[0])
        self.cpu_prioritization_policy = StringVar(value=sorted(list(CPU_PRIORITIZATION_POLICIES.keys()))[0])
        self.scheduler_type = StringVar(value=sorted(list(SCHEDULERS.keys()))[0])
        self.duplex = BooleanVar(value=False)
        self.io_cpu = BooleanVar(value=True)

        self.root = Toplevel(root)
        self.root.wm_title("Scheduler params")
        self.build()

    def build(self):
        self.frame = Frame(self.root)
        self.frame.pack(fill='both', expand=True)

        make_entry(self.frame, "queue_generation_policy", self.queue_generation_policy,
                   widget=Combobox, values=sorted(list(QUEUE_GENERATION_POLICIES.keys())))
        make_entry(self.frame, "cpu_prioritization_policy", self.cpu_prioritization_policy,
                   widget=Combobox, values=sorted(list(CPU_PRIORITIZATION_POLICIES.keys())))
        make_entry(self.frame, "scheduler_type", self.scheduler_type,
                   widget=Combobox, values=sorted(list(SCHEDULERS.keys())))
        make_entry(self.frame, "duplex", self.duplex, widget=Checkbutton)
        make_entry(self.frame, "io_cpu", self.io_cpu, widget=Checkbutton)

        button = Button(self.frame, text='okay', command=self.do_generate)
        button.pack(side='right')

    def do_generate(self):
        queue_generation_policy = QUEUE_GENERATION_POLICIES[self.queue_generation_policy.get()]()
        cpu_prioritization_policy = CPU_PRIORITIZATION_POLICIES[self.cpu_prioritization_policy.get()]()
        scheduler_type = SCHEDULERS[self.scheduler_type.get()]

        system = System(self.system_graph,
                        duplex=self.duplex.get(),
                        has_io_cpu=self.io_cpu.get())
        print(self.duplex.get(), self.io_cpu.get())
        router = DFSRouter(self.system_graph)

        scheduler = scheduler_type(self.task_dag, self.system_graph,
                                   queue_generation_policy,
                                   cpu_prioritization_policy,
                                   system,
                                   router)
        scheduler.schedule_dag()
        draw_gantt_diagram(system)
