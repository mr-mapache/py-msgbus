from typing import Callable
from typing import Any
from typing import Union
from typing import Protocol
from inspect import signature

from pymsgbus.depends import inject, Provider
from pymsgbus.depends import Depends as Depends
from pymsgbus.exceptions import TypeNotFound
from pymsgbus.exceptions import Exceptions

class Producer(Protocol):
    """
    A PRODUCER is any component that produces messages within a BOUNDED CONTEXT. A producer is responsible for
    emitting EVENTS that are consumed by consumers. You can implement a producer implementing the `register`
    method to register consumers, and some delivery mechanism to deliver the events to them.

    Example:

        .. code-block:: python

        from pymsgbus import Consumer

        class Repository:
            def __init__(self, id: str, name: str):
                self.id = id
                self.name = name
                self.consumers = Consumers()

            def register(self, consumer: Consumer):
                self.consumers.append(consumer)

            def save(self, aggregate: Aggregate):
                for consumer in self.consumers:
                    consumer.consume('AggregateSaved', aggregate)
    """

    def register(self, *args):
        ...

class Consumer:
    """
    A CONSUMER is a component that listens for and reacts to events or certain types of messages 
    within a BOUNDED CONTEXT. Consumers are responsible for processing events and triggering side
    effects in response to them.

    Unlike a SUBSCRIBER, a consumer is responsible for deciding which handlers to invoke based on
    the message type.

    Methods:
        register:
            Registers a message type and its corresponding handler function.

        handler:
            Decorator for registering a handler function for one or more message types.

        handle:
            Consumes a message by invoking its registered handler functions.
        
        consume:
            Consumes an occurrence of the given event type with the given payload. This method validates the payload
            and invokes the corresponding handler functions.

        listen:
            Register this consumer to a given producer. An event producer could be any class
            that implements the `Producer` protocol with a `register` method.
            
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
        producer.publish(UserCreated(id='1', name='Alice'))
        producer.publish(UserUpdated(id='1', name='Bob'))
        assert db['1'].name == 'Bob'
        assert nfs[0].name == 'Alice'
        assert nfs[1].name == 'Bob'
    """
    def __init__(
        self, 
        name: str = None,
        cast: bool = True,
        provider: Provider = None, 
        generator: Callable[[str], str] = lambda name: name,
        validator: Callable[[Any, Any], Any] = lambda type, payload: type(**payload)
    ):
        """
        Initializes a new instance of the Subscriber class.

        Args:
            name (str, optional): The name of the subscriber. Defaults to None.
            cast (bool, optional): Casting dependencies during dependency injection. Defaults to True.
            provider (Provider, optional): . The dependency provider for dependency injection. Defaults to None.
            generator (Callable[[str], str], optional): The generator function for generating the handler key. Defaults to lambda name: name.
            validator (Callable[[Any, Any], Any], optional): The validator function for validating the payload. Defaults to lambda type, payload: type(**payload).
        """
        self.name = name
        self.provider = provider or Provider()
        self.cast = cast
        self.handlers = dict[str, list[Callable[[Any], None]]]()
        self.types = dict[str, Any]()
        self.generator = generator
        self.validator = validator
        self.exceptions = Exceptions()
    
    def listen(self, producer: Producer):
        """
        Registers this consumer with a given producer. An event producer could be an `Events` instance or
        any class that implements the `Producer` protocol with a `register` method.

        Args:
            producer (Producer): The producer to register this consumer with.
        """
        producer.register(self)

    @property
    def dependency_overrides(self) -> dict:
        return self.provider.dependency_overrides

    def validate(self, type: str, payload: Any):
        """
        Validate the payload associated with the given type. The type is used to determine the validator function to be used.
        The validator function defaults to the constructor of the type class. If you are using a validation library like pydantic,
        you can override the validator function to use the pydantic model_validate function.

        Args:
            type (str): The type of the payload to be validated.
            payload (Any): The payload to be validated.

        Raises:
            TypeNotFound: If the type is not registered.

        Returns:
            The validated payload as an instance of the type class.
        """
        if type not in self.types.keys():
            raise TypeNotFound(f"The type {type} is no registered")
        return self.validator(self.types[type], payload)
    

    def register(self, annotation: Any, handler: Callable[..., None]) -> None:
        """
        Register a handler for a given annotation. This method is called recursively to handle nested annotations.
        Don't call this method directly, use the handler decorator instead. This method is called by the handler decorator.
        
        Args:
            annotation (Any): The annotation to register.
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
            key = self.generator(annotation.__name__)
            self.types[key] = annotation    
            injected = inject(handler, dependency_overrides_provider=self.provider, cast=self.cast)
            self.handlers.setdefault(key, []).append(injected)


    def handler(self, wrapped: Callable[..., None]) -> Callable[..., None]:
        """
        Decorator for registering a handler function for one or more event types.

        Args:
            wrapped (Callable[..., None]): The handler function to register.

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

    def handle(self, event: Any):
        """
        Handles an event by invoking its registered handler functions.

        Args:
            event (Event): The event to handle.
        """
        with self.exceptions:
            key = self.generator(event.__class__.__name__)
            for handler in self.handlers.get(key, []):
                handler(event)

    def consume(self, event_type: str, payload: Any):
        """
        Consumes an occurrence of the given event type with the given payload.
        This method validates the payload and invokes the corresponding handler functions.

        Args:
            occurrence (str): The event type to consume.
            payload (Any): The event payload to consume.
        """
        if event_type in self.types.keys():
            event = self.validate(event_type, payload)
            self.handle(event(**payload))

            
    
    def on(self, exception_type: type[Exception]):
        """
        Decorator for registering a handler for a given exception type. The handler is called when an exception of
        the given type is raised.

        Args:
            exception_type (type[Exception]): The type of the exception to be handled.
        
        Returns:
            The handler function.
        """
        def wrapper(handler: Callable[[Any, Exception], Any]) -> bool:
            self.exceptions.handlers[exception_type] = handler
            return handler
        return wrapper