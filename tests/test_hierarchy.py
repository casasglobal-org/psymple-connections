import unittest

from psymple_connections.connections.hierarchy import HierarchyAddress

from psymple.build import HIERARCHY_SEPARATOR

class TestHierarchyAddress(unittest.TestCase):
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

        