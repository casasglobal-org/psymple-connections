from psymple.build.abstract import PortedObject
from psymple.build import HIERARCHY_SEPARATOR
from .addresses import HierarchyAddress

class PortedObjectWithHierarchy(PortedObject):
    def _set_parent(self, parent: PortedObject):
        self.parent_object = parent

    @property
    def parent(self):
        try:
            parent = self.parent_object
        except AttributeError:
            parent = None
        return parent

    @property
    def address(self):
        try:
            parent_address = self.parent.address
            address = HIERARCHY_SEPARATOR.join([parent_address, self.name])
        except AttributeError:
            address = self.name
        return HierarchyAddress(address)