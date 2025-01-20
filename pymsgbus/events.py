from typing import Callable
from typing import Optional
from collections import deque

from pymsgbus.depends import Depends as Depends
from pymsgbus.models import Event
from pymsgbus.exceptions import Exceptions

class Events:
    """
    A simple event bus that allows for events to be enqueued and handled within an AGGREGATE ROOT. This
    class provides a simple way to model domain logic and side effects in an AGGREGATE. The event bus
    allows for events to be enqueued and handled in the order they were enqueued, be handled immediately and
    producing cascades of events.
    
    Methods:

        enqueue:
            Enqueues an event to be handled later with the `commit` method is called.

        dequeue:
            Dequeues the next event from the queue. If the queue is empty, this method will return None.

        handle:
            Handles the event by calling the appropriate handler(s) for the event. If the event is a type, 
            the handler will be called for all events of that type. If the event is an instance, the handler
            will be called for that specific event type.

        commit:
            Handles all events in the queue. This method will dequeue all events in the queue and handle them in the order
            they were enqueued.

        rollback:
            Clears the event queue.
    """
    def __init__(self):
        self.queue = deque[Event]()
        self.handlers = dict[type[Event], Callable[..., None] | list[Callable[..., None]]]()
        self.exceptions = Exceptions()

    def enqueue(self, event: Event):
        """
        Enqueues an event to be handled later with the `commit` method is called.

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


    def handle(self, event: Event):
        """
        Handles the event by calling the appropriate handler(s) for the event. If the event is a type, 
        the handler will be called for all events of that type. If the event is an instance, the handler
        will be called for that specific event type.

        Args:
            event (Event): The event to handle. If the event is a type, the handler will be called for
            all events of that type with without any arguments. If the event is an instance, the handler
            will be called for that specific event type with the event as an argument.
        """
        if isinstance(event, type):
            if isinstance(self.handlers.get(event), list):
                for handler in self.handlers.get(event, []):
                    with self.exceptions:
                        handler()
            else:
                with self.exceptions:
                    self.handlers[event]() if self.handlers.get(event) else None
        else:
            if isinstance(self.handlers.get(type(event)), list):
                for handler in self.handlers.get(type(event), []):
                    with self.exceptions:
                        handler(event)
            else:
                with self.exceptions:
                    self.handlers[type(event)](event)

    def commit(self):
        """
        Handles all events in the queue. This method will dequeue all events in the queue and handle them in the order
        they were enqueued.

        Args:
            event (Event): _description_
        """
        while self.queue:
            event = self.dequeue()
            self.handle(event)

    def rollback(self):
        """
        Clears the event queue.
        """
        self.queue.clear()

    def publish(self, event: Event):
        """
        Publishes an event to the event bus. This method will immediately handle the event and
        commit the event bus. All events of the queue will be handled in the order they were enqueued
        including the event passed to this method.

        Args:
            event (Event): The event to publish.
        """
        self.enqueue(event)
        self.commit()