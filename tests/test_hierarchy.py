import unittest

from psymple_connections.connections.hierarchy.addresses import HierarchyAddress, PortHierarchyAddress
from psymple_connections.connections.hierarchy.ported_objects import PortedObjectWithHierarchy

from psymple.build import HIERARCHY_SEPARATOR

class PortedObjectWithHierarchyTest(PortedObjectWithHierarchy):
    def to_data():
        pass

    def compile():
        pass

class TestHierarchyAddresses(unittest.TestCase):
    def test_address_parts(self):
        test_parts = ["A", "B", "C"]
        test_address = HIERARCHY_SEPARATOR.join(test_parts)

        address = HierarchyAddress(test_address)

        address_parts = address.address_parts
        self.assertEqual(address_parts, test_parts)

        base_object = address.base_object
        self.assertEqual(base_object, test_parts[-1])

    def test_common_ancestor(self):
        address_1 = HierarchyAddress("A.B.C")
        address_2 = HierarchyAddress("A.B.D")

        common_ancestor = address_1.get_common_ancestor(address_2)
        self.assertEqual(common_ancestor, "B")

    def test_port_hierarchy_address(self):
        address = PortHierarchyAddress("A.B.C.p")

        port_name = address.port_name
        address_parts = address.address_parts
        self.assertEqual(port_name, "p")
        self.assertEqual(address_parts, ["A", "B", "C"])

        
class TestPortedObjectWithHierarchy(unittest.TestCase):
    def test_set_parent(self):
        X = PortedObjectWithHierarchyTest(name="X")
        Y = PortedObjectWithHierarchyTest(name="Y")

        Y._set_parent(X)

        Y_parent = Y.parent
        self.assertEqual(Y_parent, X)

        X_parent = X.parent
        self.assertEqual(X_parent, None)

    def test_address_no_parent(self):
        X = PortedObjectWithHierarchyTest(name="X")
        address = X.address

        self.assertEqual(address, X.name)

    def test_address(self):
        X = PortedObjectWithHierarchyTest(name="X")
        Y = PortedObjectWithHierarchyTest(name="Y")
        Z = PortedObjectWithHierarchyTest(name="Z")

        Z._set_parent(Y)
        Y._set_parent(X)
        address = Z.address

        self.assertEqual(address, "X.Y.Z")