from psymple_connections.connections.connection_ported_objects import (
    PortedObjectWithConnections,
    CompositePortedObjectWithConnections
)

class PortedObjectWithConnectionsTest(PortedObjectWithConnections):
    def compile(self):
        pass

    def to_data(self):
        pass


class TestPortedObjectWithConnections:
    def test_variable_connections_parsing(self):
        variable_connections = {"u": "A.B.C.u", "v": "A.B.C.v"}
        P = PortedObjectWithConnectionsTest(
            name="P",
            variable_ports=["u", "v"],
            variable_connections=variable_connections,
        )

        assert len(P.variable_connections) == 2

        connection_1 = P.variable_connections[0]
        assert connection_1.first_port.address == "P.u"
        assert connection_1.second_port.address == "A.B.C.u"

        connection_2 = P.variable_connections[1]
        assert connection_2.first_port.address == "P.v"
        assert connection_2.second_port.address == "A.B.C.v"

class TestCompositePortedObjectWithConnections:
    def test_connections_collection(self):
        B = PortedObjectWithConnectionsTest(name="B", variable_ports=["v"], variable_connections={"v": "A.C.v"})
        C = PortedObjectWithConnectionsTest(name="C", variable_ports=["u"], variable_connections={"u": "A.D.u"})
        A = CompositePortedObjectWithConnections(name="A", children=[B, C], variable_ports = ["u", "v"], variable_connections={"v": {"A.B.v", "A.C.u"}})

        A.collect_child_connections()

        for c in A.variable_connections:
            print(c.first_port.address, c.second_port.address)