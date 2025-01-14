from typing import Callable
from typing import Any
from fast_depends import Provider
from fast_depends import inject
from fast_depends import Depends as Depends

class Message:
    """
    A MESSAGE is an intention of transmitting information from within an Aggregate
    to the outside of the BOUNDED CONTEXT.

    This class is intended to be subclassed to define concrete message types
    with the required attributes.
    """
    ...

class Subscriber:
    """
    A SUBSCRIBER is a component that listens for messages published by an Aggregate and
    processes them accordingly.
    """

    def __init__(self, provider: Provider = None, cast: bool = True) -> None:
        self.handlers = dict[str, list[Callable[[Message | Any], None]]]()
        self.provider = provider or Provider()
        self.cast = cast
        self.key_generator = lambda name: name
    
    
    def register(self, topic: str, subscriber: Callable[[Message | Any], None]) -> None:        
        """
        Registers a message type and its corresponding handler function.

        Args:
            topic (str): The topic to register.
            subscriber (Callable[[Message], None]): The handler function for the message.
        """
        injected = inject(subscriber, dependency_overrides_provider=self.provider, cast=self.cast)
        self.handlers.setdefault(topic, []).append(injected)

    def subscribe(self, *topics: str):
        """
        Decorator for registering a handler function to one or more topics.

        Args:
            topics (str): The topics to subscribe to.

        Returns:
            Callable: The original handler function, unmodified.
        """
        def decorator(wrapped: Callable[[Message | Any], None]):
            for topic in topics:
                self.register(topic, wrapped)
            return wrapped
        return decorator

    def receive(self, topic: str, message: Message | Any):
        """
        Receives a message from a given topic and triggers the corresponding handler functions
        to process it.
        
        Args:
            topic (str): The topic of the message.
            message (Message | Any): The message to process.
        """
        for handler in self.handlers.get(topic, []):
            handler(message)

class Publisher:
    """
    A PUBLISHER is a component that publishes messages to a group of SUBSCRIBERS.
    """

    def __init__(self) -> None:
        self.subscribers = list[Subscriber]()

    def publish(self, topic: str, message: Message | Any) -> None:
        """
        Publishes a message to all registered SUBSCRIBERS.

        Args:
            topic (str): The topic of the message.
            message (Message | Any): The message to publish.
        """
        for subscriber in self.subscribers:
            subscriber.receive(topic, message)

    def register(self, *subscribers: Subscriber) -> None:
        """
        Adds a group of SUBSCRIBERS to the PUBLISHER.

        Args:
            subscriber (Subscriber): The subscriber to subscribe.
        """
        for subscriber in subscribers:
            self.subscribers.append(subscriber)