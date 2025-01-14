from typing import Callable
from typing import Any
from inspect import signature
from collections import deque

from fast_depends import Provider
from fast_depends import inject
from fast_depends import Depends as Depends

class Event:
    """
    An EVENT is a significant occurrence that happens within a system's BOUNDED CONTEXT.
    Events are immutable facts that represent a change in state or a notification of an action.

    This class is intended to be subclassed to define concrete event types
    with the required attributes.
    """
    ...


class Consumer:
    """
    A CONSUMER is a component that listens for and reacts to events within a BOUNDED CONTEXT.
    Consumers are responsible for processing events and triggering side effects in response to them.
    """

    def __init__(self, provider: Provider = None, cast_dependency: bool = True):
        self.provider = provider or Provider()
        self.types = dict[str, type[Event]]()
        self.handlers = dict[str, list[Callable[[Event], None]]]()
        self.cast_dependency = cast_dependency
        self.key_generator = lambda name: name
    
    
    def register(self, event_type: type[Event], consumer: Callable[[Event], None]):
        """
        Registers an event type and its corresponding handler function.

        Args:
            event_type (type[Event]): The type of the event to register.
            consumer (Callable[[Event], None]): The handler function for the event.
        """
        key = self.key_generator(event_type.__name__)
        self.types[key] = event_type
        injected = inject(consumer, dependency_overrides_provider=self.provider, cast=self.cast_dependency)
        self.handlers.setdefault(key, []).append(injected)


    def handler(self, wrapped: Callable[[Event], Any]):
        """
        Decorator for registering a handler function for one or more event types.

        Args:
            wrapped (Callable[[Event], Any]): The handler function to register.

        Returns:
            Callable: The original handler function, unmodified.

        Note:
            If the handler function is annotated with a union of event types,
            all of those types will be registered for the given handler.    
        """
        function_signature = signature(wrapped)
        parameter = next(iter(function_signature.parameters.values()))
        if hasattr(parameter.annotation, '__args__'):
            for message_type in getattr(parameter.annotation, '__args__'):
                self.register(message_type, wrapped)
        else:
            message_type = parameter.annotation
            self.register(message_type, wrapped)
        return wrapped

    def consume(self, event: Event):
        """
        Consumes an event by invoking its registered handler functions.

        Args:
            event (Event): The event to consume.
        """
        key = self.key_generator(event.__class__.__name__)
        for handler in self.handlers.get(key, []):
            handler(event)

class Producer:
    """
    A PRODUCER is a component that emits events within a BOUNDED CONTEXT. It is responsible for
    enqueue events and dispatching them to registered consumers for processing.
    """
    def __init__(self):
        self.queue = deque[Event]()
        self.consumers = list[Consumer]()

    def emit(self, event: Event):
        """
        Dispatches an event to all registered consumers and processes all pending events in the queue,
        propagating them to their respective consumers.

        Args:
            event (Event): _description_
        """
        self.queue.append(event)
        while self.queue:
            event = self.queue.popleft()
            for consumer in self.consumers:
                consumer.consume(event)

    def register(self, consumer: Consumer):
        """
        Registers a consumer to receive events emitted by the producer.

        Args:
            consumer (Consumer): The consumer to register.
        """
        self.consumers.append(consumer)