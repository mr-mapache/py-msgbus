"""
The are situations where "a priori" knowledge of the functions that will be called is not available
in a given domain and the observer pattern is not applicable. In this case, a callback can be injected
into a function or method to act as normal function injected but performing additional logic from the
outside, even grouping multiple callbacks together to be called in sequence.
"""

from typing import Callable
from typing import Iterator
from typing import Any

class Callback[T: Callable]:
    """
    Callbacks is a class that manages a group of callback objects. It is responsible for
    calling the callback objects and returning their results.

    Args:
        callbacks: A sequence of callback objects.

    Example:

        .. code-block:: python

        class Flushable:
            def flush(self):
                print(f'flushing')
                        
        class SomeCallback(Flushable):
            def __call__(self, *args, **kwargs) -> Any:
                return args
                
        class OtherCallback(Flushable):
            def __call__(self, *args, **kwargs) -> Any:
                return kwargs

        callbacks = Callbacks(SomeCallback(), OtherCallback())

        for result in callbacks(1, 2, 3, a=4, b=5, c=6):
            print(result)
            
        for callback in callbacks:
            callback.flush()
    """

    def __init__(self, *callbacks: T):
        """
        Args:
            *callbacks: A sequence of callback objects.
        """
        self.callbacks = callbacks

    def __call__(self, *args, **kwargs) -> tuple[Any]:
        """
        Calls each callback object with the given arguments and keyword arguments.

        Args:
            *args: A sequence of arguments.
            **kwargs: A dictionary of keyword arguments.

        Returns:
            A tuple of results from each callback object.
        """
        return tuple(callback(*args, **kwargs) for callback in self.callbacks)
    
    def __iter__(self) -> Iterator[T]:
        """
        Returns an iterator over the callback objects.
        """
        return iter(self.callbacks)