from psymple.build.abstract import PortedObject, PortedObjectWithAssignments
from psymple.build.ported_objects import (
    CompositePortedObject,
    FunctionalPortedObject,
    VariablePortedObject,
    PortedObjectData,
)
from psymple.build.ports import InputPort, OutputPort, VariablePort
from psymple.build import HIERARCHY_SEPARATOR

from .parameters import AddressAccessedDict

from itertools import combinations

from sympy.combinatorics import Permutation


class HierarchyAddress:
    def get_ancestor_name(self, ancestor_name, back_generations: int = 0):
        index = self.address_parts.index(ancestor_name)
        return_name = self.address_parts[index - back_generations]
        return return_name

    def get_ancestor(self, ancestor_name, back_generations: int = 0):
        return self.parents[self.get_ancestor_name(ancestor_name, back_generations)]
    
    def get_object_by_port_address(self, address):
        address_parts = address.split(HIERARCHY_SEPARATOR)
        ancestor_name, *address, port = address_parts
        ancestor_object = self.get_ancestor(ancestor_name)
        if address:
            target_object = ancestor_object._get_child(HIERARCHY_SEPARATOR.join(address))
        else:
            target_object = ancestor_object

        return target_object

    @property
    def address(self):
        return HIERARCHY_SEPARATOR.join(reversed(self.address_parts))

    @property
    def address_parts(self):
        return [self.name] + list(self.parents.keys())

    @property
    def parents(self):
        if self.parent:
            parents = {self.parent.name: self.parent} | self.parent.parents
        else:
            parents = {}
        return parents


class Connections(dict):
    def __init__(self):
        self.update({"parameters": {}, "variables": {}, "internal_variables": {}})

    def aggregate_variables(self, aggregations: dict[str, set[str]]):
        pass

    @property
    def parameters(self):
        return self.get("parameters")

    @parameters.setter
    def parameters(self, value):
        self.update({"parameters": value})

    @property
    def variables(self):
        return self.get("variables")

    @variables.setter
    def variables(self, value):
        self.update({"variables": value})

    @property
    def internal_variables(self):
        return self.get("internal_variables")

    @internal_variables.setter
    def internal_variables(self, value):
        self.update({"internal_variables": value})

    @property
    def all_variables(self):
        return self.variables | self.internal_variables

    @property
    def all(self):
        return self.parameters | self.all_variables


class ConnectionError(Exception):
    pass


class ParameterError(Exception):
    pass


class PortedObjectWithHierarchy(PortedObject, HierarchyAddress):
    def __init__(
        self,
        name: str,
        parent: PortedObject = None,
        children: list = [],
        input_ports: list[InputPort | dict | tuple | str] = [],
        output_ports: list[OutputPort | dict | str] = [],
        variable_ports: list[VariablePort | dict | str] = [],
        parsing_locals: dict = {},
    ):
        super().__init__(
            name=name,
            input_ports=input_ports,
            output_ports=output_ports,
            variable_ports=variable_ports,
            parsing_locals=parsing_locals,
        )
        self.children = {}
        self.add_children(*children)

        self.parent = parent

    def add_children(self, *children: PortedObjectData | PortedObject):
        """
        Add children to `self`. A child is a `PortedObject` instance whose ports and assignments
        become available to `self`.

        Args:
            *children: instance of `PortedObject` or `PortedObjectData` specifying a
                ported object. Entries can be a mixture of types.
        """
        for data in children:
            # Attempt to coerce dictionary into PortedObjectData
            if isinstance(data, dict):
                if not type(data) == PortedObjectData:
                    data = PortedObjectData(**data)
                self._build_child(data)
            elif isinstance(data, PortedObject):
                self._add_child(data)

    def _build_child(self, child_data: PortedObjectData):
        # Build a ported object instance from data
        if not type(child_data) == PortedObjectData:
            raise TypeError(
                f"Argument 'child_data' must have type PortedObjectData, not {type(child_data)}"
            )
        child = child_data.to_ported_object(parsing_locals=self.parsing_locals)
        self._add_child(child)

    def _add_child(self, child):
        if child.name in self.children:
            raise ValueError(
                f"Child {child.name} already exists in ported object {self.name}"
            )
        self.children[child.name] = child
        child.parent = self
        # print(f"Added {child.name} to {self.name}")

    def set_parent(self, parent):
        self.parent = parent
        if self.name in self.parents:
            raise NameError()

    def to_data(self):
        pass

    def compile(self):
        pass

class PortedObjectWithConnections(PortedObjectWithHierarchy):
    def __init__(
        self,
        name: str,
        parent: PortedObject = None,
        children: list = [],
        inputs: dict = {},
        output_connections: dict = {},
        variable_connections: dict = {},
        input_ports: list[InputPort | dict | tuple | str] = [],
        output_ports: list[OutputPort | dict | str] = [],
        variable_ports: list[VariablePort | dict | str] = [],
        parsing_locals: dict = {},
        **parameters,
    ):

        # TODO: Validate ports
        super().__init__(
            name=name,
            parent=parent,
            children=children,
            input_ports=input_ports,
            output_ports=output_ports,
            variable_ports=variable_ports,
            parsing_locals=parsing_locals,
        )

        self.connections = Connections()
        self._initialise_dummy_numbers()
        self.inputs = {}
        self.output_connections = {}
        self.variable_connections = {}
        self.inputs_from_other = set()
        if not hasattr(self, "required_parameters"):
            self.required_parameters = set()
        if not hasattr(self, "required_inputs"):
            self.required_inputs = set()
        for port, address in inputs.items():
            self.add_input_connection(port, address)
        for port, connection in output_connections.items():
            self.add_output_connection(port, connection)
        for port, connection in variable_connections.items():
            self.add_variable_connection(port, connection)
        self.parameters = AddressAccessedDict()
        self.parameters.set(parameters)
        #print(f"PARAMETERS OF {self.name}: {self.parameters}")

        #self.initialise_object() 

    def get_relative(self, address: str):
        address_parts = address.split(HIERARCHY_SEPARATOR, 1)
        #print("PARTS", address_parts)
        ancestor_name = address_parts[0]
        address_rel_ancestor = address_parts[1]
        return self.get_ancestor(ancestor_name)._get_child(address_rel_ancestor)
    
    def get_target(self, address: str):
        ancestor, target_address = address.split(HIERARCHY_SEPARATOR, 1)
        return self.get_ancestor(ancestor)._get_child(target_address)

    def process_structural_parameters(self, search_ancestry=True):
        for parameter_name in self.required_parameters:
            parameter_value = self.search_for_parameter(parameter_name, search_ancestry)
            if parameter_value is None:
                raise ParameterError(
                    f"PBDM object {self.name} could not find parameter {parameter_name} in itself or ancestry"
                )
            self.parameters.update({parameter_name: parameter_value})
            #print(
            #    f"Got parameter value {parameter_name} in {self.name}: {parameter_value}"
            #)

    def get_in_parameters(self, parameter_address: str, default: str|int|float = None):
        #DEPR
        parameters = self.parameters
        while HIERARCHY_SEPARATOR in parameter_address:
            parameter_location, parameter_address = parameter_address.split(HIERARCHY_SEPARATOR, 1)
            parameters = parameters.get(parameter_location, {})
            if parameters == {}:
                break
        return parameters.get(parameter_address, default)

    def search_for_parameter(self, parameter_name: str, default: str|int|float = None, search_ancestry: bool = True):
        #DEPR
        # print(self.name, self.parameters)
        parameter_value = self.get_in_parameters(parameter_name, default)
        if parameter_value is None and search_ancestry:
            if self.parent:
                parameter_value = self.parent.search_for_parameter(
                    parameter_name, default, search_ancestry
                )
            else:
                raise Exception(f"Parameter {parameter_name} could not be found")
        return parameter_value
    
    def get_parameter(self, parameter_address: str, default: str|int|float = None, search_ancestry: bool = True):
        params_search = self.parameters
        parameter_value = params_search.get(parameter_address)
        if parameter_value is None and search_ancestry and self.parent:
            parameter_value = self.parent.get_parameter(parameter_address, default, search_ancestry)
        if parameter_value is None:
            if default is not None:
                parameter_value = default
            else:
                raise Exception(f"Parameter with address '{parameter_address}' not found in {self.name} with no default specified.")
        return parameter_value

    def search_for_required_inputs(self, inputs, parameters):
        SKIP_SEARCH = {"TMAX", "TMIN", "RH", "SOLAR_RAD", "DAY_LENGTH", "TEMP"}
        # Could add customisation here on where to automatically search, key transformations, etc.
        # missing_inputs = self.required_inputs - inputs.keys()
        #print("REQIN", self.address, self.input_ports.keys(), inputs.keys())
        missing_inputs = {
            port_name
            for port_name, port in self.input_ports.items()
            if (port.default_value is None)
        } - inputs.keys() - self.inputs_from_other - SKIP_SEARCH
        #print(missing_inputs)

        #print(f"Searching in {self.name} for {missing_inputs}. Inputs from other: {self.inputs_from_other}.")
        for input in missing_inputs:
            #print(f"Seaching for input {input} in {self.name}")
            if input in parameters:
                self.add_input_ports({"name":input, "default_value":parameters[input]})
                #print(f"Found input {input} in parameters")
            elif self.parent:
                #print(f"Creating connection for {input} from {self.name} to {self.parent.name}")
                if input not in self.parent.input_ports:
                    #print(f"HERE, {input} is not in {self.parent.name} for {self.name}. Creating port...")
                    # TODO: DUMMY PORT INSTEAD
                    self.parent.add_input_ports(input)
                #self.add_input_connection(input, f"{self.parent.name}.{input}")
                #self.add_parameter_connections({input: f"{self.parent.name}.{input}"})
                self.parent.add_parameter_connections({input: f"{self.name}.{input}"})

                ### JUST EDIT self.parameters.connections directly!!
            # No else because if no parent, it becomes a required system input

    def add_input_connection(self, port: str, value: str, overwrite=True):
        connection = self.inputs.setdefault(port, None)
        if connection and not overwrite:
            raise ConnectionError(
                f"An input for port {port} in {self.name} was already specified with address {value} and cannot be overwritten."
            )

        if isinstance(value, str) and HIERARCHY_SEPARATOR in value:
            # Points to an address in the system
            self.inputs[port] = value
        else:
            #print(f"ADDING INPUT PORT to {self.name} of name {port} and value {value}")
            self.add_input_ports({"name": port, "default_value": value})
            del self.inputs[port]

    def add_output_connection(self, port: str, connections: set[str], overwrite=False):
        if isinstance(connections, str):
            connections = {connections}
        if not overwrite:
            existing_connections = self.output_connections.setdefault(port, set())
            connections |= existing_connections
        self.output_connections[port] = connections

    def add_variable_connection(self, port, connections: set[str], overwrite=False):
        if isinstance(connections, str):
            connections = {connections}
        connections = set(connections)
        if not overwrite:
            existing_connections = self.variable_connections.setdefault(port, set())
            connections |= existing_connections
        self.variable_connections[port] = connections

    def expose_variables_old(self, variables: list | dict, target_address):
        """
        ---DEPR---??
        Adds variable connections for each variable in variables to variables in target_name.

        If list, variable "v" is connected to "target_address.v".

        If dict, variable "v" is connected to "target_address.variables[v]".

        Args:
            variables: list or dict of variables in self.
            target_name: (relative) address of object to connect to.
        """
        if isinstance(variables, list):
            for v in variables:
                self.add_variable_connection(v, {f"{target_address}.{v}"})
        elif isinstance(variables, dict):
            for v, target_v in variables.items():
                self.add_variable_connection(v, {f"{target_address}.{target_v}"})

    def _initialise_dummy_numbers(
        self,
        input_names="dummy_input",
        output_names="dummy_output",
        variable_names="dummy_variable",
        internal_variable_names="dummy_internal_variable",
    ):
        self.dummy_numbers = {
            "input": {"name": input_names, "value": 1},
            "output": {"name": output_names, "value": 1},
            "variable": {"name": variable_names, "value": 1},
            "internal_variable": {"name": internal_variable_names, "value": 1},
        }

    def add_dummy_input_port(self):
        dummy_data = self.dummy_numbers.get("input")
        port_id = dummy_data.get("name")
        port_number = dummy_data.get("value")

        port_name = f"{port_id}_{port_number}"
        self.add_input_ports(port_name)
        self.dummy_numbers["input"]["value"] += 1

        return port_name

    def add_dummy_output_port(self):
        dummy_data = self.dummy_numbers.get("output")
        port_id = dummy_data.get("name")
        port_number = dummy_data.get("value")

        port_name = f"{port_id}_{port_number}"
        self.add_output_ports(port_name)
        self.dummy_numbers["output"]["value"] += 1

        return port_name

    def add_dummy_variable_port(self):
        dummy_data = self.dummy_numbers.get("variable")
        port_id = dummy_data.get("name")
        port_number = dummy_data.get("value")

        port_name = f"{port_id}_{port_number}"
        self.add_variable_ports(port_name)
        self.dummy_numbers["variable"]["value"] += 1

        return port_name

    def add_dummy_internal_variable(self):
        dummy_data = self.dummy_numbers.get("internal_variable")
        port_id = dummy_data.get("name")
        port_number = dummy_data.get("value")

        internal_name = f"{port_id}_{port_number}"
        self.dummy_numbers["internal_variable"]["value"] += 1

        return internal_name

    def common_ancestor(self, other, all=False):
        """
        Returns the closest common ancestor of two objects, or None.
        If all=True, returns all common ancestors.
        """
        if isinstance(other, HierarchyAddress):
            other_address = other.address
        else:
            other_address = other
        other_address_parts = other_address.split(HIERARCHY_SEPARATOR)
        common_ancestors = [
            name for name in self.address_parts if name in other_address_parts
        ]
        if not common_ancestors:
            if any(name in self.parent.children for name in other_address):
                common_ancestors = [self.parent.name]
            else:
                raise Exception()
        if all:
            return common_ancestors
        else:
            return common_ancestors[0]

    def parse_address(self, address: str):
        """
        An address has the form "A.B.C.q"
        """
        address_parts = address.split(HIERARCHY_SEPARATOR)
        target_port = address_parts.pop(-1)
        common_ancestor = self.common_ancestor(address_parts[::-1])
        index = address_parts.index(common_ancestor[0])
        return common_ancestor, address_parts[index:], target_port

    def _add_parameter_connection(self, port, address: str):
        port_connections = self.connections.all.get(port, set())
        #print(f"Adding connection in {self.name} PORT {port} ADDRESS {address}")
        #print(port, address, self.name)
        address_main = HIERARCHY_SEPARATOR.join(address.split(HIERARCHY_SEPARATOR)[:-1])
        #print("HELLO", address_main)
        try:
            ancestor_name = self.common_ancestor(address_main)
            # print("here", ancestor_name)
        except Exception:
            try:
                self._get_child(address_main)
            except:
                raise Exception("address could not be resolved")
            ancestor_name = address_main
        # print(address.split(ancestor_name + HIERARCHY_SEPARATOR))
        """
        if address.startswith(ancestor_name + HIERARCHY_SEPARATOR):
            relative_address = address
        else:
            relative_address = (
                ancestor_name
                + HIERARCHY_SEPARATOR
                + address.split(
                    HIERARCHY_SEPARATOR + ancestor_name + HIERARCHY_SEPARATOR
                )[1]
            )
        """
        # print("TRIM", relative_address)
        # BUG: What is meant to happen here?
        #port_connections.add(relative_address)
        port_connections.add(address)
        self.connections.parameters.update({port: port_connections})

    def _add_variable_connection(self, node, address, internal):
        if internal:
            node_connections = self.connections.internal_variables.get(node, set())
        else:
            node_connections = self.connections.variables.get(node, set())

        address_main = HIERARCHY_SEPARATOR.join(address.split(HIERARCHY_SEPARATOR)[:-1])

        #print(f"adding variable connection to {self.name}, from {node} to {address}")
        #print(f"main address is {address_main}")
        try:
            ancestor_name = self.common_ancestor(address_main)
            #print("ANC", ancestor_name)
        except Exception:
            try:
                self._get_child(address_main)
            except:
                raise Exception("address could not be resolved")
            ancestor_name = address_main
        if address.startswith(ancestor_name + HIERARCHY_SEPARATOR):
            relative_address = address
        else:
            relative_address = (
                ancestor_name
                + HIERARCHY_SEPARATOR
                + address.split(
                    HIERARCHY_SEPARATOR + ancestor_name + HIERARCHY_SEPARATOR
                )[1]
            )
        # BUG: As above
        #node_connections.add(relative_address)
        node_connections.add(address)
        if internal:
            self.connections.internal_variables.update({node: node_connections})
        else:
            self.connections.variables.update({node: node_connections})

    def add_variable_connections(self, connections: dict, internal=False):
        for port, data in connections.items():
            if isinstance(data, set):
                for address in data:
                    self._add_variable_connection(port, address, internal=internal)
            elif isinstance(data, str):
                self._add_variable_connection(port, data, internal=internal)
            else:
                raise TypeError()

    def add_parameter_connections(self, connections: dict):
        """
        connections is a dict of port: address pairs.
        """
        for port, data in connections.items():
            if isinstance(data, set):
                for address in data:
                    self._add_parameter_connection(port, address)
            elif isinstance(data, str):
                self._add_parameter_connection(port, data)
            else:
                raise TypeError()

    def parameter_search(self):
        # TODO: I probably want to search for the structural parameters and inputs during the compile phase
        # self.process_structural_parameters()
        for child in self.children.values():
            #print(f"PARAM SEARCH CHILD of {self.name}: {child.name} ")
            child.parameter_search()
        self.search_for_required_inputs(self.inputs, self.parameters)
        # for child in self.children.values():
        #    child.process_structural_parameters()

    def attribute_parameter_connections(self):
        # TODO: Mirror output connections to check for destination inputs
        for port, address in self.inputs.items():
            #print(f"Attributing {port} with INPUT {address} IN {self.name}...")
            #print(f"Attributing {self.address}.{port} with INPUT {address}...")
            address_parts = address.split(HIERARCHY_SEPARATOR)

            ## SIBLING CONNECTIONS HERE 
            ancestor_name = address_parts[0]
            if self.parent:
                #print("PARENT", self.parent, self.parent.children)
                if address_parts[0] in self.parent.children:
                    ancestor_name = self.parent.name
                    address_parts = [self.parent.name] + address_parts

            ## TO HERE

            #print("NAME", ancestor_name, self.name)
            ancestor_object = self.get_ancestor(ancestor_name)

            if len(address_parts) > 2:
                target_address = HIERARCHY_SEPARATOR.join(address_parts[1:-1])
                target_object = ancestor_object._get_child(target_address)
                #print(target_address, target_object.address)
                trimmed_parts = self.address_parts[
                    : self.address_parts.index(ancestor_name) + 1
                ]
            else:
                target_object = ancestor_object
                trimmed_parts = self.address_parts[
                    : self.address_parts.index(ancestor_name)
                ]

            target_port = address_parts[-1]

            target_output_connections_at_port = (
                target_object.connections.parameters.get(target_port, [])
            )
            # print(address)
            if any(
                other_address.endswith(address)
                for other_address in target_output_connections_at_port
            ):
                raise Exception("Unresolvable connection conflict")

            # print("PARTSSSSSS", self.address_parts, ancestor_name)

            trimmed_parts.reverse()
            trimmed_parts.append(port)
            mirror_address = HIERARCHY_SEPARATOR.join(trimmed_parts)
            target_object.add_parameter_connections({target_port: mirror_address})
            #print(target_object.name, target_object.connections.parameters)
            #print(
            #    f"...to {target_object.address}.{target_port}, OUTPUT {mirror_address}"
            #)

            self.inputs_from_other.add(port)

        #self.inputs.clear()

        for port, connections in self.output_connections.items():
            for address in connections:
                address_parts = address.split(HIERARCHY_SEPARATOR)

                ## SIBLING CONNECTIONS HERE 
                ancestor_name = address_parts[0]
                if self.parent:
                    if address_parts[0] in self.parent.children:
                        ancestor_name = self.parent.name
                        address_parts = [self.parent.name] + address_parts

                ## TO HERE
                ancestor_object = self.get_ancestor(ancestor_name)

                if len(address_parts) > 2:
                    target_address = HIERARCHY_SEPARATOR.join(address_parts[1:-1])
                    target_object = ancestor_object._get_child(target_address)
                else:
                    target_object = ancestor_object
                target_port = address_parts[-1]

                #print(f"{target_object.name} has input/output {target_port} from {self.address}.{port}.")

                target_object.inputs_from_other.add(target_port)

        self.add_parameter_connections(self.output_connections)

        if hasattr(self, "children"):
            for child in self.children.values():
                child.attribute_parameter_connections()

    def process_parameters(self):

        #print("PROCESSING!!", self.address, self.connections.parameters)

        for child in self.children.values():
            child.process_parameters()

        #print("PROCESSING!! POST CHILDREN", self.address, self.connections.parameters)
        new_child_connections = {}

        for port, connections in self.connections.parameters.items():
            #print(port, connections)
            ancestor_connections = {
                address
                for address in connections
                if address.split(HIERARCHY_SEPARATOR)[0] in self.parents
            }
            child_connections = {
                address
                for address in connections
                if address not in ancestor_connections
            }

            #print("ANC-CHL", ancestor_connections, child_connections)
            exposure_port = None
            parent_connections = {
                address
                for address in ancestor_connections
                if address.startswith(self.parent.name)
            }
            non_parent_connections = {
                address
                for address in ancestor_connections
                if address not in parent_connections
            }
            #print("FIL-OTH", filter_connections, other_connections)

            # filter_connections = those which are processed in the parent

            exposure_connections = {
                address
                for address in parent_connections
                if len(address.split(HIERARCHY_SEPARATOR)) == 2
            }
            sibling_connections = {
                address
                for address in parent_connections
                if len(address.split(HIERARCHY_SEPARATOR)) == 3
            }
            other_connections = {
                address
                for address in parent_connections
                if len(address.split(HIERARCHY_SEPARATOR)) > 3
            }
            #print(other_connections)
            # Deal with "horseshoe" connections to siblings
            #sibling_connections = sibling_connections
            sibling_connector_ports = {}
            for address in sibling_connections:
                ancestor_name, sibling_name, sibling_port = address.split(
                    HIERARCHY_SEPARATOR
                )
                sibling_object = self.parent.children[sibling_name]
                if sibling_port not in sibling_object.input_ports:
                    pass
                    # raise Exception(f"Input port {sibling_port} not found in {sibling_object.name}")
                target_address = f"{sibling_name}.{sibling_port}"
                sibling_connector_ports.update({sibling_name: sibling_port})

            # Deal with connections to siblings' offspring
            #other_connections = other_connections
            for address in other_connections:
                ancestor_name, sibling_name, target_address = address.split(
                    HIERARCHY_SEPARATOR, 2
                )
                sibling_object = self.parent.children[sibling_name]

                if sibling_name in sibling_connector_ports:
                    sibling_port = sibling_connector_ports[sibling_name]
                else:
                    sibling_port = sibling_object.add_dummy_input_port()
                    sibling_connector_ports.update({sibling_name: sibling_port})
                    sibling_target_address = f"{sibling_name}.{sibling_port}"

                # print(f"Connect {target_address} from {sibling_port} in {sibling_name}")
                sibling_object.add_parameter_connections({sibling_port: target_address})

            if exposure_connections:
                if len(exposure_connections) > 1:
                    raise Exception("I don't know what to do with many exposed ports")
                elif len(exposure_connections) == 1:
                    exposure_port = exposure_connections.pop().split(
                        HIERARCHY_SEPARATOR
                    )[1]

            if non_parent_connections:
                if not exposure_port:
                    exposure_port = self.parent.add_dummy_output_port()
                # print(f"Pass forward: connect {exposure_port} in {self.parent.name} to {other_connections}")
                parent_port_connections = self.parent.connections.parameters.setdefault(
                    exposure_port, set()
                )
                parent_port_connections.update(non_parent_connections)
                self.parent.connections["parameters"][
                    exposure_port
                ] = parent_port_connections

            wire_destinations = []
            if sibling_connector_ports:
                wire_destinations += [
                    f"{name}.{port}" for name, port in sibling_connector_ports.items()
                ]
            if exposure_port:
                wire_destinations.append(exposure_port)
            if wire_destinations:
                source_port = f"{self.name}.{port}"
                # print(f"WIRE IN {self.parent.name} FROM {self.name}.{port} to {wire_destinations}")
                self.parent.connections.parameters.update(
                    {source_port: wire_destinations}
                )
                # directed_wires.update({source_port: wire_destinations})

                # self.parent.add_directed_wire(source_port, wire_destinations)
            #print(f"DIRECTED WIRES in {self.parent.name}: {directed_wires}")
            #print(f"CONS-PAR BEFORE", port, connections, self.name, len(self.connections.parameters))
            new_child_connections[port] = child_connections
            #self.connections.parameters[port] = child_connections
            #print("CONS-PAR AFTER", port, connections, self.name, len(self.connections.parameters))

        self.connections.parameters = new_child_connections
        # Clear empty values from connections
        self.connections.parameters = {
            key: value for key, value in self.connections.parameters.items() if value
        }

        #print("PROCESSED", self.address, self.connections.parameters)

        # return directed_wires

    def attribute_variable_connections(self):
        # Process those connections which go through an ancestor to sit at that ancestor.
        # Connections to children are unchanged.
        for port, connections in self.variable_connections.items():
            #print(f"Reattributing PORT {port} with CONNECTIONS {connections} in {self.name}")
            
            ### SIBLING CONNECTIONS HERE 

            sibling_connections = {
                address 
                for address in connections
                if address.split(HIERARCHY_SEPARATOR)[0] in self.parent.children
            } if self.parent else {}
            ancestor_connections = {
                address
                for address in connections
                if address.split(HIERARCHY_SEPARATOR)[0] in self.parents
            } | {f"{self.parent.name}.{address}" for address in sibling_connections}
            ## TO HERE
            child_connections = {
                address
                for address in connections
                if address not in ancestor_connections
            }

            ancestors = {
                address.split(HIERARCHY_SEPARATOR)[0]
                for address in ancestor_connections
            }

            ancestor_connections_grouped = {
                ancestor: [
                    address.split(HIERARCHY_SEPARATOR, 1)[1]
                    for address in ancestor_connections
                    if address.startswith(ancestor)
                ]
                for ancestor in ancestors
            }
            #print(ancestor_connections_grouped)

            for ancestor, connections in ancestor_connections_grouped.items():
                #print("ANC-CON", ancestor, connections)
                # Find if there is a source port in connections
                ancestor_object = self.parents[ancestor]

                trimmed_parts = self.address_parts[: self.address_parts.index(ancestor)]
                trimmed_parts.reverse()
                trimmed_parts.append(port)
                port_address_from_ancestor = HIERARCHY_SEPARATOR.join(trimmed_parts)

                source_connections = {
                    address
                    for address in connections
                    if len(address.split(HIERARCHY_SEPARATOR)) == 1
                }
                other_connections = {
                    address
                    for address in connections
                    if address not in source_connections
                }
                internal_connection = False
                other_connections.add(port_address_from_ancestor)
                #print(other_connections)
                # print(self.connections.all_variables.items())
                if len(source_connections) > 1:
                    # We should not be in this case if variables were added properly
                    raise Exception()
                elif len(source_connections) == 1:
                    ancestor_node = source_connections.pop()
                else:
                    ancestor_node = ancestor_object.add_dummy_internal_variable()
                    internal_connection = True

                ancestor_object.add_variable_connections(
                    {ancestor_node: other_connections}, internal=internal_connection
                )

            self.connections.variables[port] = child_connections

        if hasattr(self, "children"):
            for child in self.children.values():
                child.attribute_variable_connections()

    def get_aggregation_groups(self, aggregations: list[tuple]):
        # print("GETTING AGGRS", aggregations)
        # Find the cyclic form of the permutation generated by the pairwise intersections
        # (equivalent to running through all n-fold intersections)

        unique_nodes = set().union(*(set(aggregation) for aggregation in aggregations))
        # print(unique_nodes)
        permutation_dict = {node: i for i, node in enumerate(unique_nodes)}
        inverse_permutation_dict = {i: node for (node, i) in permutation_dict.items()}

        # print("AGGR", aggregations)

        cycles = Permutation(
            [tuple(permutation_dict[node] for node in group) for group in aggregations]
        ).full_cyclic_form

        aggregation_groups = [
            [inverse_permutation_dict[i] for i in cycle] for cycle in cycles
        ]

        # print(f"Aggregation groups in {self.name} of {aggregation_groups}")

        ordered_aggregation_groups = []
        for group in aggregation_groups:
            dummy_names = [
                self.dummy_numbers["internal_variable"]["name"],
                self.dummy_numbers["variable"]["name"],
            ]
            non_user_variables = [
                node
                for node in group
                if any(node.startswith(name) for name in dummy_names)
            ]
            user_variables = [node for node in group if node not in non_user_variables]
            # print("USER", group, user_variables)
            if len(user_variables) > 1:
                raise ConnectionError("unresolvable variable aggregation")
            elif len(user_variables) == 1:
                node = user_variables[0]

            # non_user_variables = [node for node in group if node not in user_variables]
            # print("US-NONUS VARS", user_variables, non_user_variables)
            user_variables.sort(key=lambda x: (x == node))
            non_user_variables.sort(
                key=lambda x: ("_".join(x.split("_")[:-1]), -int(x.split("_")[-1])),
                reverse=True,
            )
            group = user_variables + non_user_variables
            ordered_aggregation_groups.append(group)

        # print(ordered_aggregation_groups)

        return ordered_aggregation_groups

    def perform_variable_aggregations(self, aggregations: list[tuple]):

        # ordered_aggregation_groups = self.get_aggregation_groups(aggregations)

        aggregations = [group for group in aggregations if group]

        for group in aggregations:
            node, *other_nodes = group

            group_union = self.connections.all_variables[node].union(
                *(self.connections.all_variables[node] for node in other_nodes)
            )
            #print(f"Aggregating {group} to node {node}")
            if node in self.connections.variables:
                self.connections.variables[node] = group_union
            else:
                self.connections.internal_variables[node] = group_union

            #print(f"Deleting {other_nodes}")
            for node in other_nodes:
                if node in self.connections.variables:
                    del self.connections.variables[node]
                    del self.variable_ports[node]
                else:
                    del self.connections.internal_variables[node]

    def process_variables(self, parent_variable_translations={}):
        """
        Assume that attribute_variable_connections() has been called on all objects.

        Strategy:
        (1) Simplify variable/internal variable connections from attribution/generated from parents
            (1a) Find all pairwise intersections between connections of variables/internal variables of self
            (1b) Perform variable aggregations in self using the pairwise data
            (1c) Work out the induced aggregations in the parent, translating them using parent_variable_translations
        (2) For each node, split the remaining connections by child
            (2a) Work out which children are addressed in connections
            (2b) Connect node to child through a variable port if a direct connection to the child is specified,
                otherwise through a dummy port
            (2c) Pass on any remaining variable connections to the child port
            (2d) Translations for the child updated to convert child port to the node
            (2e) Alter the variable connections of self to reflect the connections to child ports
        (3) Process the induced aggregations from children
            (3a) Call process variables for each child, using translations generated in (2d)
            (3b) Perform the induced aggregations from children
            (3c) Work out the induced aggregations in the parent
        (4) Return the induced aggregations in the parent, from (1c) and (3c)

        BUG: (2e) above needs to be performed later, once the induced aggregations from children are considered
        """
        # First, check if any variables have connections which share addresses
        variable_combinations = combinations(self.connections.variables, 2)
        variable_intersections = [
            (a, b)
            for (a, b) in variable_combinations
            if self.connections.variables[a].intersection(self.connections.variables[b])
        ]
        if variable_intersections:
            print("Potential connection error", variable_intersections)

        # Now, we know that all connections in self.variables are disjoint.
        # Combine any internal variables and variables which share elements, keeping
        # the variable port label over the internal variable label
        variable_combinations = combinations(self.connections.all_variables, 2)
        # Find all pairwise intersections
        variable_aggregations = [
            (a, b)
            for (a, b) in variable_combinations
            if self.connections.all_variables[a].intersection(
                self.connections.all_variables[b]
            )
        ]
        #print(f"variable aggregations in {self.name}: {variable_aggregations}")

        # induced_aggregations = [(a,b) for (a,b) in induced_aggregations if (a is not None and b is not None)]

        variable_aggregation_groups = self.get_aggregation_groups(variable_aggregations)
        self.perform_variable_aggregations(variable_aggregation_groups)
        #print("VARIABLE TRANSLATIONS 1", self.name, parent_variable_translations)
        #print(f"groups = {variable_aggregation_groups}")
        induced_aggregations = [
            [
                parent_node
                for node in group
                if (parent_node := parent_variable_translations.get(node, None)) is not None
            ]
            for group in variable_aggregation_groups
        ]
        #print(f"induced aggregations in parent: {induced_aggregations}")
        """
        variable_intersections is, in effect, variable aggregations to perform.

        I then go to each child, and work out the induced aggregations there, and aggregate those
        with the existing aggregation in the child (what's the best way?)

        Then go back up the chain and action the aggregations, making wires
        """
        variable_translations = {}
        child_connector_ports = {}
        node_port_connections = {}
        for node, connections in self.connections.all_variables.items():
            node_port_connections[node] = set()
            # print(self.name, connections)
            children = {
                address.split(HIERARCHY_SEPARATOR)[0] for address in connections
            }

            connections_by_child = {
                child: [
                    address.split(HIERARCHY_SEPARATOR, 1)[1]
                    for address in connections
                    if address.startswith(child)
                ]
                for child in children
            }

            for child in children:
                child_connector_ports[child] = None

            for child, connections in connections_by_child.items():
                # print(f"CHILD connections in {self.name} from {node} to {child}, connections: {connections}")
                try:
                    child_object = self.children[child]
                except:
                    raise Exception(f"Object {child} is not a child object of {self.name}")
                source_connections = {
                    address
                    for address in connections
                    if len(address.split(HIERARCHY_SEPARATOR)) == 1
                }
                other_connections = {
                    address
                    for address in connections
                    if address not in source_connections
                }

                # other_connections.add(port_address_from_ancestor)

                if len(source_connections) > 1:
                    # We should not be in this case if variables were added properly
                    raise Exception()
                elif len(source_connections) == 1:
                    child_port = source_connections.pop()

                else:
                    child_port = child_object.add_dummy_variable_port()

                # TODO: Check if other_connections?

                child_object.add_variable_connections(
                    {child_port: other_connections},
                )

                child_port_address_in_parent = f"{child}.{child_port}"
                node_port_connections[node].add(child_port_address_in_parent)

                

                variable_translations.setdefault(child, {})
                #CHANGED FROM node to {node} ??
                variable_translations[child].update({child_port: node})
                #print("VARIABLE TRANSLATIONS 2", self.name, variable_translations)
        # print("VARTRANS", variable_translations)
        aggregations_from_children = []
        for child_name, child_object in self.children.items():
            aggregations_from_child, aggregations_in_child = (
                child_object.process_variables(
                    variable_translations.get(child_name, {})
                )
            )
            # print(f"from {child_name}: {induced_aggregations_from_child}")
            if aggregations_from_child:
                for group in aggregations_from_child:
                    aggregations_from_children.append(group)

            # print("NPCS WAS ", node_port_connections)
            # print(aggregations_in_child)
            for connections in node_port_connections.values():
                # print(child_name, connections)
                for address in connections:
                    if address.startswith(child_name):
                        # print(address)
                        _, port = address.split(HIERARCHY_SEPARATOR)
                        new_port = next(
                            (
                                group[0]
                                for group in aggregations_in_child
                                if port in group
                            ),
                            None,
                        )
                        if new_port:
                            connections.remove(address)
                            connections.add(f"{child_name}.{new_port}")

            # print("NPCS IS ", node_port_connections)

        # print(f"Induced aggregations from children in {self.name}: {aggregations_from_children}")

        for node in self.connections.all_variables:

            if node in self.connections.variables:
                if node_port_connections[node]:
                    self.connections.variables[node] = node_port_connections[node]
                else:
                    del self.connections.variables[node]
            else:
                if node_port_connections[node]:
                    self.connections.internal_variables[node] = node_port_connections[
                        node
                    ]
                else:
                    del self.connections.internal_variables[node]

        aggregation_groups_from_children = self.get_aggregation_groups(
            aggregations_from_children
        )
        # print(aggregation_groups_from_children)
        self.perform_variable_aggregations(aggregation_groups_from_children)
        induced_aggregations_groups = [
            [
                parent_node
                for node in group
                if (parent_node := parent_variable_translations.get(node, None)) is not None
            ]
            for group in aggregation_groups_from_children
        ]
        #print("INDUCED AGGR GROUPS", induced_aggregations_groups)

        total_aggregations = self.get_aggregation_groups(
            variable_aggregation_groups + aggregation_groups_from_children
        )

        # print("RETURN", self.name, induced_aggregations_groups + induced_aggregations, total_aggregations)

        return induced_aggregations + induced_aggregations_groups, total_aggregations

    def process_ported_data(self):
        pass

    def add_parameters(self, **parameters):
        self.parameters.set(parameters)

    def initialise_object(self):
        pass


class FunctionalPortedObjectWithConnections(PortedObjectWithConnections):
    add_parameter_assignments = FunctionalPortedObject.add_parameter_assignments
    parse_assignment_entry = FunctionalPortedObject.parse_assignment_entry
    _dump_assignments = FunctionalPortedObject._dump_assignments
    def __init__(
        self,
        name,
        parent=None,
        inputs={},
        output_connections={},
        input_ports=[],
        assignments=[],
        parsing_locals: dict = {},
        **parameters,
    ):
        #print("INPUTS", inputs)
        super().__init__(
            name=name,
            parent=parent,
            inputs=inputs,
            output_connections=output_connections,
            input_ports=input_ports,
            parsing_locals=parsing_locals,
            #ancestor_parameters=self.parent.parameters,
            **parameters,
        )
        #self.initialise_object()

        self.assignments = {}
        self.add_parameter_assignments(*assignments)

    def generate_ported_object(self, parsing_locals = {}):
        self.parsing_locals = parsing_locals
        ported_object = FunctionalPortedObject(
            name=self.name,
            input_ports=self._dump_input_ports(),
            assignments=self._dump_assignments(),
            parsing_locals=self.parsing_locals,
        )

        return ported_object
    
    def expose_outputs(self, object, translations: dict|set = {}):
        """
        Creates output ports in `object` and connections from `self` to `object`.

        If translations is not specified, all parameters on the left-hand side of assignments are exposed as parameters with the same name.

        If translations dict is specified, only the listed parameters are exposed with names according to the (port, target) pairs.

        If translations set is specified, it is converted into a dict of (name, name) pairs for name in set.
        """
        if object not in self.parents.values():
            raise Exception(f"Cannot expose ports from {self.name} to {object.name} because {object.name} is not an ancestor.")
        if not translations:
            translations = {
                (name:=assg.parameter.name): name for assg in self.assignments.values()
            }
        if type(translations) == set:
            translations = {
                name: name for name in translations
            }
        object.add_output_ports(*translations.values())
        for name, target_name in translations.items():
            self.add_output_connection(name, {f"{object.name}.{target_name}"})

        
        


class VariablePortedObjectWithConnections(PortedObjectWithConnections):
    add_variable_assignments = VariablePortedObject.add_variable_assignments
    parse_assignment_entry = VariablePortedObject.parse_assignment_entry
    _dump_assignments = VariablePortedObject._dump_assignments
    def __init__(
        self,
        name,
        parent=None,
        inputs={},
        variable_connections={},
        output_connections={},
        input_ports=[],
        variable_ports=[],
        assignments=[],
        parsing_locals: dict = {},
        **parameters,
    ):
        #print(f"Variable object {name} init with inputs {inputs}")
        super().__init__(
            name=name,
            parent=parent,
            inputs=inputs,
            output_connections=output_connections,
            variable_connections=variable_connections,
            input_ports=input_ports,
            variable_ports=variable_ports,
            parsing_locals=parsing_locals,
            **parameters,
        )
        # self.initialise_object()
        self.assignments = {}
        self.internals = {}
        self.add_variable_assignments(*assignments)
        

    def generate_ported_object(self, parsing_locals = {}):
        self.parsing_locals = parsing_locals
        ported_object = VariablePortedObject(
            name=self.name,
            input_ports=self._dump_input_ports(),
            variable_ports=self._dump_variable_ports(),
            assignments=self._dump_assignments(),
            parsing_locals=self.parsing_locals,
        )

        return ported_object
    
    def expose_variables(self, object, translations: dict = {}):
        """
        Creates variable ports in `object` and connections from `self` to `object`.

        If translations is not specified, all variables on the left-hand side of assignments are exposed as variables with the same name.

        If translations is specified, only the listed variables are exposed with names according to the (port, target) pairs.
        """
        if object not in self.parents.values():
            raise Exception(f"Cannot expose ports from {self.name} to {object.name} because {object.name} is not an ancestor.")
        if not translations:
            #print(self.assignments)
            translations = {
                (name:=assg.variable.name): name for assg in self.assignments.values()
            }
        if type(translations) == set:
            translations = {
                name: name for name in translations
            }
        object.add_variable_ports(*translations.values())
        for name, target_name in translations.items():
            self.add_variable_connection(name, {f"{object.name}.{target_name}"})


class CompositePortedObjectWithConnections(PortedObjectWithConnections):
    def __init__(
        self,
        name,
        parent=None,
        children: list = [],
        inputs={},
        output_connections={},
        variable_connections={},
        input_ports=[],
        output_ports=[],
        variable_ports=[],
        parsing_locals: dict = {},
        wires={},
        **parameters,
    ):
        super().__init__(
            name=name,
            parent=parent,
            children=children,
            inputs=inputs,
            output_connections=output_connections,
            variable_connections=variable_connections,
            input_ports=input_ports,
            output_ports=output_ports,
            variable_ports=variable_ports,
            parsing_locals=parsing_locals,
            **parameters,
        )
        # self.initialise_object()

        """
        CompositePortedObject.__init__(
            self,
            name=name,
            children=children,
            **wires,
            input_ports=input_ports,
            output_ports=output_ports,
            variable_ports=variable_ports,
        )
        """

    def _get_child(self, name: str):
        # TODO: overwrite in psymple. Is there any reason for type() == CompositePortedObject?
        # Parses a string identifier to try to return a child ported object of self
        parts = name.split(HIERARCHY_SEPARATOR, 1)
        if len(parts) == 1:
            if name == self.name:
                return self
            elif name in self.children:
                return self.children[name]
            else:
                raise KeyError(f"{name} is not a child of {self.name}")
        else:
            parent_name, child_name = parts
            #print("PARTS", parent_name, child_name, self.name)
            if parent_name == self.name:
                return self._get_child(child_name)
            elif parent_name in self.children:
                parent = self.children[parent_name]
                #print("NEW PARENT", parent.name)
                if isinstance(
                    parent, CompositePortedObject | PortedObjectWithHierarchy
                ):
                    #print(parent._get_child(child_name).address)
                    return parent._get_child(child_name)
                else:
                    raise TypeError(
                        f"Ported object {parent_name} is of type {type(parent)} and has no children."
                    )
            else:
                raise KeyError(f"{name} is not a child of {self.name}")

    def create_variable_wires(self):
        variable_wires = []
        # Should be called only after variables are processed
        for port, connections in self.connections.variables.items():
            # self.add_variable_wire(connections, port)
            variable_wires.append({"child_ports": connections, "parent_port": port})
            # print(f"VARIABLE WIRE IN {self.name} from {connections} to {port}")
        for name, connections in self.connections.internal_variables.items():
            # self.add_variable_wire(child_ports=connections, output_name=name)
            variable_wires.append({"child_ports": connections, "output_name": name})
            # print(f"VARIABLE WIRE IN {self.name} between {connections} with name {name}")

        return variable_wires

    def create_directed_wires(self):
        """
        INBOUND LEG:

        - remaining parameter connections are to direct (grand)-children
        """
        directed_wires = []

        outbound_connections = {
            port: connections
            for port, connections in self.connections.parameters.items()
            if HIERARCHY_SEPARATOR in port
        }
        inbound_connections = {
            port: connections
            for port, connections in self.connections.parameters.items()
            if port not in outbound_connections
        }

        for child_port, connections in outbound_connections.items():
            directed_wires.append(
                {
                    "source": child_port,
                    "destinations": connections,
                }
            )

        for port, connections in inbound_connections.items():
            # print(self.name, port, connections)
            child_connections = {
                address
                for address in connections
                if len(address.split(HIERARCHY_SEPARATOR)) == 2
            }
            non_child_connections = {
                address for address in connections if address not in child_connections
            }
            child_connector_ports = {}

            for address in child_connections:
                child_name, child_port = address.split(HIERARCHY_SEPARATOR)
                child_object = self.children[child_name]
                if child_port not in child_object.input_ports:
                    pass
                    # raise Exception(f"{child_port} is not in {child_name} input ports")
                child_connector_ports.update({child_name: child_port})

            for address in non_child_connections:
                child_name, target_address = address.split(HIERARCHY_SEPARATOR, 1)
                child_object = self.children[child_name]
                if child_name in child_connector_ports:
                    child_port = child_connector_ports[child_name]
                else:
                    child_port = child_object.add_dummy_input_port()
                    child_connector_ports.update({child_name: child_port})

                # print(f"Connect {target_address} from {child_port} in {child_name}")
                child_object.add_parameter_connections({child_port: target_address})

            wire_destinations = []
            if child_connector_ports:
                wire_destinations = [
                    f"{name}.{port}" for name, port in child_connector_ports.items()
                ]
            if wire_destinations:
                # print(f"WIRE IN {self.name} FROM {port} to {wire_destinations}")
                # self.add_directed_wire(port, wire_destinations)
                directed_wires.append(
                    {
                        "source": port,
                        "destinations": wire_destinations,
                    }
                )
                # directed_wires.update({port: wire_destinations})

        return directed_wires

    def generate_ported_object(self, parsing_locals = {}):
        #print("PARLO", self.address, parsing_locals)
        self.parsing_locals = parsing_locals

        directed_wires = self.create_directed_wires()
        variable_wires = self.create_variable_wires()

        #print(
        #    f"Adding directed wires {directed_wires} and variable wires {variable_wires} to {self.address}"
        #)

        child_objects = [
            child.generate_ported_object(parsing_locals) for child in self.children.values()
        ]

        #print(
        #    f"Adding children to {self.name}", [child.name for child in child_objects]
        #)


        ported_object = CompositePortedObject(
            name=self.name,
            children=child_objects,
            input_ports=self._dump_input_ports(),
            output_ports=self._dump_output_ports(),
            variable_ports=self._dump_variable_ports(),
            directed_wires=directed_wires,
            variable_wires=variable_wires,
            parsing_locals=self.parsing_locals,
        )

        return ported_object
    
    def initialise_object(self):
        for child in self.children.values():
            child.initialise_object()
        super().initialise_object()

    def compile_system_connections(self):

        self.initialise_object()

        self.attribute_parameter_connections()
        self.attribute_variable_connections()

        self.parameter_search()

        self.process_variables()
        self.process_parameters()

    def process_ported_data(self):
        for child in self.children.values():
            child.process_ported_data()

    def expose_outputs(self, object, translations = {}):
        self._expose(object, "output", translations)

    def expose_variables(self, object, translations = {}):
        self._expose(object, "variable", translations)

    def _expose(self, object, port_type, translations = {}):
        if object not in self.parents.values():
            raise Exception(f"Cannot expose ports from {self.name} to {object.name} because {object.name} is not an ancestor.")  
        
        if port_type == "output":
            ports = self.output_ports
            add_ports_function = object.add_output_ports
            add_connection_function = self.add_output_connection
        elif port_type == "variable":
            ports = self.variable_ports
            add_ports_function = object.add_variable_ports
            add_connection_function = self.add_variable_connection
        if not translations:
            translations = {
                name: name for name in ports
            }
        if type(translations) == set:
            translations = {
                name: name for name in translations
            }
        for name, target_name in translations.items():
            add_ports_function(target_name)
            add_connection_function(name, {f"{object.name}.{target_name}"})
