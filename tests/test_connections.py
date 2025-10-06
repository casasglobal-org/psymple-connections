from psymple_connections.connections.connections import Connection, Connections
from psymple_connections.connections.addressed_ports import AddressedPort
from psymple_connections.hierarchy.addresses import PortHierarchyAddress, HierarchyAddress

class TestAddressedPort:
    def test_address_parsing(self):
        str_address = "A.B.C.p"
        obj_address = PortHierarchyAddress(str_address)
        P = AddressedPort("p", str_address)
        Q = AddressedPort("q", obj_address)

        assert P.address == Q.address

    def test_address_prefixing(self):
        P = AddressedPort("p", "A.B.C.p")
        prefixed = P.prefix_address("X")

        assert prefixed.address == "X.A.B.C.p"

class TestConnection:
    def test_prefix_ports(self):
        P = AddressedPort("p", "A.B.C.p")
        Q = AddressedPort("q", "C.D.q")
        
        # Test 1 - prefix by existing object name
        C = Connection(P, Q)
        prefix = "B"
        C.prefix_ports(prefix)

        assert C.first_port.address == "A.B.C.p"
        assert C.second_port.address == "C.D.q"

        # Test 2 - prefix by other object name
        prefix = "X"
        C.prefix_ports(prefix)

        assert C.first_port.address == "X.A.B.C.p"
        assert C.second_port.address == "X.C.D.q"

    def test_addresses(self):
        P = AddressedPort("p", "A.B.C.p")
        Q = AddressedPort("q", "C.D.q")

        C = Connection(P, Q)

        assert C.addressed_ports == {"A.B.C.p": P, "C.D.q": Q}

class TestConnections:
    def test_add_connections(self):
        P = AddressedPort("p", "A.B.C.p")
        Q = AddressedPort("q", "A.B.C.q")
        R = AddressedPort("r", "A.B.C.r")

        C_1 = Connection(P, Q)
        C_2 = Connection(P, R)
        C_3 = Connection(Q, R)

        C = Connections(C_1, C_2)

        assert C == [C_1, C_2]

        C.add_connections(C_3)

        assert C == [C_1, C_2, C_3]

    def test_prefix_connections(self):
        P = AddressedPort("p", "A.B.C.p")
        Q = AddressedPort("q", "A.B.C.q")

        C_1 = Connection(P, Q)

        C = Connections(C_1)

        C.prefix_connections("X")

        assert C[0].first_port.address == "X.A.B.C.p"
        assert C[0].second_port.address == "X.A.B.C.q"

    def test_addresses(self):
        P = AddressedPort("p", "A.B.C.p")
        Q = AddressedPort("q", "A.B.C.q")
        R = AddressedPort("r", "A.B.C.r")

        C_1 = Connection(P, Q)
        C_2 = Connection(P, R)
        C_3 = Connection(Q, R)

        C = Connections(C_1, C_2, C_3)

        assert C.addressed_ports == [{"A.B.C.p": P, "A.B.C.q": Q}, {"A.B.C.p": P, "A.B.C.r": R}, {"A.B.C.q": Q, "A.B.C.r": R}]
        assert C.view_ports == [["A.B.C.p", "A.B.C.q"], ["A.B.C.p", "A.B.C.r"], ["A.B.C.q", "A.B.C.r"]]
        assert C.elements == {"A.B.C.p": P, "A.B.C.q": Q, "A.B.C.r": R}