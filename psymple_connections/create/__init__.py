class psymple_features:
    CONNECTIONS = PortedObjectWithConnections

def create_ported_features_object(*features):
    def create_ported_object(object):
        class object(*features):
            def to_data(self):
                pass
            def compile(self):
                pass
        return object
    return create_ported_object

@create_ported_features_object(psymple_features.CONNECTIONS)
class PortedObjectNew:
    pass

PortedObjectNew(name="hi")