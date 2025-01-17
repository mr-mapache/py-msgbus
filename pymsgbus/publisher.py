from typing import Callable
from typing import Any
from typing import Protocol

from pymsgbus.depends import inject, Provider
from pymsgbus.depends import Depends as Depends
from pymsgbus.models import Message
        
class Publisher(Protocol):
    
    def register(self, *args):...


class Subscriber:
    """
    A SUBSCRIBER is a component that listens for messages published processes them accordingly.

    Unlike a CONSUMER, a SUBSCRIBER is responsible for processing messages based on the
    topic they were published to. It means that the publisher is responsible for deciding
    which handlers to invoke based on the topic of the message.

    Methods:
        register:
            Registers a message type and its corresponding handler function.

        handler:
            Decorator for registering a handler function to one or more topics.

        receive:
            Receives a message from a given topic and triggers the corresponding handler functions
            to process it.

    Example:

        .. code-block:: python

        from pymsgbus import Subscriber
        from pymsgbus import Publisher
        from pymsgbus import Depends

        subscriber = Subscriber()
        notifications = []
        database = []

        def get_db():
            return database

        @subscriber.handler('topic-1', 'topic-2')
        def callback(message):
            notifications.append(message)

        @subscriber.handler('topic-2')
        def second_callback(message, db = Depends(get_db)): # Like FastAPI's Depends
            database.append(message)
            
        publisher = Publisher()
        publisher.register(subscriber)
        publisher.publish('topic-1', 'Hello')
        publisher.publish('topic-2', 'World')
        assert database == ['World']
        assert notifications == ['Hello', 'World']
    """

    def __init__(self, provider: Provider = None, cast: bool = True) -> None:
        self.handlers = dict[str, list[Callable[[Message | Any], None]]]()
        self.provider = provider or Provider()
        self.cast = cast
        self.key_generator = lambda name: name
    
    @property
    def dependency_overrides(self) -> dict:
        return self.provider.dependency_overrides
    
    def register(self, topic: str, subscriber: Callable[[Message | Any], None]) -> None:        
        """
        Registers a message type and its corresponding handler function.

        Args:
            topic (str): The topic to register.
            subscriber (Callable[[Message], None]): The handler function for the message.
        """
        injected = inject(subscriber, dependency_overrides_provider=self.provider, cast=self.cast)
        self.handlers.setdefault(topic, []).append(injected)
    
    def handler(self, *topics: str) -> Callable[[Message | Any], None]:
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

    def receive(self, message: Message | Any, topic: str):
        """
        Receives a message from a given topic and triggers the corresponding handler functions
        to process it.
        
        Args:
            topic (str): The topic of the message.
            message (Message | Any): The message to process.
        """
        for handler in self.handlers.get(topic, []):
            handler(message)
    
    def subscribe(self, publisher: Publisher):
        """
        Subscribe the subscriber to a given publisher.

        Args:
            publisher (Publisher): the publisher 
        """
        publisher.register(self)

class Publisher:
    """
    A PUBLISHER is a component that publishes messages to a group of SUBSCRIBERS. It is
    responsible for transmitting information between components of an application. 

    Unlike an PRODUCER, a PUBLISHER publishes messages into defined topics, which are then
    received by SUBSCRIBERS that have registered to listen to those topics.

    Methods:
        publish:
            Publishes a message to all registered SUBSCRIBERS.

        register:
            Adds a group of SUBSCRIBERS to the PUBLISHER

    Example:

        .. code-block:: python

        from pymsgbus import Subscriber
        from pymsgbus import Publisher
        subscriber = Subscriber()
        
        ...

        publisher = Publisher()
        publisher.register(subscriber)
        publisher.publish('topic-1', 'Hello')
        publisher.publish('topic-2', 'World')
    """

    def __init__(self) -> None:
        self.subscribers = list[Subscriber]()

    def publish(self, message: Message | Any, topic: str) -> None:
        """
        Publishes a message to all registered SUBSCRIBERS.

        Args:
            topic (str): The topic of the message.
            message (Message | Any): The message to publish.
        """
        for subscriber in self.subscribers:
            subscriber.receive(message, topic)

    def register(self, *subscribers: Subscriber) -> None:
        """
        Adds a group of SUBSCRIBERS to the PUBLISHER.

        Args:
            *subscribers (Subscriber): the subscribers to register
        """
        for subscriber in subscribers:
            self.subscribers.append(subscriber)