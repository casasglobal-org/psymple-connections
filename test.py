from psymple_connections.connections.connection_ported_objects import PortedObjectWithConnections, CompositePortedObjectWithConnections
from psymple_connections.connections.compiler import ConnectionsCompiler
from psymple_connections.hierarchy.addresses import HierarchyAddress, PortHierarchyAddress
from psymple_connections.connections.wire_groups import ParameterWireGroup

class PortedObjectWithConnectionsTest(PortedObjectWithConnections):
    def to_data(self):
        pass

    def compile(self):
        pass

variable_ports = ["u","v","w","x","y"]
input_ports = ["a", "b", "c", "d", "e"]
output_ports = ["p", "q", "r", "s", "t"]


""" TEST 1
D,E,G,K = (PortedObjectWithConnectionsTest(name=name, variable_ports=variable_ports) for name in ["D", "E", "G", "K"])
A,B,C,F,J,H = (CompositePortedObjectWithConnections(name=name, variable_ports=variable_ports) for name in ["A", "B", "C", "F", "J", "H"])
C.add_children(D,E)
F.add_children(G)
B.add_children(C,F)
J.add_children(K)
H.add_children(J)
A.add_children(B,H)

D.add_variable_connections(v={"A.H.J.K.v", "A.B.F.v"})
E.add_variable_connections(v="A.B.v")
A.add_variable_connections(v="A.H.J.v")
C.add_variable_connections(v="B.v")
H.add_variable_connections(v="H.J.v")
"""

""" TEST 2 """
C,D,G,F,J,K = (PortedObjectWithConnectionsTest(name=name, variable_ports=variable_ports, input_ports=input_ports, output_ports=output_ports) for name in ["C", "D", "G", "F", "J", "K"])
A,B,E,H = (CompositePortedObjectWithConnections(name=name, variable_ports=variable_ports, input_ports=input_ports, output_ports=output_ports) for name in ["A", "B", "E", "H"])
B.add_children(C,D)
E.add_children(F,G)
H.add_children(J,K)
A.add_children(B,E,H)

print(H.children)

C.add_variable_connections(v={"A.v", "A.H.J.v"})
H.add_variable_connections(v={"H.J.v", "A.E.v"})
F.add_variable_connections(w={"E.w", "A.B.C.w"})
H.add_variable_connections(w={"A.E.w"})
B.add_variable_connections(u="B.C.u")
C.add_variable_connections(u="B.D.u")
G.add_variable_connections(x="E.F.x")
A.add_variable_connections(y={"A.H.y", "A.H.J.y"})


C.add_output_connections(q={"B.q", "B.D.a"})
C.add_input_connections(a="A.a", b="A.E.F.p")
A.add_output_connections(c={"A.B.C.c", "A.E.c", "A.H.c", "A.H.J.c"})
J.add_output_connections(r={"H.r", "A.E.e", "A.r", "A.B.D.e"})
G.add_input_connections(d="E.F.s")

X = CompositePortedObjectWithConnections(name="X", children=[A])

#TESTING

obj = A
obj._collect_child_connections()

print(obj.parameter_connections.view_ports)

handler = ConnectionsCompiler(obj.parameter_connections)

obj._process_connections("parameter", handler.wire_groups)
print(handler.wire_groups)

print([ParameterWireGroup(*group).root for group in handler.wire_groups])

handler = ConnectionsCompiler(obj.variable_connections)
obj._process_connections("variable", handler.wire_groups)

