import unittest

from psymple_connections.hierarchy.addresses import HierarchyAddress, PortHierarchyAddress
from psymple_connections.hierarchy.ported_objects import PortedObjectWithHierarchy, CompositePortedObjectWithHierarchy

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

    def test_hierarchy_address_prefix(self):
        address = HierarchyAddress("A.B.C")
        
        # Test prefix not in address
        prefix_1 = "P"
        new_address_1 = address.prefix(prefix_1)
        self.assertEqual(new_address_1.address_parts, ["P", "A", "B", "C"])

        # Test prefix in address, not allowing repetition
        prefix_2 = "B"
        new_address_2 = address.prefix(prefix_2)
        self.assertEqual(new_address_2.address_parts, ["A", "B", "C"])

        # Test prefix in address, allowing repetition
        prefix_3 = "B"
        new_address_3 = address.prefix(prefix_3, allow_repetition=True)
        self.assertEqual(new_address_3.address_parts, ["B", "A", "B", "C"])

    def test_port_hierarchy_address(self):
        address = PortHierarchyAddress("A.B.C.p")

        port_name = address.port_name
        address_parts = address.address_parts
        self.assertEqual(port_name, "p")
        self.assertEqual(address_parts, ["A", "B", "C"])

    def test_port_hierarchy_address_prefix(self):
        address = PortHierarchyAddress("A.B.C.p")

        prefix = "P"
        new_address = address.prefix(prefix)

        self.assertIsInstance(new_address, PortHierarchyAddress)
        self.assertEqual(new_address.address_parts, ["P", "A", "B", "C"])
        self.assertEqual(new_address.port_name, "p")

        
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

class TestCompositePortedObjectWithHierarchy(unittest.TestCase):
    def test_add_child(self):
        X = CompositePortedObjectWithHierarchy(name="X")
        Y = PortedObjectWithHierarchyTest(name="Y")
        X._add_child(Y)

        self.assertDictEqual(X.children, {"Y": Y})
        self.assertEqual(Y.parent, X)

    def test_add_children_on_instantiation(self):
        Y = PortedObjectWithHierarchyTest(name="Y")
        X = CompositePortedObjectWithHierarchy(name="X", children=[Y])

        self.assertDictEqual(X.children, {"Y": Y})
        self.assertEqual(Y.parent, X)

