from psymple.build import HIERARCHY_SEPARATOR

from typing import overload

class AddressAccessedDict(dict):

    def get(self, address, default=None):
        """Retrieve a value from the nested dictionary using a dotted address."""
        keys = address.split(".")
        d = self
        for key in keys:
            if isinstance(d, dict) and key in d:
                d = d[key]
            else:
                return default
        return d
    
    def set(self, values):
        """Set values in the nested dictionary using a dictionary of (address, value) pairs."""
        for address, param in values.items():
            self._set(address, param)

    def _set(self, address, value):
        keys = address.split(".")
        d = self
        for key in keys[:-1]:
            if key not in d or not isinstance(d[key], dict):
                d[key] = {}
            d = d[key]
        d[keys[-1]] = value

    def merge(self, other):
        """Merge another NestedDict into this one, overriding existing values."""
        if not isinstance(other, AddressAccessedDict):
            other = AddressAccessedDict(other)
        def deep_merge(d1, d2):
            for key, value in d2.items():
                if isinstance(value, dict) and isinstance(d1.get(key), dict):
                    deep_merge(d1[key], value)
                else:
                    d1[key] = value
        
        deep_merge(self, other)


"""
TESTS
A = AddressAccessedDict({"a": 1, "b": 2, "c": {"c_1": 3, "c_2": 4}})

B = AddressAccessedDict({"a": 2, "c": {"c_1": 4, "c_2": 4, "c_3": 5}, "d": 12})

print(A.get("a"), A.get("c.c_1"))

B._set("c.c_1.a", 12)

print(A)

A.merge(B)

print(A)
"""

class Parameters(AddressAccessedDict):
    @classmethod
    def from_ancestor(cls, new_params: dict, ancestor_params):
        combined_params = ancestor_params.get("ancestor")
        combined_params.merge(ancestor_params.get("instance"))
        print(combined_params)
        return Parameters(new_params, combined_params)
    
    def __init__(self, new_params = {}, ancestor_params = {}):
        self._set("instance", AddressAccessedDict(new_params))
        self._set("ancestor", AddressAccessedDict(ancestor_params))

    def find(self, address: str, default = None, search_ancestry = True):
        params_search = self.get("instance")
        param_value = params_search.get(address)
        if param_value is None:
            if search_ancestry:
                params_search = self.get("ancestor")
                param_value = params_search.get(address)
                if param_value is None:
                    param_value = default
            elif default is not None:
                param_value = default
            else: 
                raise Exception(f"Parameter with address {address} not found with no default specified.")
                
        return param_value
                

"""
TESTS
P = Parameters({"a": 1, "b": 2, "c": {"c_1": 3, "c_2": 4}}, {"a": 1, "c": {"c_1": 4, "c_3": 5}, "d": 6})

R = Parameters.from_ancestor({"a": 12}, P)

print(R)


print(P)
print(P.get("instance.c.c_1"), P.get("ancestor.c.c_1"))
"""