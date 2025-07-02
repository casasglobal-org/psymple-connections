import unittest

from psymple_connections.hierarchy.addresses import HierarchyAddress, PortHierarchyAddress
from psymple_connections.hierarchy.ported_objects import PortedObjectWithHierarchy, CompositePortedObjectWithHierarchy

from psymple.build import HIERARCHY_SEPARATOR

from ._ported_objects_for_testing import PortedObjectWithHierarchyTest

class TestHierarchyAddress:
    def test_address_parts(self):
        test_parts = ["A", "B", "C"]
        test_address = HIERARCHY_SEPARATOR.join(test_parts)

        address = HierarchyAddress(test_address)

        address_parts = address.address_parts
        assert address_parts == test_parts

        base_object = address.base_object_name
        assert base_object == test_parts[-1]

    def test_common_ancestor(self):
        address_1 = HierarchyAddress("A.B.C")
        address_2 = HierarchyAddress("A.D.E")

        common_ancestor = address_1.get_common_ancestor(address_2)
        assert common_ancestor == "A"

    def test_common_ancestor_nested(self):
        address_1 = HierarchyAddress("A.B.C")
        address_2 = HierarchyAddress("A.B.D")

        common_ancestor = address_1.get_common_ancestor(address_2)
        assert common_ancestor == "B"

    def test_no_common_ancestor(self):
        address_1 = HierarchyAddress("A.B.C")
        address_2 = HierarchyAddress("D.E.F")

        common_ancestor = address_1.get_common_ancestor(address_2)
        assert common_ancestor == None

    def test_hierarchy_address_prefix(self):
        address = HierarchyAddress("A.B.C")
        
        # Test prefix not in address
        prefix_1 = "P"
        new_address_1 = address.prefix(prefix_1)
        assert new_address_1.address_parts == ["P", "A", "B", "C"]

        # Test prefix in address, not allowing repetition
        prefix_2 = "B"
        new_address_2 = address.prefix(prefix_2)
        assert new_address_2.address_parts == ["A", "B", "C"]

        # Test prefix in address, allowing repetition
        prefix_3 = "B"
        new_address_3 = address.prefix(prefix_3, allow_repetition=True)
        assert new_address_3.address_parts == ["B", "A", "B", "C"]

    def test_hierarchy_address_strip(self):
        address = HierarchyAddress("A.B.C")

        address = address.strip()
        assert address == "B.C"

        address = address.strip()
        assert address == "C"

    def test_port_hierarchy_address(self):
        address = PortHierarchyAddress("A.B.C.p")    

        assert address.port_name == "p"
        assert address.address_parts == ["A", "B", "C"]
        assert address.object_address == "A.B.C"

    def test_port_hierarchy_address_prefix(self):
        address = PortHierarchyAddress("A.B.C.p")

        prefix = "P"
        new_address = address.prefix(prefix)

        assert isinstance(new_address, PortHierarchyAddress)

        assert new_address.address_parts == ["P", "A", "B", "C"]
        assert new_address.port_name == "p"
        assert new_address.object_address == "P.A.B.C"

        
class TestPortedObjectWithHierarchy:
    def test_set_parent(self):
        X = PortedObjectWithHierarchyTest(name="X")
        Y = PortedObjectWithHierarchyTest(name="Y")

        Y._set_parent(X)

        assert Y.parent == X
        
        assert X.parent is None

    def test_address_no_parent(self):
        X = PortedObjectWithHierarchyTest(name="X")

        assert X.address == X.name

    def test_address(self):
        X = PortedObjectWithHierarchyTest(name="X")
        Y = PortedObjectWithHierarchyTest(name="Y")
        Z = PortedObjectWithHierarchyTest(name="Z")

        Z._set_parent(Y)
        Y._set_parent(X)

        assert Y.address == "X.Y"
        assert Z.address == "X.Y.Z"

class TestCompositePortedObjectWithHierarchy:
    def test_add_child(self):
        X = CompositePortedObjectWithHierarchy(name="X")
        Y = PortedObjectWithHierarchyTest(name="Y")
        X._add_child(Y)

        assert X.children == {"Y": Y}
        assert Y.parent == X

    def test_add_children_on_instantiation(self):
        Y = PortedObjectWithHierarchyTest(name="Y")
        X = CompositePortedObjectWithHierarchy(name="X", children=[Y])

        assert X.children == {"Y": Y}
        assert Y.parent == X

