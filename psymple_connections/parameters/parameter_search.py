from ..hierarchy.ported_objects import PortedObjectWithHierarchy
from psymple.build.ports import InputPort, OutputPort, VariablePort
from .parameters import AddressAccessedDict

#TODO: need composite parameter search objects

class ParameterSearchObject(PortedObjectWithHierarchy):
    PARSING_DATA = {}
    PORTED_OBJECT_DATA = {}
    def __init__(
        self,
        **data
    ):
        #print("INITIALISING PARAMETER SEARCH OBJECT", data, self.PORTED_OBJECT_DATA)
        ported_object_data = {key: value for key, value in data.items() if key in self.PORTED_OBJECT_DATA}
        super().__init__(
            **ported_object_data
        )  
        parameters = {key: value for key, value in data.items() if key not in self.PORTED_OBJECT_DATA}
        self.parameters = AddressAccessedDict(parameters)
        self._check_parameters()
        #print("ParameterSearchObject", self.address, self.parameters)

    def _check_parameters(self):
        for parameter in self.parameters:
            if parameter in self.input_ports:
                # TODO: Could check if the value is the same as the parameter value
                raise Exception(
                    f"Parameter '{parameter}' is already defined as an input port in {self.address}."
                )
            
    def parse_parameters(self, **parameters):
        parsing_data = self.PARSING_DATA
        #print("PARSING PARAMETERS", parsing_data, parameters)
        for key, value in parameters.items():
            #print("Parsing parameter", self.address, key, value)
            if not value:
                continue
            object_class = parsing_data.get(key)
            #print(object_class, type(value))
            if not object_class:
                raise ValueError(f"Unknown parameter key: {key}")
            if isinstance(value, (list, tuple)):
                for item in value:
                    if isinstance(item, object_class):
                        self.add_children(item)
                    else:
                        raise ValueError(f"Invalid item in {key}: {item}")
            elif isinstance(value, (str, float, int, bool, dict)):
                self.parameters.set(**{key: value})
                #print(self.parameters)
            elif isinstance(value, object_class):
                self.add_children(value)

            # TODO: The logic here can get confused if the object class is str

    #def build_object(self):
    #    pass

    def get_parameter(self, parameter_address: str, default: str|int|float = None, search_ancestry: bool = True):
        #print("SEARCHING FOR PARAMETER", parameter_address, self.address)
        params_search = self.parameters
        parameter_value = params_search.get(parameter_address)
        if (parameter_value is None) and (search_ancestry) and (self.parent):
            parameter_value = self.parent.get_parameter(parameter_address, default, search_ancestry)
        if parameter_value is None:
            if default is not None:
                parameter_value = default
                self.parameters.set(**{parameter_address: default})
            else:
                raise Exception(f"Parameter with address '{parameter_address}' not found in {self.name} with no default specified.")
        return parameter_value
    

class ParameterSearchObjectWithAssignments(ParameterSearchObject):
    pass

