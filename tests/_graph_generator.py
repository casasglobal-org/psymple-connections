from psymple_connections.connections.connection_ported_objects import PortedObjectWithConnections, CompositePortedObjectWithConnections
from psymple_connections.hierarchy.addresses import PortHierarchyAddress
import networkx as nx

def build_graphs(obj: PortedObjectWithConnections):
    variable_edges, directed_edges = build_edges(obj)
    variable_graph = nx.Graph()
    variable_graph.add_edges_from(variable_edges)
    parameter_graph = nx.DiGraph()
    parameter_graph.add_edges_from(directed_edges)
    return variable_graph, parameter_graph

def build_edges(obj: PortedObjectWithConnections):
    variable_edges = []
    directed_edges = []
    if isinstance(obj, CompositePortedObjectWithConnections):
        for wire in obj.variable_aggregation_wiring:
            edges = []
            if wire.parent_port:
                parent_port = wire.parent_port.prefix(obj.address)
            else:
                parent_port = PortHierarchyAddress(wire.output_name).prefix(obj.address)
            for port in wire.child_ports:
                child_port = port.prefix(obj.address) 
                edges.append((parent_port, child_port))
            variable_edges += edges

        for wire in obj.directed_wires:
            edges = []
            source_port = wire.source_port.prefix(obj.address)
            for port in wire.destination_ports:
                destination_port = port.prefix(obj.address)
                edges.append((source_port, destination_port))
            directed_edges += edges


        for child in obj.children.values():
            child_variable_edges, child_directed_edges = build_edges(child)
            variable_edges += child_variable_edges
            directed_edges += child_directed_edges
    
    return variable_edges, directed_edges
    