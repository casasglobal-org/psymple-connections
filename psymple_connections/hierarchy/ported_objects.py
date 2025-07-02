from psymple.build.abstract import PortedObject
from psymple.build import HIERARCHY_SEPARATOR, CompositePortedObject
from .addresses import HierarchyAddress

class PortedObjectWithHierarchy(PortedObject):
    def _set_parent(self, parent: PortedObject):
        self.parent_object = parent

    def get_ancestor_by_address(self, address: HierarchyAddress):
        ancestor_object_name = address.ancestor_object_name
        search_object = self

        while search_object.name != ancestor_object_name:
            try:
                search_object = search_object.parent
            except AttributeError:
                raise Exception(f"Incorrect addressing detected: the ancestor {ancestor_object_name} could not be found for address {address}.")
        return search_object
    
    def get_child_by_address(self, address: HierarchyAddress):
        child_object_name = address.ancestor_object_name
        if hasattr(self, "children"):
            if address in self.children:
                return self.children[address]
        if child_object_name == self.name:
            return self.get_child_by_address(address)
        else:
            try:
                child_object = self.children[child_object_name]
            except (AttributeError, KeyError):
                raise Exception("Child not found")
            return child_object.get_child_by_address(address)


    @property
    def parent(self):
        try:
            parent = self.parent_object
        except AttributeError:
            parent = None
        return parent
    
    @property
    def ancestors(self):
        pass

    def get_truncated_address(self, name: str):
        address = self.address
        while not address.startswith(name):
            address = address.strip()
        return address


    @property
    def address(self):
        try:
            parent_address = self.parent.address
            address = HIERARCHY_SEPARATOR.join([parent_address, self.name])
        except AttributeError:
            address = self.name
        return HierarchyAddress(address)
    
class CompositePortedObjectWithHierarchy(PortedObjectWithHierarchy, CompositePortedObject):
    def _add_child(self, child: PortedObjectWithHierarchy):
        super()._add_child(child)
        child._set_parent(self)