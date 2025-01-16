from typing import Callable
from typing import Union
from typing import Any
from inspect import signature

from pymsgbus.depends import inject, Provider
from pymsgbus.depends import Depends as Depends
from pymsgbus.models import Command, Query

class Service:
    """
    A SERVICE is the technical authority for a business capability. And it is the exclusive
    owner of a certain subset of the business data.  It centralizes and organizes domain
    operations, enforces business rules, and coordinates workflows. 

    Methods:
        register:
            Registers a handler for a specific command or query type. Handles nested or generic annotations.

        handler:
            Decorator for registering a function as a handler for a command or query type.

        execute:
            Executes the handler associated with the given command or query.

    Example:

        .. code-block:: python
        from dataclasses import dataclass
        from pymsgbus import Service
        from pymsgbus.models import Command, Query

        @dataclass
        class CreateUser(Command):
            id: str
            name: str

        @dataclass
        class UpdateUser(Command):
            id: str
            name: str

        @dataclass
        class QueryUser(Query):
            id: str

        @dataclass
        class User:
            id: str
            name: str

        service = Service() # Define a new service
        db = {}

        @service.handler
        def handle_put_user(command: CreateUser[str] | UpdateUser):
            db[command.id] = command.name

        @service.handler
        def handle_query_user(query: QueryUser) -> User: # Performs pydantic validation
            return User(id=query.id, name=db.get(query.id))

        service.execute(CreateUser(id='1', name='Alice'))
        service.execute(UpdateUser(id='1', name='Bob'))
        user = service.execute(QueryUser(id='1'))
        assert user.name == 'Bob'
        assert user.id == '1'
    """
    def __init__(self, provider: Provider = None, cast: bool = True) -> None:
        self.handlers = dict[str, Callable[[Command | Query], None | Any]]()
        self.types = dict[str, Command | Query]()
        self.provider = provider or Provider()
        self.cast = cast
        self.key_generator = lambda name: name

    @property
    def dependency_overrides(self) -> dict:
        return self.provider.dependency_overrides

    def register(self, annotation, handler) -> None:
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
            self.handlers[key] = inject(handler, dependency_overrides_provider=self.provider, cast=self.cast)
    
    def handler(self, wrapped: Callable[..., None | Any]) -> Callable[..., None | Any]:
        """
        Decorator for registering a function as a handler for a command or query type.

        Args:
            wrapped: The function to be registered as a handler.

        Returns:
            The original function, unmodified.
        """
        function_signature = signature(wrapped)
        parameter = next(iter(function_signature.parameters.values()))
        self.register(parameter.annotation, wrapped)
        return wrapped
    
    def execute(self, request: Command | Query) -> None | Any:
        """
        Executes the handler associated with the given command or query.

        Args:
            request: The command or query to be processed.

        Returns:
            The result of the handler function, if any.

        Raises:
            ValueError: If no handler is registered for the given command or query type.
        """
        key = self.key_generator(request.__class__.__name__)
        handler = self.handlers.get(key)
        if handler is None:
            raise ValueError(f'No handler found for {key}')
        return handler(request)