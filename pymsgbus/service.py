from typing import Callable
from typing import Union
from typing import Any
from inspect import signature

from pymsgbus.depends import inject, Provider
from pymsgbus.depends import Depends as Depends
from pymsgbus.exceptions import HandlerNotFound, TypeNotFound

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

        handle:
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

        service.handle(CreateUser(id='1', name='Alice'))
        service.handle(UpdateUser(id='1', name='Bob'))
        user = service.handle(QueryUser(id='1'))
        assert user.name == 'Bob'
        assert user.id == '1'
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
        self.handlers = dict[str, Callable[..., Any]]()
        self.exceptions: dict[type[Exception], Callable[[Exception], None]] = {}
        self.types = dict[str, Any]()
        self.generator = generator
        self.validator = validator
    
    
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
            self.exceptions[exception_type] = handler
            return handler
        return wrapper

    @property
    def dependency_overrides(self) -> dict:
        return self.provider.dependency_overrides

    def register(self, annotation, handler) -> None:
        """
        Register a handler for a given annotation. This method is called recursively to handle nested annotations.
        Don't call this method directly, use the handler decorator instead. This method is called by the handler decorator.

        Args:
            annotation (Any): The annotation to be registered.
            handler (Callable): The handler to be registered.
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
            self.handlers[key] = inject(handler, dependency_overrides_provider=self.provider, cast=self.cast)

    def handler(self, wrapped: Callable[..., Any]) -> Callable[..., Any]:
        """
        Decorator for registering a function as a handler for a a given request type.

        Args:
            wrapped: The function to be registered as a handler.

        Returns:
            The original function, unmodified.
        """
        parameter = next(iter(signature(wrapped).parameters.values()))
        self.register(parameter.annotation, wrapped)
        return wrapped
    

    def validate(self, type: str, payload: Any):
        """
        Validate the payload associated with the given type. The type is used to determine the validator function to be used.
        The validator function defaults to the constructor of the type class. If you are using a validation library like pydantic,
        you can override the validator function to use the pydantic model_validate function.

        Args:
            type (str): The type of the payload to be validated.
            payload (Any): The payload to be validated.

        Raises:
            TypeNotFound: If no handler is registered for the given type.

        Returns:
            The validated payload as an instance of the type class.
        """
        if type not in self.types.keys():
            raise TypeNotFound(f"No handler registered for type: {type}")
        return self.validator(self.types[type], payload)
    
    def handle(self, request: Any) -> Any:
        """
        Handles a request by executing the handler associated with the request type. The handler is determined by the
        generator function provided by the user.

        Args:
            request (Any): The request to be handled. The name of the request class is used to determine the handler to be handled
            using the generator function provided by the user. The generator functions defaults to the name of the request class.

        Raises:
            HandlerNotFound: If no handler is registered for the given request type.

        Returns:
            Any: The result of the handler function.
        """
        action = self.generator(request.__class__.__name__)
        handler = self.handlers.get(action, None)
        if not handler:
            raise HandlerNotFound(f"No handler registered for type: {action}")
        try:
            return handler(request)
        except Exception as exception:
            if type(exception) in self.exceptions:
                return self.exceptions[type(exception)](request, exception)
            else:
                raise exception

    def execute(self, action: str, payload: Any) -> Any:
        """
        Executes the handler associated with the given request action and it's payload. It validates the payload
        asoociated with the action using the validator function provided by the user. The validator function defaults
        to the constructor of the action class. If you are using a validation library like pydantic, you can override
        the validator function to use the pydantic model_validate function.

        Args:
            action: to be handled
            payload: the payload to be passed to the handler
        Returns:
            The result of the handler function, if any.

        Raises:
            TypeNotFound: If no action is registered for the given command or query type.
        """
        request = self.validate(action, payload)
        return self.handle(request)