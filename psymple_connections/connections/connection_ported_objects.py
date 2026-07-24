from ..hierarchy.ported_objects import (
    PortedObjectWithHierarchy,
    CompositePortedObjectWithHierarchy,
)
from ..hierarchy.addresses import PortHierarchyAddress, HierarchySeparatedStr
from .connections import Connections, Connection, TemporaryConnection
from .addressed_ports import (
    AddressedVariablePort,
    AddressedParameterPort,
    AddressedInputPort,
    AddressedOutputPort,
    BaseOutputPort,
)
from .compiler import ConnectionsCompiler
from .wire_groups import VariableWireGroup, ParameterWireGroup

from psymple.build import PortedObjectData, HIERARCHY_SEPARATOR
from psymple.build.abstract import PortedObject, PortedObjectWithAssignments
from psymple.build.ports import InputPort, OutputPort, VariablePort

#from psymple_visualise import psympleGraph

from typing import TypedDict, Any
from enum import Enum

# TODO: DeepDiff is a good library to look at, should make an issue


class AddressingError(Exception):
    pass


class ConnectionTypes(TypedDict):
    variable: Any
    parameter: Any


ADDRESSED_PORT_CLASSES = ConnectionTypes(
    variable=AddressedVariablePort,
    parameter=AddressedParameterPort,
)

WIRE_GROUP_CLASSES = ConnectionTypes(
    variable=VariableWireGroup,
    parameter=ParameterWireGroup,
)


# TODO: Add to psymple
class PortTypes(Enum):
    INPUT = InputPort
    OUTPUT = OutputPort
    VARIABLE = VariablePort


class DummyTypes(Enum):
    INPUT = "input"
    OUTPUT = "output"
    VARIABLE = "variable"
    INTERNAL_VARIABLE = "internal_variable"


class PortedObjectWithDummyPorts(PortedObject):
    def __init__(
        self,
        dummy_port_prefix="dummy_",
        **ported_object_kwargs,
    ):
        self.dummy_numbers = {
            type: {"name": dummy_port_prefix + type.value, "value": 1}
            for type in DummyTypes
        }
        super().__init__(**ported_object_kwargs)

    def add_dummy_port(self, type):
        dummy_data = self.dummy_numbers.get(type)
        dummy_id = dummy_data.get("name")
        dummy_number = dummy_data.get("value")
        dummy_name = f"{dummy_id}_{dummy_number}"

        if type == DummyTypes.INPUT:
            self.add_input_ports(dummy_name)
        elif type == DummyTypes.OUTPUT:
            self.add_output_ports(dummy_name)
        elif type == DummyTypes.VARIABLE:
            self.add_variable_ports(dummy_name)

        self.dummy_numbers[type]["value"] += 1
        return dummy_name


class PortedObjectWithConnections(
    PortedObjectWithDummyPorts, PortedObjectWithHierarchy
):
    def __init__(
        self,
        inputs: dict = {},
        output_connections: dict = {},
        variable_connections: dict = {},
        delay_connection_parsing: bool = True,
        **ported_object_kwargs,
    ):
        super().__init__(**ported_object_kwargs)
        self.variable_connections = Connections()
        self.parameter_connections = Connections()
        self._temp_variable_connections = set()
        self._temp_parameter_connections = set()
        self.add_variable_connections(delay_connection_parsing, **variable_connections)
        self.add_input_connections(delay_connection_parsing, **inputs)
        self.add_output_connections(delay_connection_parsing, **output_connections)

    def _parse_connections(
        self,
        type: str,
        connections: set[TemporaryConnection],
    ):
        """
        NOTE: Connections of the form {"v": {A1, A2}, "u": {B1, B2}}
        TODO: How do I validate the connection entries?
        """
        connections_list = []
        AddressedPortClass = ADDRESSED_PORT_CLASSES.get(type)
        for temp_connection in connections:
            source = temp_connection.port
            destinations = temp_connection.connections
            options = temp_connection.options
            if isinstance(destinations, str):
                destinations = {destinations}
            source_port = self._get_port_by_name(source, type=type)
            if not source_port:
                raise NameError(
                    f"Error in creating connection between {source} and {destinations} in {self.address}: "
                    f"port {source} is not a port of {self.address}."
                )
            source_port_expected_type = options.get("port_type").value
            if not isinstance(source_port, source_port_expected_type):
                raise TypeError(
                    f"Error in creating connection between {source} and {destinations} in {self.address}: "
                    f"port {source} in {self.address} is not of type {source_port_expected_type}, but a "
                    f"{type(source_port)}."
                )
            for destination in destinations:
                port_address = PortHierarchyAddress(destination)
                try:
                    common_ancestor = self.get_ancestor_by_address(port_address)
                except:
                    raise AddressingError(
                        f"Incorrect addressing detected from {self.address}: the destintion "
                        f"port {port_address} could not be found for source {source}"
                    )

                addressed_source_port = AddressedPortClass.from_port(
                    source_port, self.get_truncated_address(common_ancestor.name)
                )

                if isinstance(addressed_source_port, AddressedInputPort):
                    overwrite = options.get("overwrite", False)
                    if (value := addressed_source_port.default_value is not None) and (
                        not overwrite
                    ):
                        raise ValueError(
                            f"Cannot connect to input port {addressed_source_port.name} in "
                            f"{self.address} since it already has a default value {addressed_source_port.default_value}"
                        )
                    source_port.default_value = addressed_source_port.address
                # Destination parsing
                try:
                    destination_object = common_ancestor._resolve_destination(
                        port_address.object_address
                    )
                except Exception as e:
                    raise AddressingError(
                        f"Couldn't create a connection from {source} to {destination} in {self.address}: {e}"
                    )
                destination_port = destination_object._get_port_by_name(
                    port_address.port_name,
                    type=type,
                )
                if not destination_port:
                    raise AddressingError(
                        f"Port {port_address.port_name} in object {destination_object.address} not found."
                    )
                addressed_destination_port = AddressedPortClass.from_port(
                    destination_port,
                    destination_object.get_truncated_address(common_ancestor.name),
                )
                if isinstance(addressed_destination_port, AddressedInputPort) and (
                    isinstance(addressed_source_port, AddressedOutputPort)
                ):
                    # If the source is an output port (this is an output connection), we need to
                    # set the default value at the input port. This will overwrite any non-connection 
                    # default value.
                    overwrite = options.get("overwrite", True)
                    """ DEBUG 
                    print(
                        "HERE",
                        addressed_source_port.address,
                        addressed_destination_port.address,
                        addressed_destination_port.default_value,
                        overwrite,
                    )
                    """
                    if (
                        value := addressed_destination_port.default_value is not None
                    ) and (not overwrite):
                        if isinstance(value, str) and HIERARCHY_SEPARATOR in value:
                            raise ValueError(
                                f"Cannot connect to input port {addressed_destination_port.name} in "
                                f"{destination_object.address} since it already has a connection {value}."
                            )
                        else:
                            raise ValueError(
                                f"Cannot connect to input port {addressed_destination_port.name} in "
                                f"{destination_object.address} since it already has a default value {value}."
                            )
                    destination_port.default_value = addressed_source_port.address
                connection = Connection(
                    addressed_source_port, addressed_destination_port
                )
                connections_list.append(connection)
        return connections_list

    def _resolve_destination(self, address):
        if self.name == address:
            return self
        else:
            raise Exception(
                f"The address {address} is not recognised in {self.address}. If you're trying to reference a "
                f"child of {self.name}, make sure {self.name} is a CompositePortedObjectWithConnections instance."
            )

    """
    def _check_connection(
        self,
        type,
        source_object,
        addressed_source_port,
        destination_object,
        addressed_destination_port,
    ):
        ALLOWED_PORT_CLASSES = {
            "variable": AddressedVariablePort,
            "parameter": (AddressedInputPort, AddressedOutputPort)
        }
        for port in [addressed_source_port, addressed_destination_port]:

        if type == "variable":
            self._check_variable_connection(
                addressed_source_port, addressed_destination_port
            )
        elif type == "parameter":
            self._check_parameter_connection(
                addressed_source_port, addressed_destination_port
            )

    def _check_variable_connection(self, source_port, destination_port):
        if not isinstance(source_port, AddressedVariablePort):
            raise TypeError(
                f"Connection between {source_port.address} and {destination_port.address} defined "
                f"in {self.address} failed since {source_port.address} is not a variable port."
            )
        elif not isinstance(destination_port, AddressedVariablePort):
            raise TypeError(
                f"Connection between {source_port.address} and {destination_port.address} defined "
                f"in {self.address} failed since {destination_port.address} is not a variable port."
            )

    def _check_parameter_connection(
        self, source_object, source_port, destination_object, destination_port
    ):
        source_is_base_object = hasattr(source_object, "children")
        destination_is_base_object = hasattr(destination_object, "destination")
        source_port_type = type(source_port)
        destination_port_type = type(destination_port)
    """

    def add_input_connections(
        self,
        delay_connection_parsing: bool = True,
        overwrite: bool = True,
        **connections: str | HierarchySeparatedStr,
    ):
        # TODO: Do we need to enable overwrite facility?
        # TODO: Enable adding numeric/non-hierarchy connections
        address_connections = {}
        for port, connection in connections.items():
            try:
                connection = float(connection)
                if connection.is_integer():
                    connection = int(connection)
                if port in self.input_ports:
                    # TODO: Could check if the value is the same as the parameter value
                    raise Exception(
                        f"Input '{port}' is already defined as an input port in {self.address}."
                    )
                self.add_input_ports({"name": port, "default_value": connection})
            except (ValueError, TypeError):
                if isinstance(connection, str):
                    address_connections[port] = connection
                elif isinstance(connection, (list, dict, tuple)):
                    raise TypeError(
                        f"Multiple inputs {connection} specified for the input connection to port "
                        f"{port} of {self.address}."
                    )
                else:
                    raise TypeError(
                        f"Invalid input connection {connection} for port {port} in {self.address}."
                    )

        options = {
            "port_type": PortTypes.INPUT,
            "type": "parameter",
            "overwrite": overwrite,
        }
        self._add_parameter_connections(
            delay_connection_parsing, options, **address_connections
        )

    def add_output_connections(
        self,
        delay_connection_parsing: bool = True,
        **connections: str | HierarchySeparatedStr | set[str | HierarchySeparatedStr],
    ):
        options = {"port_type": PortTypes.OUTPUT, "type": "parameter"}
        self._add_parameter_connections(
            delay_connection_parsing, options, **connections
        )

    def _add_parameter_connections(
        self, delay_connection_parsing: bool = True, options: dict = {}, **connections
    ):
        temp_connections = {
            TemporaryConnection(port, connections, **options)
            for port, connections in connections.items()
        }
        # print("ADD TEMP CONNECTIONS", [(conn.port, conn.connections) for conn in temp_connections])
        self._temp_parameter_connections |= temp_connections
        if not delay_connection_parsing:
            self._process_temp_parameter_connections()

    def add_variable_connections(
        self,
        delay_connection_parsing: bool = True,
        **connections: str | HierarchySeparatedStr | set[str | HierarchySeparatedStr],
    ):
        # TODO: Allow non-hierarchy connections to be interpreted as internal variable names
        options = {"port_type": PortTypes.VARIABLE, "type": "variable"}
        temp_connections = {
            TemporaryConnection(port, connections, **options)
            for port, connections in connections.items()
        }
        self._temp_variable_connections |= temp_connections
        if not delay_connection_parsing:
            self._process_temp_variable_connections()

    def _process_temp_variable_connections(self):
        if connections := self._temp_variable_connections:
            connections_list = self._parse_connections(
                type="variable", connections=connections
            )
            self.variable_connections.add_connections(*connections_list)
        self._temp_variable_connections.clear()

    def _process_temp_parameter_connections(self):
        if connections := self._temp_parameter_connections:
            connections_list = self._parse_connections(
                type="parameter", connections=connections
            )
            self.parameter_connections.add_connections(*connections_list)
        self._temp_parameter_connections.clear()


class PortedObjectWithAssignmentsAndConnections(
    PortedObjectWithAssignments,
    PortedObjectWithConnections,
):
    def _add_output_port(self, port):
        port = BaseOutputPort(name=port.name, description=port.description)
        super()._add_output_port(port)


class CompositePortedObjectWithConnections(
    PortedObjectWithConnections, CompositePortedObjectWithHierarchy
):
    def __init__(
        self,
        name: str,
        children: list[PortedObjectWithConnections | PortedObjectData] = [],
        input_ports: list[dict | tuple | str] = [],
        output_ports: list[dict | str] = [],
        variable_ports: list[dict | str] = [],
        inputs: dict[HierarchySeparatedStr | set[HierarchySeparatedStr]] = {},
        output_connections: dict[
            HierarchySeparatedStr | set[HierarchySeparatedStr]
        ] = {},
        variable_connections: dict[
            HierarchySeparatedStr | set[HierarchySeparatedStr]
        ] = {},
        variable_wires: list[dict | tuple] = [],
        directed_wires: list[dict | tuple] = [],
        parsing_locals: dict = {},
        **kwargs,
    ):
        super().__init__(
            name=name,
            children=children,
            input_ports=input_ports,
            output_ports=output_ports,
            variable_ports=variable_ports,
            inputs=inputs,
            output_connections=output_connections,
            variable_connections=variable_connections,
            variable_wires=variable_wires,
            directed_wires=directed_wires,
            parsing_locals=parsing_locals,
            **kwargs,
        )
        # TODO: Intercept directed and variable wires

    def _resolve_destination(self, address):
        return self._get_child(address)

    def _collect_child_connections(self):
        for child_object in self.children.values():
            try:
                child_object._collect_child_connections()
            except Exception as e:
                if isinstance(e, AttributeError):
                    pass
                else:
                    raise e
            child_variable_connections = child_object.variable_connections
            child_parameter_connections = child_object.parameter_connections
            child_variable_connections.prefix_connections(self.name)
            child_parameter_connections.prefix_connections(self.name)
            self.variable_connections.add_connections(*child_variable_connections)
            self.parameter_connections.add_connections(*child_parameter_connections)

    def pre_compile(self):
        self._process_temp_variable_connections()
        self._process_temp_parameter_connections()
        self._collect_child_connections()
        compiled_variable_connections = ConnectionsCompiler(self.variable_connections)
        # TODO: rename
        variable_wire_groups = compiled_variable_connections.wire_groups
        self._process_connections("variable", variable_wire_groups)

        compiled_parameter_connections = ConnectionsCompiler(self.parameter_connections)
        parameter_wire_groups = compiled_parameter_connections.wire_groups
        self._process_connections("parameter", parameter_wire_groups)

    """
    def draw(
        self,
        suppress_dummy: bool = True,
        filename=None,
        filetype="png",
        draw_prog="dot",
    ):
        data = self.to_data()
        G = psympleGraph(data)
        A = G.to_pgv(suppress_dummy=suppress_dummy)
        A.layout(prog=draw_prog, args="-Efontsize=8")
        if not filename:
            filename = self.name
        A.draw(f"{filename}.{filetype}")
    """
    
    def _process_connections(self, type: str, wire_groups: list):
        WireGroupClass = WIRE_GROUP_CLASSES[type]
        wire_groups = [WireGroupClass(*group) for group in wire_groups]
        for wire_group in wire_groups:
            self._process_wire_group(type, wire_group)

    def _process_wire_group(self, type: str, wire_group: VariableWireGroup):
        wire_root = wire_group.root

        """ DEBUG
        print(
            "------",
            f"processing {type} wire group",
            f"object: {self.address}",
            f"ports: {wire_group.ports}",
            f"root {wire_group.root}",
            "------",
            sep="\n",
        )
        """

        port_hierarchy = wire_group.port_hierarhcy
        local_ports = port_hierarchy.get("locals")

        # Safety check - should never be here
        # assert len(local_ports) in {0, 1}

        ports_by_child = port_hierarchy.get("by_child")
        # If there's only one child, then only connect to it if there's a local port.
        # If there's more than one child, then a wire will always be created.
        num_child_connections = len(ports_by_child)
        # print("NUM CHILD CONNECTIONS", ports_by_child, local_ports)

        child_connector_ports = []
        # TODO: collect common functionality in each case below
        if num_child_connections == 1:
            child_name = next(iter(ports_by_child.keys()))
            child_ports = next(iter(ports_by_child.values()))
            try:
                child_object = self._get_child(child_name)
            except KeyError as e:
                raise AddressingError(
                    f"Failed to process wire group between {wire_group.ports} in {self.address}: {e}"
                )
            if local_ports:
                child_connector_port = self._create_local_child_connection(
                    type, child_object, child_ports, wire_root
                )
                if child_connector_port:
                    child_connector_ports.append(child_connector_port)
            else:
                # Pass the whole wire group down
                wire_group = wire_group.strip_port_addresses()
                child_object._process_wire_group(type, wire_group)
        elif num_child_connections > 1:
            for child_name, child_ports in ports_by_child.items():
                try:
                    child_object = self._get_child(child_name)
                except KeyError as e:
                    raise AddressingError(
                        f"Failed to process wire group between {wire_group.ports} in {self.address}: {e}"
                    )
                child_connector_port = self._create_local_child_connection(
                    type, child_object, child_ports, wire_root
                )
                if child_connector_port:
                    child_connector_ports.append(child_connector_port)

        if child_connector_ports:
            self._create_wire(type, local_ports, child_connector_ports)

    def _create_wire(self, type, local_ports, child_ports):
        local_ports = set(local_ports)
        child_ports = set(child_ports)
        if type == "variable":
            self._create_variable_wire(local_ports, child_ports)
        elif type == "parameter":
            self._create_parameter_wire(local_ports, child_ports)

    def _create_variable_wire(self, local_ports, child_ports):
        def get_local_port_address(ports):
            return set(port.strip_address().address for port in ports)

        child_variable_ports = get_local_port_address(child_ports)
        if local_ports:
            if len(local_ports) > 1:
                raise Exception()
            local_variable_ports = get_local_port_address(local_ports)
            self.add_variable_wire(child_variable_ports, local_variable_ports.pop())
        else:
            dummy_variable = self.add_dummy_port(DummyTypes.INTERNAL_VARIABLE)
            self.add_variable_wire(
                child_variable_ports,
                output_name=dummy_variable,
            )

    def _create_parameter_wire(self, local_ports, child_ports):
        child_output_ports = set(
            port for port in child_ports if isinstance(port, AddressedOutputPort)
        )
        all_ports = local_ports.union(child_ports)

        def get_local_port_address(ports):
            return set(port.strip_address().address for port in ports)

        all_parameter_ports = get_local_port_address(all_ports)
        if child_output_ports:
            if len(child_output_ports) > 1:
                raise Exception()
            child_output_ports = get_local_port_address(child_output_ports)
            source = child_output_ports.pop()
            all_parameter_ports.remove(source)
            # print("PARAMETER CONNECTION from", source, "to", all_parameter_ports)
            self.add_directed_wire(source, all_parameter_ports)
        else:
            if len(local_ports) > 1:
                raise Exception()
            local_ports = get_local_port_address(local_ports)
            source = local_ports.pop()
            all_parameter_ports.remove(source)
            # print("PARAMETER CONNECTION from", source, "to", all_parameter_ports)
            self.add_directed_wire(source, all_parameter_ports)

    def _create_local_child_connection(
        self, type: str, child_object, child_ports, wire_root
    ):
        local_child_ports = child_ports.get("child_ports")
        descendent_child_ports = child_ports.get("descendent_ports")
        all_ports = local_child_ports + descendent_child_ports

        local_child_port = None
        wire_group = None

        WireGroupClass = WIRE_GROUP_CLASSES[type]
        AddressedPortClass = ADDRESSED_PORT_CLASSES[type]

        if local_child_ports:
            if len(local_child_ports) > 1:
                # BUG: This can be triggered if the object has two different ports which are connected from the
                # same source. It feels like this should be allowed. In this case the passed "root" to
                # the wire group is not really the root.
                raise Exception()
            local_child_port = local_child_ports[0]
            if descendent_child_ports:
                # wire_group = WireGroupClass(*all_ports, root=local_child_port)
                wire_group = WireGroupClass(*all_ports, root=None)
        else:
            if descendent_child_ports:
                if type == "variable":
                    local_child_port_name = child_object.add_dummy_port(
                        DummyTypes.VARIABLE
                    )
                elif type == "parameter":
                    child_address = child_object.get_truncated_address(self.name)
                    root_address = wire_root.address.object_address
                    # print("ROOT", root_address, "CHILD", child_address, "WIRE ROOT", wire_root)
                    if root_address.startswith(child_address):
                        dummy_type = DummyTypes.OUTPUT
                    else:
                        dummy_type = DummyTypes.INPUT
                    local_child_port_name = child_object.add_dummy_port(dummy_type)
                else:
                    raise Exception()
                local_child_port = AddressedPortClass.from_port(
                    child_object._get_port_by_name(local_child_port_name, type=type),
                    child_object.get_truncated_address(self.name),
                )
                all_ports.append(local_child_port)
                # wire_group = WireGroupClass(*all_ports, root=local_child_port)
                wire_group = WireGroupClass(*all_ports, root=None)
        if wire_group:
            child_object._process_wire_group(type, wire_group.strip_port_addresses())
        return local_child_port

    def _process_temp_parameter_connections(self):
        for child in self.children.values():
            child._process_temp_parameter_connections()
        super()._process_temp_parameter_connections()

    def _process_temp_variable_connections(self):
        for child in self.children.values():
            child._process_temp_variable_connections()
        super()._process_temp_variable_connections()
