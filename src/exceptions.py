class InitializedError(Exception):
    """
    Raised when trying to initialize an already initialized object.
    """

class UninitializedError(Exception):
    """
    Raised when trying to interact with an uninitialized object.
    """
