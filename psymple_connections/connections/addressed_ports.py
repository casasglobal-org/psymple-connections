from psymple.build.ports import Port, InputPort, OutputPort, VariablePort
from ..hierarchy.addresses import HierarchySeparatedStr, PortHierarchyAddress, HierarchyAddress

from psymple.build import HIERARCHY_SEPARATOR

class BaseOutputPort(OutputPort):
    pass

class AddressedPort(Port):
    def __init__(self, name: str, address: HierarchySeparatedStr|PortHierarchyAddress, description: str = ""):
        super().__init__(name, description)
        self.address = self._parse_address(address)

    def _parse_address(self, address):
        if isinstance(address, (str, HierarchySeparatedStr)):
            return PortHierarchyAddress(address)
        elif isinstance(address, PortHierarchyAddress):
            return address
        else:
            raise TypeError(f"Address input must be of type {type(HierarchySeparatedStr)} or {type(PortHierarchyAddress)}, not {type(address)}")

    def prefix_address(self, name: str, allow_repetition: bool = False):
        new_address = self.address.prefix(name, allow_repetition)
        return type(self)(self.name, new_address, self.description)

    def strip_address(self):
        new_address = self.address.strip()
        return type(self)(self.name, new_address, self.description)

    def __repr__(self):
        return self.address

class AddressedVariablePort(AddressedPort):
    @classmethod
    def from_port(cls, port: Port, object_address: HierarchySeparatedStr|HierarchyAddress, **kwargs):
        port_address = PortHierarchyAddress(HIERARCHY_SEPARATOR.join([object_address, port.name]))
        if not isinstance(port, VariablePort):
            raise TypeError(f"Unrecognised port type for variable port: {type(port)} for port {port_address}.")
        return cls(port.name, port_address, port.description, **kwargs)

class AddressedParameterPort(AddressedPort):
    @classmethod
    def from_port(cls, port: Port, object_address: HierarchySeparatedStr|HierarchyAddress, **kwargs):
        port_address = PortHierarchyAddress(HIERARCHY_SEPARATOR.join([object_address, port.name]))
        if isinstance(port, InputPort):
            port_class = AddressedInputPort
        elif isinstance(port, OutputPort):
            if isinstance(port, BaseOutputPort):
                port_class = AddressedBaseOutputPort
            else:
                port_class = AddressedOutputPort
        else:
            raise TypeError(f"Unrecognised port type for parameter port: {type(port)} for port {port_address}.")
        return port_class(port.name, port_address, port.description, **kwargs)
    
class AddressedInputPort(AddressedParameterPort, InputPort):
    def __init__(self, name: str, address: PortHierarchyAddress, description: str = "", default_value = None):
        AddressedParameterPort.__init__(self, name, address, description)
        self.default_value = default_value 

class AddressedOutputPort(AddressedParameterPort):
    pass

class AddressedBaseOutputPort(AddressedOutputPort):
    pass