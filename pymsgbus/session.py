"""
This module is a framework for managing transactions across multiple resources, inspired by the
SQLAlchemy library. It provides a mechanism for coordinating transactional operations, ensuring
data integrity and reliability in complex workflows.

The core concept of this module is the `Session` class, which represents a session for managing
transactions with one or more resources. Sessions are used to group multiple operations into a
single transaction that can be committed or rolled back as a unit. Custom exception handlers can
be registered to handle specific exceptions that occur during the session to avoid rolling back
the transaction. This is useful for early stopping in loops or other scenarios where an exception
is expected and should not cause the transaction to fail.

In order to use the `Session` class, you need to define a resource that implements the `Resource`
interface. Resources are objects that can handle transactions and provide access to data or services.
"""


from typing import Protocol
from typing import Callable
from typing import Optional
from logging import getLogger
from inspect import signature

logger = getLogger(__name__)

class Resource(Protocol):
    """
    Represents an interface (Protocol) for resources. Resources are objects that can handle
    transactions and provide access to data or services.
    """
    ...
    def begin(self):
        """
        Begins a transaction. This method should be called before any other
        transactional methods are invoked.
        """
        ...

    def commit(self):
        """
        Commits the current transaction. This method should be called after all
        transactional methods have been invoked successfully.
        """
        ...

    def rollback(self):
        """
        Rolls back the current transaction. This method should be called if an
        error occurs during the transaction.
        """
        ...

    def close(self):
        """
        Closes the resource. This method should be called after all transactions
        have been completed.
        """
        ...

class Session:
    """
    Represents a session for managing transactions with a resource. Sessions are used
    to group multiple operations into a single transaction that can be committed or
    rolled back as a unit.

    Custom exception handlers can be registered to handle specific exceptions that
    occur during the session to avoid rolling back the transaction. This is useful
    for example for early stopping in loops.

    Attributes:
        *args: Variable length argument list with resource instances. 

    Methods:
        begin(self) -> None:
            Begins a transaction with the resource.

        commit(self) -> None:
            Commits the current transaction with the resource.

        rollback(self) -> None:
            Rolls back the current transaction with the resource.

        close(self) -> None:
            Closes the session and releases the resource.

    Example:

        .. code-block:: python

        from pybondi import Session
        
        with Session(sqlalchemy, rabbitmq) as session: # Handle the resources you want!
            session.on(StopIteration)(lambda: session.commit()) # If StopIteration is raised, commit the transaction
            repository.put(model)
            publisher.publish(event)
            for epoch in range(10):
                if epoch == 2:
                    raise StopIteration("Early stopping") # Session will commit all resources in epoch 2
                                                          # since we added a handler for StopIteration
        with Session(sqlalchemy) as session:
            repository.put(another_model)
            raise Exception("Something went wrong") # Session will rollback all resources
                                                    # to the state where they were committed
    """
    def __init__(self, *args: Resource):
        """
        Initializes a new session with the given resources.

        Args:
            *args: Variable length argument list with resource instances.
        """
        self.resources = args
        self.handler: dict[type[BaseException], Callable[[Optional[BaseException]], bool]] = {}

    def on(self, exception: type[BaseException]) -> Callable:
        """
        Registers an exception handler for the given exception type.

        Args:
            exception: The type of exception to handle.

        Returns:
            A decorator that registers the exception handler.
        """
        def decorator(handler: Callable[[Optional[BaseException]], bool]):
            self.handler[exception] = handler
        return decorator

    def __enter__(self):
        """
        Begins a transaction with the resource. This method should be called
        """
        for resource in self.resources:
            resource.begin()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        """
        Handles the session's lifecycle, including invoking exception handlers if an exception occurs.
        if a handler exists for the exception type, non exception will be raised else the exception will be raised.
        if the exception handler returns True, the transaction will be committed, otherwise it will be rolled back.

        Args:
            exc_type (Any): The type of the exception raised.
            exc_value (Any): The exception instance raised.
            traceback (Any): The traceback object.

        """
        if exc_type:
            result = False
            commit = False
            if exc_type in self.handler:
                result = True
                try:
                    handler_signature = signature(self.handler[exc_type])
                    if len(handler_signature.parameters) == 0:
                        commit = self.handler[exc_type]()
                    else:
                        commit = self.handler[exc_type](exc_value)
                except Exception as error:
                    logger.error(f"Error while handling exception: {error}")
                    commit = False
                    result = False
        else:
            result = True
            commit = True

        if commit:
            for resource in self.resources:
                resource.commit()
        else:
            for resource in self.resources:
                resource.rollback()

        for resource in self.resources:
            resource.close()
        return result
    
    def commit(self) -> bool:
        """
        Commits the current transaction with the resource.

        Returns:
            True in order to indicate that the transaction was committed successfully.
        """
        for resource in self.resources:
            resource.commit()
        return True

    def rollback(self) -> bool:
        """
        Rolls back the current transaction with the resource.

        Returns:
            False in order to indicate that the transaction was rolled back.
        """
        for resource in self.resources:
            resource.rollback()
        return False