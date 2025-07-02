from psymple_connections.connections.connection_ported_objects import (
    PortedObjectWithConnections,
    CompositePortedObjectWithConnections
)

from ._ported_objects_for_testing import PortedObjectWithConnectionsTest


class TestPortedObjectWithConnections:
    def test_variable_connections_parsing(self):
              
        P = PortedObjectWithConnectionsTest(
            name="P",
            variable_ports=["u", "v"],
            delay_connection_parsing = True,
        )

        A = PortedObjectWithConnectionsTest(name="A", variable_ports=["u"], variable_connections={"u": "P.u"})
        A.parent_object = P
        B = PortedObjectWithConnectionsTest(name="B", variable_ports=["v"], variable_connections={"v": "P.v"})
        B.parent_object = P

        A._process_temp_variable_connections()
        B._process_temp_variable_connections()

        assert len(A.variable_connections) == 1
        connection_1 = A.variable_connections[0]
        assert connection_1.first_port.address == "P.A.u"
        assert connection_1.second_port.address == "P.u"

        assert len(B.variable_connections) == 1
        connection_2 = B.variable_connections[0]
        assert connection_2.first_port.address == "P.B.v"
        assert connection_2.second_port.address == "P.v"

class TestCompositePortedObjectWithConnections:
    def test_connections_collection(self):
        B = PortedObjectWithConnectionsTest(name="B", variable_ports=["v"])
        C = PortedObjectWithConnectionsTest(name="C", variable_ports=["u"])
        A = CompositePortedObjectWithConnections(name="A", children=[B, C], variable_ports = ["u", "v"], variable_connections={"v": {"A.B.v", "A.C.u"}})
        B.add_variable_connections(v="A.C.u")
        C.add_variable_connections(u="A.B.v")

        A._collect_child_connections()

        for c in A.variable_connections:
            print(c.first_port.address, c.second_port.address)