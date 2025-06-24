from __future__ import annotations

from psymple.build import HIERARCHY_SEPARATOR

from typing import NewType

HierarchySeparatedStr = NewType("HierarchySeparatedStr", str)
"""A string consisting of components separated by HIERARCHY_SEPARATOR, by default '.'."""


class HierarchyAddress(str):
    """
    A hierarchy address stores the location of a ported object, for example "A.B.C".
    """
    def __new__(cls, address: HierarchySeparatedStr):
        obj = super().__new__(cls, address)
        obj.address_parts = address.split(HIERARCHY_SEPARATOR)
        return obj

    def _validate_hierarchy_separator(self):
        pass 

    @property
    def base_object(self):
        return self.address_parts[-1]
    
    def get_common_ancestor(self, address: HierarchyAddress):
        common_ancestors = [A for A in self.address_parts if A in address.address_parts]
        return common_ancestors[-1]


class PortHierarchyAddress(HierarchyAddress):
    """
    A hierarchy address which references the port of a hierarchy object, for example "A.B.C.p". 
    """
    def __new__(cls, address: HierarchySeparatedStr):
        obj = super().__new__(cls, address)
        obj.port_name = obj.address_parts.pop(-1)
        return obj