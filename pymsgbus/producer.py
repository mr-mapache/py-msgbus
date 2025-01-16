from typing import Callable
from typing import Any
from typing import Union
from typing import Optional
from inspect import signature
from collections import deque

from pymsgbus.depends import inject, Provider
from pymsgbus.depends import Depends as Depends
from pymsgbus.models import Event

class Consumer:
    """
    A CONSUMER is a component that listens for and reacts to events within a BOUNDED CONTEXT.
    Consumers are responsible for processing events and triggering side effects in response to them.

    Unlike a SUBSCRIBER, a consumer is responsible for deciding which handlers to invoke based on
    the event type.

    Methods:
        register:
            Registers an event type and its corresponding handler function.

        handler:
            Decorator for registering a handler function for one or more event types.

        consume:
            Consumes an event by invoking its registered handler functions.

    Example:

        .. code-block:: python

        @dataclass
        class UserCreated:
            id: str
            name: str

        @dataclass
        class UserUpdated:
            id: str
            name: str

        consumer = Consumer()

        db = {} # Database
        nfs = [] # Notification flags

        @consumer.handler
        def on_user_created(event: UserCreated | UserUpdated):
            db[event.id] = event
            nfs.append(event)

        producer = Producer()
        producer.register(consumer)
        producer.emit(UserCreated(id='1', name='Alice'))
        producer.emit(UserUpdated(id='1', name='Bob'))
        assert db['1'].name == 'Bob'
        assert nfs[0].name == 'Alice'
        assert nfs[1].name == 'Bob'
    """

    def __init__(self, provider: Provider = None, cast: bool = True):
        self.provider = provider or Provider()
        self.types = dict[str, type[Event]]()
        self.handlers = dict[str, list[Callable[[Event], None]]]()
        self.cast = cast
        self.key_generator = lambda name: name
    
    @property
    def dependency_overrides(self) -> dict:
        return self.provider.dependency_overrides
    
    def register(self, annotation: type, handler: Callable[..., None]) -> None:
        """
        Registers an event type and its corresponding handler function.
        
        Args:
            annotation (type): The event type or Union of event types to register.
            handler (Callable): The handler function for the event.
        """
        if hasattr(annotation, '__origin__'):
            origin = getattr(annotation, '__origin__')
            if isinstance(origin, type(Union)):
                for arg in getattr(annotation, '__args__'):
                    self.register(arg if not hasattr(arg, '__origin__') else getattr(arg, '__origin__'), handler)
            else:
                self.register(origin, handler)

        elif hasattr(annotation, '__args__'):
            for arg in getattr(annotation, '__args__'):
                self.register(arg if not hasattr(arg, '__origin__') else getattr(arg, '__origin__'), handler)
        else:
            key = self.key_generator(annotation.__name__)
            self.types[key] = annotation    
            injected = inject(handler, dependency_overrides_provider=self.provider, cast=self.cast)
            self.handlers.setdefault(key, []).append(injected)


    def handler(self, wrapped: Callable[[Event], Any]) -> Callable[[Event], Any]:
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
        self.register(parameter.annotation, wrapped)
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

    Unlike a PUBLISHER, a producer emits events and the consumers are responsible for deciding
    wich handlers to invoke based on the event type.

    
    Methods:        
        emit:
            Dispatches an event to all registered consumers and processes all pending events in the queue, 
            propagating them to their respective consumers.

        register: 
            Registers a consumer to receive events emitted by the producer.
            
    Example:

        .. code-block:: python
    
        from pymsgbus.producer import Producer, Consumer

        consumer = Consumer()
        producer = Producer()

        ...
    
        producer.register(consumer)
        producer.emit(UserCreated(id='1', name='Alice'))
        ```
    """
    
    def __init__(self):
        self.queue = deque[Event]()
        self.consumers = list[Consumer]()

    def enqueue(self, event: Event):
        """
        Enqueues an event to be processed later by the producer.

        Args:
        
            event (Event): The event to enqueue.
        """
        self.queue.append(event)


    def dequeue(self) -> Optional[Event]:
        """
        Dequeues the next event from the queue. If the queue is empty, this method will return None.

        Returns:
            Event: the next event in the queue or None if the queue is empty.
        """
        return self.queue.popleft() if self.queue else None


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