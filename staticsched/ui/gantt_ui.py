from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator


def task_annotation_text(task):
    return "%s-%s-%s\n[%s>%s]" % (task.transmission.source_cpu,
                                     task.meta().target,
                                     task.transmission.target_cpu,
                                     task.transmission.source.n_id,
                                     task.transmission.target.n_id
                                     )


def draw_gantt_diagram(system):
    fig = plt.figure()
    ax = fig.add_subplot(111)

    max_time = 0
    for i, cpu in enumerate(sorted(system._cpus.values(), key=lambda cpu: cpu.cpu_id)):
        ranges = []
        for task in cpu._alu_tasks:
            if task.range[1] > max_time:
                max_time = task.range[1]
            duration = task.range[1] - task.range[0]
            ranges.append((task.range[0], duration))
            plt.annotate("%s [%s]" % (task.task_name, duration), (task.range[0] + 0.1, i + 0.1))
        ax.broken_barh(ranges, (i, 0.3), alpha=.5, facecolors='lightgray')

        link_height = 0.7 / len(cpu._links)
        for link in cpu._links:
            ranges = []
            for task in link._io_tasks:
                if task.direction == 0:
                    continue
                if task.range[1] > max_time:
                    max_time = task.range[1]
                duration = task.range[1] - task.range[0]
                ranges.append((task.range[0], duration))
                plt.annotate(task_annotation_text(task),
                             (task.range[0] + 0.1, i + 0.3 + link_height*link.link_id + 0.05 + link_height/2))
            ax.broken_barh(ranges, (i + 0.3 + link_height*link.link_id + link_height/2, link_height/2),
                           alpha=.5, facecolors='yellow', hatch="/")

            ranges = []
            for task in link._io_tasks:
                if task.direction == 1:
                    continue
                if task.range[1] > max_time:
                    max_time = task.range[1]
                duration = task.range[1] - task.range[0]
                ranges.append((task.range[0], duration))
                plt.annotate(task_annotation_text(task),
                             (task.range[0] + 0.1, i + 0.3 + link_height*link.link_id + 0.05))
            ax.broken_barh(ranges, (i + 0.3 + link_height*link.link_id, link_height/2),
                           alpha=.5, facecolors='yellow', hatch="\\")

    #
    # for x in range(1, cpus+1):
    #     rang = []
    #     for t in plan_copy[x-1]:
    #         rang.append((t[0], t[1] - t[0]))
    #         plt.annotate("{}>\n{}".format(t[2], t[3]), (t[0] + 0.1, x + 0.6))
    #     ax.broken_barh(rang, (x+0.5, 0.5), facecolors='yellow')

    ax.set_ylim(0, len(system._cpus))
    ax.set_yticks(list(range(len(system._cpus))))

    ax.set_xlim(0, max_time*1.1)
    ax.set_xlabel('tacts since start')
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.xaxis.set_major_locator(MultipleLocator(2))

    ax.grid(True, which="both")
    mng = plt.get_current_fig_manager()
    mng.window.showMaximized()
    plt.legend([Rectangle((0, 0), 1, 1, fc="lightgray"),
                Rectangle((0, 0), 1, 1, fc="yellow")],
               ["Regular tasks",
                "Data transfer"])
    plt.show()
