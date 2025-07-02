from psymple_connections.connections.connection_ported_objects import PortedObjectWithConnections, PortedObjectWithAssignmentsAndConnections
from psymple_connections.hierarchy.ported_objects import PortedObjectWithHierarchy
from psymple.build.abstract import PortedObject

class PortedObjectTest(PortedObject):
    def compile(self):
        pass

    def to_data(self):
        pass

class PortedObjectWithConnectionsTest(PortedObjectTest, PortedObjectWithConnections):
    pass
    
class PortedObjectWithHierarchyTest(PortedObjectTest, PortedObjectWithHierarchy):
    pass

class PortedObjectWithAssignmentsAndConnectionsTest(PortedObjectTest, PortedObjectWithAssignmentsAndConnections):
    pass