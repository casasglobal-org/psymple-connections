"""
These tests aim to test psymple-connections viewed as a start-to-finish package, taking user inputs
and returning psymple objects.

Eventually, these tests will be generalised to support Hypothesis testing.

Since psymple-connections is an interface to producing directed and variable wires in psymple, the aim
is to decode and check the graph object implied by these wires in the created composite ported objects.
"""

from ._ported_objects_for_testing import PortedObjectWithAssignmentsAndConnectionsTest
from psymple_connections.connections.connection_ported_objects import (
    CompositePortedObjectWithConnections,
    PortedObjectWithAssignmentsAndConnections,
)
from psymple_connections.connections.connections import Connection, Connections
from psymple_connections.connections.addressed_ports import (
    AddressedInputPort,
    AddressedOutputPort,
    AddressedBaseOutputPort,
    AddressedVariablePort,
)

from ._graph_generator import build_graphs
import networkx as nx


input_ports = ["a", "b", "c", "d"]
output_ports = ["p", "q", "r", "s"]
variable_ports = ["u", "v", "x", "y"]

# BASE OBJECTS

base_objects = ["C1", "C3", "D1", "D2", "D3", "D4"]

C1, C3, D1, D2, D3, D4 = (
    PortedObjectWithAssignmentsAndConnectionsTest(
        name=name,
        input_ports=input_ports,
        output_ports=output_ports,
        variable_ports=variable_ports,
    )
    for name in base_objects
)

# COMPOSITE OBJECTS

composite_objects = ["A", "B1", "B2", "C2", "C4"]

A, B1, B2, C2, C4 = (
    CompositePortedObjectWithConnections(
        name=name,
        input_ports=input_ports,
        output_ports=output_ports,
        variable_ports=variable_ports,
    )
    for name in composite_objects
)

A.add_children(B1, B2)
B1.add_children(C1, C2)
B2.add_children(C3, C4)
C2.add_children(D1, D2)
C4.add_children(D3, D4)

# CONNECTIONS

## Parameter connections

test_parameter_connections = Connections()

### Base output to composite output (p ports)

# D2.add_output_connections(p={"C2.p", "B1.p"})

test_parameter_connections.add_connections(
    Connection(
        AddressedBaseOutputPort("p", "A.B1.C2.D2.p"),
        AddressedOutputPort("p", "A.B1.C2.p"),
    ),
    Connection(
        AddressedBaseOutputPort("p", "A.B1.C2.D2.p"),
        AddressedOutputPort("p", "A.B1.p"),
    ),
)

### Composite input to base input (a ports)

#D4.add_input_connections(a="A.a")
#B2.add_input_connections(a="A.a")

test_parameter_connections.add_connections(
    Connection(
        AddressedInputPort("a", "A.a"),
        AddressedInputPort("a", "A.B2.a"),
    ),
    Connection(
        AddressedInputPort("a", "A.a"),
        AddressedInputPort("a", "A.B2.C4.D4.a"),
    ),
)

### Base output to composite input (b/q ports)

#C1.add_output_connections(q="B1.C2.b")
#B2.add_input_connections(b="A.B1.C1.q")

test_parameter_connections.add_connections(
    Connection(
        AddressedBaseOutputPort("q", "A.B1.C1.q"),
        AddressedInputPort("b", "A.B1.C2.b"),
    ),
    Connection(
        AddressedBaseOutputPort("q", "A.B1.C1.q"),
        AddressedInputPort("b", "A.B2.b"),
    )
)

### Base output to base input (c/r ports)

#D1.add_input_connections(c="B1.C1.r")
#C1.add_output_connections(r="A.B1.C4.D3.c")

test_parameter_connections.add_connections(
    Connection(
        AddressedBaseOutputPort("r", "A.B1.C1.r"),
        AddressedInputPort("c", "A.B1.C2.D1.c"),
    ),
    Connection(
        AddressedBaseOutputPort("r", "A.B1.C1.r"),
        AddressedInputPort("c", "A.B2.C4.D3.c"),
    )
)

### Composite input to composite input (d ports)

#B1.add_input_connections(d="A.d")
#C4.add_input_connections(d="A.d")

test_parameter_connections.add_connections(
    Connection(
        AddressedInputPort("d", "A.d"),
        AddressedInputPort("d", "A.B1.d"),
    ),
    Connection(
        AddressedInputPort("d", "A.d"),
        AddressedInputPort("d", "A.B2.C4.d")
    )
)

A.parameter_connections = test_parameter_connections

## Variable connections

test_variable_connections = Connections()

# Variable to variable (u ports)

#C1.add_variable_connections(u={"B1.C2.D1.u", "A.B2.C3.u", "A.B2.C4.u"})

test_variable_connections.add_connections(
    Connection(
        AddressedVariablePort("u", "A.B1.C1.u"),
        AddressedVariablePort("u", "A.B1.C2.D1.u")
    ),
    Connection(
        AddressedVariablePort("u", "A.B1.C1.u"),
        AddressedVariablePort("u", "A.B2.C3.u")
    ),
    Connection(
        AddressedVariablePort("u", "A.B1.C1.u"),
        AddressedVariablePort("u", "A.B2.C4.u")
    ),
)

# Variable to variable, with ancestor composite variable (v ports)

#A.add_variable_connections(v={"B1.C2.D2.v", "B2.C4.D3.v"})

test_variable_connections.add_connections(
    Connection(
        AddressedVariablePort("v", "A.v"),
        AddressedVariablePort("v", "A.B1.C2.D2.v")
    ),
    Connection(
        AddressedVariablePort("v", "A.v"),
        AddressedVariablePort("v", "A.B2.C4.D3.v")
    ),
)

# Variable to ancestor variable (x ports)

#B1.add_variable_connections(x={"B1.C2.x", "B1.C2.D1.x"})

test_variable_connections.add_connections(
    Connection(
        AddressedVariablePort("x", "A.B1.x"),
        AddressedVariablePort("x", "A.B1.C2.x")
    ),
    Connection(
        AddressedVariablePort("x", "A.B1.x"),
        AddressedVariablePort("x", "A.B1.C2.D1.x")
    ),
)

# Composite variable to composite variable (y ports)

#C1.add_variable_connections(y="B1.C2.D1.y")
#B2.add_variable_connections(y="B2.C4.D3.y")
#D1.add_variable_connections(y="A.B2.C4.D3.y")

test_variable_connections.add_connections(
    Connection(
        AddressedVariablePort("y", "A.B1.C1.y"),
        AddressedVariablePort("y", "A.B1.C2.D1.y")
    ),
    Connection(
        AddressedVariablePort("y", "A.B2.y"),
        AddressedVariablePort("y", "A.B2.C4.D3.y")
    ),
    Connection(
        AddressedVariablePort("y", "A.B1.C2.D1.y"),
        AddressedVariablePort("y", "A.B2.C4.D3.y")
    ),
)

A.variable_connections = test_variable_connections


class TestScenario:
    def test_compile(self):
        A.pre_compile()
        variable_graph, parameter_graph = build_graphs(A)
        assert nx.is_forest(variable_graph)
        assert nx.is_forest(parameter_graph)

        for test_connections, graph in zip(
            [test_parameter_connections, test_variable_connections],
            [parameter_graph, variable_graph]
        ):
            for pair in test_connections.view_ports:
                paths = list(
                    nx.all_simple_edge_paths(graph, *pair)
                )
                assert len(paths) == 1
            
