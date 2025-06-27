from .connections import Connections

import networkx as nx


class ConnectionsCompiler:
    def __init__(self, connections: Connections):
        addressed_ports = connections.addressed_ports
        graph = nx.Graph(addressed_ports)
        groups = nx.connected_components(graph)
        self.wire_groups = [
            {connections.elements.get(vx) for vx in group} for group in groups
        ]
