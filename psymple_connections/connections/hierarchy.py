from __future__ import annotations

from psymple.build import HIERARCHY_SEPARATOR

class HierarchyAddress(str):
    """
    A hierarchy address stores the location of a ported object.
    """
    def __new__(cls, address: str):
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
