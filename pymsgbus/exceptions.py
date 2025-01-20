from typing import Callable
from typing import Any
from inspect import signature
from logging import getLogger

logger = getLogger(__name__)

class Exceptions:
    """
    A context manager for handling exceptions in a more functional way. This context manager allows you to register
    exception handlers for specific exception types. The context manager will call the appropriate handler for the
    raised exception type.

    Example:

        .. code-block:: python

        with Exceptions() as exceptions:
            exceptions.handlers[ValueError] = lambda: print(f'Everything is okay')
            raise ValueError('An error occurred.')

        # Output: Everything is okay
    """
    def __init__(self):
        self.handlers = dict[type[Exception], Callable[..., bool]]()

    def __enter__(self):
        """
        Handles the exception raised in the context manager and calls the appropriate handler. 

        Returns:
            Exceptions:  The Exceptions context manager.
        """
        
        return self
    
    def handle(self, type: type, value: Exception, traceback: Any) -> bool:
        """
        Handles the exception raised in the context manager and calls the appropriate handler. If no handler is found
        for the exception type, return False. If a handler is found, the handler is called with the exception type, value, 
        and traceback as arguments. The handler can have from 0 to 3 parameters. If the handler returns a value that is not
        False, the exception is considered handled and the context manager exits without an exception. If the handler returns
        False, the exception is re-raised. If the handler does not return a value, the exception is considered handled and
        the context manager exits without an exception. If an error occurs while handling the exception the error is logged
        and the exception is re-raised

        Args:
            type (type): The exception type
            value (Exception): The exception value
            traceback (Traceback): The traceback of the exception

        Returns:
            bool: True if the exception is handled, otherwise False.
        """
        handled = False
        if type in self.handlers:
            handler = self.handlers.get(type)
            match len(signature(handler).parameters):
                case 0:
                    handled = handler()
                case 1:
                    handled = handler(value)
                case 2:
                    handled = handler(value, traceback)
                case 3:
                    handled = handler(value, type, traceback)
                case _:
                    raise ValueError("The Exception handler must have from 0 to 3 parameters.")
        return True if handled is not False else False


    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        """
        Handles the exception raised in the context manager and calls the appropriate handler.

        Raises:
            ValueError: If the exception handler has more than 3 parameters.
        """
        if exc_type:
            return self.handle(exc_type, exc_value, traceback)
        return True


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