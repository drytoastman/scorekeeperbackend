
class SyncException(Exception):
    pass

class NoDatabaseException(SyncException):
    pass

class NoLocalHostServer(SyncException):
    pass

class DifferentSchemaException(SyncException):
    pass


