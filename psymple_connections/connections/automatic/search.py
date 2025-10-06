from ..connection_ported_objects import PortedObjectWithConnections
from .rules import SearchRule



class PortedObjectWithSearch(PortedObjectWithConnections):
    """
    A class that extends PortedObjectWithConnections to include search functionality.
    This class is designed to provide a unified interface for searching for inputs
    in parent objects.

    TODO: Search needs to assume that _process_temp_parameter_connections() has been called
    on all objects before it is called.
    """

    def search_inputs(self, search_rule: dict, skip_inputs = set(), _filter_callback=None):
        # Assume at this point that the interface is fully formed
        # Any port which has been connected to will already have a default value
        search_rule = SearchRule(**search_rule)
        
        missing_inputs = self._get_missing_inputs(search_rule, self.input_ports, skip_inputs)

        if _filter_callback:
            missing_inputs = _filter_callback(missing_inputs)

        print("filtered missing inputs", self.address, missing_inputs)

        self._connect_to_missing_inputs(missing_inputs)

    def _get_missing_inputs(self, search_rule: SearchRule, input_ports: dict, skip_inputs = set()):
        """
        Returns a set of input ports that are missing based on the search rule.
        """
        missing_inputs = {
            port_name
            for port_name, port in input_ports.items()
            if (port.default_value is None)
        } - skip_inputs

        return search_rule.apply(missing_inputs)
    
    def _connect_to_missing_inputs(self, missing_inputs: set[str]):
        """
        Connects to the missing inputs based on the search rule.
        """
        if not self.parent:
            return
        connections = {}
        for port_name in missing_inputs:
            if port_name not in self.parent.input_ports:
                self.parent.add_input_ports(port_name)
            port_address = f"{self.parent.name}.{port_name}"
            connections[port_name] = port_address

        print("ADDING CONNECTIONS", self.address, connections)
        if connections:
            self.add_input_connections(delay_connection_parsing=True, **connections)