from typing import Callable
from typing import Iterator
from typing import Any

class Callbacks[T: Callable]:
    """
    Callbacks is a class that manages a group of callback objects. It is responsible for
    calling the callback objects and returning their results.

    Args:
        *callbacks: A sequence of callback objects.

    Example:

        .. code-block:: python
        class Flushable:
            ## Supose for example that you need to implement a flush method in all callbacks
            ## you pass to a function that will call a callback

            def flush(self):
                print(f'flushing')
                        
        class SomeCallback(Flushable):
            def __call__(self, *args, **kwargs) -> Any:
                return args
                
        class OtherCallback(Flushable):
            def __call__(self, *args, **kwargs) -> Any:
                return kwargs

        # Create an instance of Callbacks with generic type Flushable
        callbacks = Callbacks[Flushable](SomeCallback(), OtherCallback())

        for result in callbacks(1, 2, 3, a=4, b=5, c=6):
            print(result) # (1, 2, 3) 
                          # {'a': 4, 'b': 5, 'c': 6} 
            
        for callback in callbacks:
            callback.flush() # type hinting will work here
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