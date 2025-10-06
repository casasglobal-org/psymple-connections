from .addressed_ports import (
    AddressedPort,
    AddressedInputPort,
    AddressedOutputPort,
    AddressedVariablePort,
    AddressedBaseOutputPort,
)

from abc import ABC, abstractmethod
from typing import TypedDict
from itertools import groupby


class WireGroupError(Exception):
    pass


class WireGroupHierarchy(TypedDict):
    locals: dict
    by_child: dict

class SplitGroupHierarchy(TypedDict):
    child_ports: list
    descendent_ports: list


class WireGroup(ABC):
    def __init__(
        self,
        *ports: AddressedPort,
        root=None,
        create_root=True,
    ):
        self._validate_ports(ports)
        self.ports = ports
        self.port_hierarhcy = self._organise_by_hierarchy(ports)
        print("HIERARCHY", self.port_hierarhcy, create_root)
        if not root and create_root:
            print("CREATING ROOT")
            root = self._get_root()
        print("WIRE ROOT", root)
        self.root = root

    def _organise_by_hierarchy(self, ports: tuple):
        port_address_parts = {port: port.address.address_parts for port in ports}
        local_ports = [
            port
            for port, address_parts in port_address_parts.items()
            if len(address_parts) == 1
        ]
        descendent_ports = [
            port
            for port, address_parts in port_address_parts.items()
            if len(address_parts) > 1
        ]

        organised = WireGroupHierarchy(
            locals=local_ports, by_child=self._split_by_child(descendent_ports)
        )
        return organised

    def _split_by_child(self, ports: list):
        sort_function = lambda port: port.address.address_parts[1]
        sorted_ports = sorted(ports, key=sort_function)
        ports_split_by_child = {
            child_name: list(ports)
            for child_name, ports in groupby(sorted_ports, sort_function)
        }

        ports_hierarchically_split_by_child = {}

        for child_name, ports in ports_split_by_child.items():
            child_ports = [
                port for port in ports if len(port.address.address_parts) == 2
            ]
            descendent_ports = [
                port for port in ports if len(port.address.address_parts) > 2
            ]
            ports_hierarchically_split_by_child.update(
                {
                    child_name: SplitGroupHierarchy(child_ports=child_ports, descendent_ports=descendent_ports)
                }
            )

        return ports_hierarchically_split_by_child

    def strip_port_addresses(self):
        """
        Remove the first part from every port address.
        """
        new_ports = [port.strip_address() for port in self.ports]
        new_root = None
        if self.root:
            new_root = self.root.strip_address()
        return type(self)(*new_ports, root=new_root)

    @abstractmethod
    def _validate_ports(self, ports):
        pass

    @abstractmethod
    def _get_root(self):
        pass


class ParameterWireGroup(WireGroup):
    def _get_root(self):
        ports = self.ports
        output_ports = [port for port in ports if isinstance(port, AddressedOutputPort)]
        if not output_ports:
            # If there are no output ports, the root must be the only local port.
            # BUG: This is wrong, a wire can go between descendents without being local.
            # Temp fix made.
            local_ports = self.port_hierarhcy.get("locals")
            number_local_ports = len(local_ports)
            if number_local_ports == 0:
                return None
                raise WireGroupError(
                    f"The parameter wire connecting ports {self.ports} has no local ports, "
                    f"could not determine a root."
                )
            if number_local_ports == 1:
                return local_ports[0]
            else:
                raise WireGroupError(
                    f"The parameter wire connecting ports {self.ports} has {number_local_ports} detected "
                    f"roots: {local_ports}. Exactly one root is allowed."
                )
        else: 
            # Find the unique base output port, or raise an error if none or more than one is found.
            # TODO: This algo is junk. What do?
            hierarchy_child_ports = self.port_hierarhcy.get("by_child")
            base_output_ports = []
            for split_ports in hierarchy_child_ports.values():
                child_ports = split_ports.get("child_ports")
                descendent_ports = split_ports.get("descendent_ports")
                all_ports = child_ports + descendent_ports
                child_base_output_ports = [port for port in all_ports if isinstance(port, AddressedBaseOutputPort)]
                base_output_ports += child_base_output_ports

            number_base_output_ports = len(base_output_ports)
            if number_base_output_ports == 0:
                #return None
                raise WireGroupError(
                    f"The parameter wire connecting ports {self.ports} has no base ports. "
                    f"Could not determine a root."
                )
            if number_base_output_ports == 1:
                return base_output_ports[0]
            else:
                raise WireGroupError(
                    f"The parameter wire connecting ports {self.ports} has {number_base_output_ports} detected "
                    f"roots: {base_output_ports}. Exactly one root is allowed."
                )

    def _validate_ports(self, ports):
        for port in ports:
            if not isinstance(port, (AddressedInputPort, AddressedOutputPort)):
                raise WireGroupError(
                    f"The parameter wire connecting ports {ports} connects to port {port} of type {type(port)}."
                )
        


class VariableWireGroup(WireGroup):
    def _get_root(self):
        """
        The root of a variable wire group is always a local port, in which case only one can exist.
        If there are no local ports, the wire group has no root.
        """
        local_ports = self.port_hierarhcy.get("locals")
        number_local_ports = len(local_ports)
        if number_local_ports == 0:
            return None
        elif number_local_ports == 1:
            return local_ports[0]
        else:
            raise WireGroupError(
                f"The variable wire connecting ports {self.ports} has {number_local_ports} detected "
                f"roots: {local_ports}. At most one root is allowed."
            )

    def _validate_ports(self, ports):
        for port in ports:
            if not isinstance(port, AddressedVariablePort):
                raise WireGroupError(
                    f"The variable wire connecting ports {ports} connects to "
                    f" port {port} of type {type(port)}."
                )
