"""
This module defines the core concepts used in the library. The types defined here are mean to be
optionally subclassed and serve as a reference in definitions and writting self-documented code.

The types defined in this module are:

`Message`: 
    Represents the intention of transmitting information the outside of the BOUNDED CONTEXT.

`Event`: 
    Represents a significant occurrence that happens within a BOUNDED CONTEXT.

`Command`: 
    Represents a directive to perform a specific action or mutation withing an AGGREGATE.

`Query`: 
    Represents a request for information or data from a BOUNDED CONTEXT.

These types are intended to be subclassed to define concrete message types with the required attributes.
"""

from typing import Any

class Message:
    """
    A MESSAGE represents the intention of transmitting information to the outside of
    the BOUNDED CONTEXT.

    It serves as a base class for defining various types of messages, such as events,
    commands, and queries, which facilitate communication in a distributed system.

    Subclass this class to define concrete message types with the required attributes.

    Example:

        .. code-block:: python
        from dataclasses import dataclass    

        @dataclass(slots=True) #just and example can be a normal class
        class Metric(Message):
            name: str
            value: float

    Attributes:
        None explicitly defined. Subclasses should introduce attributes relevant to the
        specific message type. This class is intended for documentation purposes only and
        don't provide any functionality so feel free to use it as you want or ignore it.
    """
    ...

class Event:
    """
    An EVENT is a significant occurrence that happens within a system's BOUNDED CONTEXT.

    Events are immutable facts that represent a change in state or a notification of
    an action. They are used to signal that something noteworthy has occurred, enabling
    other parts of the system or external systems to react accordingly.

    This class is intended to be subclassed to define concrete event types with the
    required attributes.

    Example:

        .. code-block:: python
        
        class OrderPlacedEvent(Event): # Could be a dataclass as well or anything
            def __init__(self, order_id: str, user_id: str, total_amount: float):
                self.order_id = order_id
                self.user_id = user_id
                self.total_amount = total_amount

            def __repr__(self):
                return f"OrderPlacedEvent(order_id={self.order_id}, user_id={self.user_id}, total_amount={self.total_amount})"

    Attributes:
        None explicitly defined. Subclasses should introduce attributes relevant to the
        specific event type. This class is intended for documentation purposes only and
        don't provide any functionality so feel free to use it as you want or ignore it.
    """
    ...

class Command:
    """
    A COMMAND is a directive to perform a specific action or operation in a system.

    Commands represent an intent to change the state of the system. Unlike events, commands
    are direct requests for actions or mutations on an AGGREGATE to be taken and are
    typically processed by a single recipient, and they belong to the service layer.

    This class is intended to be subclassed to define concrete command types with the
    required attributes.

    Example:

        .. code-block:: python
    
        class CreateUserCommand(Command): # Could be a dataclass as well or anything
            def __init__(self, user_id: str, name: str):
                self.user_id = user_id
                self.name = name

            def __repr__(self):
                return f"CreateUserCommand(user_id={self.user_id}, name={self.name})"

    Attributes:
        None explicitly defined. Subclasses should introduce attributes relevant to the
        specific command type. This class is intended for documentation purposes only and
        don't provide any functionality so feel free to use it as you want or ignore it.
    """
    ...

    def execute(self) -> Any:
        """
        Execute the command. This method may be overridden in subclasses to provide
        a default implementation for the command's execution. 

        Returns:
            Any: The result of the command execution
        """
        raise NotImplementedError("An `execute` method must be provided.")

class Query:
    """
    A QUERY is a request for information or data from a system's BOUNDED CONTEXT.

    Queries do not modify the state of the system; they are read-only operations intended
    to retrieve the current state or computed results based on the state of the system.

    This class is intended to be subclassed to define concrete query types with the
    required attributes.

    Example:

        .. code-block:: python
    
        class GetUserQuery(Query): # Could be a dataclass as well or anything
            def __init__(self, user_id: str):
                self.user_id = user_id

            def __repr__(self):
                return f"GetUserQuery(user_id={self.user_id})"

    Attributes:
        None explicitly defined. Subclasses should introduce attributes relevant to the
        specific query type. This class is intended for documentation purposes only and
        don't provide any functionality so feel free to use it as you want or ignore it.
    """
    ...