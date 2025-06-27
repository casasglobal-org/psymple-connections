from ..hierarchy.addresses import HierarchyAddress
from .addressed_ports import AddressedPort

class Connection:
    def __init__(self, first_port: AddressedPort, second_port: AddressedPort, object_address: HierarchyAddress):
        self.first_port = first_port
        self.second_port = second_port
        self.object_address = object_address

    def prefix_ports(self, object_name: str, allow_repetition: bool = False):
        new_first_port = self.first_port.prefix_address(object_name, allow_repetition)
        new_second_port = self.second_port.prefix_address(object_name, allow_repetition)
        if (new_first_port.address != self.first_port.address) and (new_second_port.address != self.second_port.address) and (not allow_repetition):
            self.first_port = new_first_port
            self.second_port = new_second_port

    @property
    def addressed_ports(self):
        return {self.first_port.address: self.first_port, self.second_port.address: self.second_port}
        
class Connections(list):
    def __init__(self, *connections: Connection):
        super().__init__()
        self.add_connections(*connections)

    def add_connections(self, *connections: Connection):
        self += connections    

    def prefix_connections(self, object_name: str, allow_repetition: bool = False):
        for connection in self:
            connection.prefix_ports(object_name, allow_repetition)

    @property
    def addressed_ports(self):
        return [connection.addressed_ports for connection in self]

    @property
    def elements(self):
        return dict(pair for dicts in self.addressed_ports for pair in dicts.items())
    
    @property
    def view_ports(self):
        return [list(connection.addressed_ports.keys()) for connection in self]
    
"""
Let's say I have D.v -> A.H.J.K.v (in D)
This should rise to C.D.v -> A.H.J.K.v in (C)
Currently, it rises to C.D.v -> C.A.H.J.K.v in (C). not good. 

The use case for prefixing is only for lower relative connections. Can we somehow mitigate that?

"""