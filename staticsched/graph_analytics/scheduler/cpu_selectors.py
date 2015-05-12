import random


def cpu_by_priority(cpus, cpu_priorities):
    return sorted(cpus, key=lambda cpu: cpu_priorities.index(cpu))[0]


class PriorityCPUSelector:
    def choose_cpu(self, m_time, task):
        cpus = self._system.free_alu_cpus(m_time)
        if cpus:
            return cpu_by_priority(cpus, self.cpu_priorities())


class NearestTransferCPUSelector:
    def choose_cpu(self, m_time, task):
        free_cpus = self._system.free_alu_cpus(m_time)
        if free_cpus:
            # parent_tasks = self._dag.get_neighbours(task, forward=False)
            transfers = self._dag.edges_to_node(task)

            cpus_transfer_time = {}
            for target_cpu in free_cpus:
                transfer_times = {}
                for edge in transfers:
                    source_cpu = self._system.cpus_by_scheduled_task(edge.source.n_id)[0].cpu_id
                    route = self.get_route(m_time, source_cpu, target_cpu)

                    transfer_time_from_cpu = transfer_times.get(source_cpu, 0)
                    transfer_times[source_cpu] = transfer_time_from_cpu + len(route) * edge.weight
                cpus_transfer_time[target_cpu] = max(transfer_times.values(), default=0)

            min_transfer_time = min(cpus_transfer_time.values())
            cpus_with_min_transfer_time = [cpu_id for cpu_id, transfer_time in cpus_transfer_time.items()
                                           if transfer_time == min_transfer_time]

            return cpu_by_priority(cpus_with_min_transfer_time, self.cpu_priorities())
            # return random.choice(cpus_with_min_transfer_time)


class ModellingTransferCPUSelector:
    def choose_cpu(self, m_time, task):
        cpu_times = {}
        for cpu in self._system._cpus:
            ready_time = self.schedule_transmits(task, m_time, cpu)
            scheduled_task = self._system.schedule_calculation(task.n_id, ready_time, task.weight, cpu)
            cpu_times[cpu] = scheduled_task.range[0]
            self._system.cancel_session()

        nearest_time = min(cpu_times.values())
        best_cpus = [cpu for cpu in cpu_times.keys() if cpu_times[cpu] == nearest_time]
        return cpu_by_priority(best_cpus, self.cpu_priorities())
