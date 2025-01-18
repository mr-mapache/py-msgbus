class HandlerNotFound(Exception):
    """Raised when a handler is not found for a message."""
    def __init__(self, message: str = 'Handler not found.'):
        self.message = message
        super().__init__(message)

class TypeNotFound(Exception):
    """Raised when a type is not registered for a given handler."""
    def __init__(self, message: str = 'Type not found.'):
        self.message = message
        super().__init__(message)