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
    def ancestor_object_name(self):
        return self.address_parts[0]

    @property
    def base_object_name(self):
        return self.address_parts[-1]
    
    def get_common_ancestor(self, address: HierarchyAddress):
        common_ancestors = [A for A in self.address_parts if A in address.address_parts]
        if common_ancestors:
            return common_ancestors[-1]
        else:
            return None
    
    def prefix(self, name: str, allow_repetition: bool = False):
        """
        Returns a new address formed as `self`, prefixed with `name`.

        Args:
            name: name to prefix the address with
            allow_repetition: if False, the address will not be prefixed if `name` is already an element of `self.address_parts`. 
        """
        if name in self.address_parts and not allow_repetition:
            return self
        else:
            new_address = HIERARCHY_SEPARATOR.join([name, self])
            return type(self)(new_address)
        
    def strip(self):
        new_address = self.split(HIERARCHY_SEPARATOR, 1)[1]
        return type(self)(new_address)


class PortHierarchyAddress(HierarchyAddress):
    """
    A hierarchy address which references the port of a hierarchy object, for example "A.B.C.p". 
    """
    def __new__(cls, address: HierarchySeparatedStr):
        obj = super().__new__(cls, address)
        obj.port_name = obj.address_parts.pop(-1)
        obj.object_address = HierarchyAddress(HIERARCHY_SEPARATOR.join(obj.address_parts))
        return obj