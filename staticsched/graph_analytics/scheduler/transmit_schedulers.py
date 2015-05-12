class NoAdvanceTransmissionScheduler:
    def schedule_transmits(self, task, m_time, target_cpu):
        max_time = m_time
        for edge in self._dag.edges_to_node(task):
            max_time = max(max_time, self.schedule_transmit(edge, m_time, target_cpu))
        return max_time

    def schedule_transmit(self, edge, m_time, target_cpu):
        source_cpus = self._system.cpus_by_scheduled_task(edge.source.n_id)
        assert len(source_cpus) == 1
        source_cpu = source_cpus[0].cpu_id

        route = self.get_route(m_time, source_cpu, target_cpu)
        if route:
            transmission = self._system.schedule_transmission(route, m_time, edge.source, edge.target, edge.weight)
            m_time = transmission.end_time()
        return m_time


class AdvanceTransmissionScheduler:
    def schedule_transmits(self, task, m_time, target_cpu):
        max_time = m_time
        for edge in self._dag.edges_to_node(task):
            max_time = max(max_time, self.schedule_transmit(edge, m_time, target_cpu))
        return max_time

    def schedule_transmit(self, edge, m_time, target_cpu):
        source_cpus = self._system.cpus_by_scheduled_task(edge.source.n_id)
        assert len(source_cpus) == 1
        source_cpu = source_cpus[0].cpu_id

        scheduled_source_task = source_cpus[0].get_scheduled_task(edge.source.n_id)
        source_task_ready_time = scheduled_source_task.range[1]

        route = self.get_route(source_task_ready_time, source_cpu, target_cpu)
        if route:
            transmission = self._system.schedule_transmission(route, source_task_ready_time, edge.source, edge.target, edge.weight)
            source_task_ready_time = transmission.end_time()
        return source_task_ready_time
