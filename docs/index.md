# Welcome to PyMsgbus

## Table of contents:

- [Introduction](#introduction)
- [Features](#features)
- [Instalation](#instalation)
- [Example](#example)
- [License](#license)

## Introduction

FastAPI is an excellent framework for building RESTful APIs, offering simplicity and efficiency. However, some backend applications require more sophisticated architectures to handle complex business logic. In many cases, straightforward CRUD APIs suffice, where no significant server-side logic is needed—simply exposing a repository interface through a REST controller is enough. No service layer required.

But sometimes the limitations of RESTful APIs become evident. Advanced use cases often demand more complex architectural patterns, such as CQRS or event-driven, in these scenarios, exposing resources from a database is not enough and a strong service layer is needed. This is becoming more common with the rise of IA and ML applications, where servers expose logic instead of resources.

PyMsgbus is a library designed to simplify the creation of the service layer, implementing several messaging patterns and providing a simple and efficient way to implement message-driven systems, using FastAPI's dependency injection system cleaned from all the HTTP logic, to help you decouple your controllers and infrastructure from your services.

This library is not meant to replace FastAPI, but to complement it, enabling a service agnostic transport layer.
and providing a way to implement a strong service layer without controllers logic.
## Features

This library provides:

- A dependency injection system.
- An Event bus to handle your events.
- A Publisher/Subscriber pattern.
- A Producer/Consumer pattern.
- A Service class to handle your commands and queries.
- An Exception class to handle your exceptions.
- A Session class to handle your transactions.

All using the dependency injection system taken from FastAPI in the [fast-depends](https://github.com/Lancetnik/FastDepends) library,
providing a very simple way to create handlers.

## Instalation

To install the package:

```bash
pip install pymsgbus
```

## Example

Create event driven system easily. Define your messages:

```python
from pymsgbus.models import Command, Event, Message, Query
from dataclasses import dataclass

@dataclass
class CreateUser(Command):
    id: str
    name: str

@dataclass
class UpdateUser(Command):
    id: str
    name: str

@dataclass
class UserUpdated(Event):
    id: str
    name: str

@dataclass
class Notification(Message):
    user_id: str
    text: str

@dataclass
class QueryUser(Query):
    id: str

@dataclass
class User:
    id: str
    name: str
```

Define the handlers:

```python
from pymsgbus import Consumer, Subscriber, Service, Depends

consumer = Consumer() 
# Disable automatic casting for this example
# this is needed because we are using dicts as dependencies
# and they get empty when casting. This is not usually needed.
service = Service(cast=False)
subscriber = Subscriber(cast=False)

def database_dependency() -> dict:
    raise NotImplementedError

def notifications_dependency() -> dict:
    raise NotImplementedError


@service.handler
def handle_put_user(command: CreateUser | UpdateUser, database = Depends(database_dependency)):
    database[command.id] = command.name
    consumer.handle(UserUpdated(id=command.id, name=command.name))

@consumer.handler
def consume_user_updated(event: UserUpdated):
    subscriber.receive(Notification(user_id=event.id, text=f'User {event.id} updated with name {event.name}'), 'topic-1') 

@subscriber.handler('topic-1', 'topic-2')
def on_notifications(message: Notification, notifications = Depends(notifications_dependency)):
    notifications[message.user_id] = message.text

@service.handler
def handle_query_user(query: QueryUser, database = Depends(database_dependency)) -> User:
    return User(id=query.id, name=database[query.id])
```

Override the dependencies if you didn't define them already!

```python
nfs = {}
db = {}

def database_adapter():
    return db

def notification_adapter():
    return nfs

service.dependency_overrides[database_dependency] = database_adapter
subscriber.dependency_overrides[notifications_dependency] = notification_adapter
```

Execute your logic:

```python
service.handle(CreateUser(id='1', name='John Doe'))
service.handle(UpdateUser(id='1', name='Jane Doe'))

print(db['1']) # Jane Doe
assert db['1'] == 'Jane Doe'

print(nfs['1']) # User 1 updated with name Jane Doe
assert nfs['1'] == 'User 1 updated with name Jane Doe'

user = service.handle(QueryUser(id='1'))

print(user.id) # '1'
print(user.name) #'1'
```

The `Service` (And `Consumer`) generates a name for each command or query (or event) depending on the class name, so you can use the `execute` method to call them, like this:

```python
service.execute('CreateUser', {'id': '1', 'name': 'John Doe'})
```
You can define in the `Service` constructor and add your own style like kebab-case or snake_case, or a dictionary. This is useful when you want to expose your with some transport layer like FastAPI. For example:

```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from pymsgbus import Service

class Command(BaseModel):
    type: str # "CreateUser" for example could be "create-user"
    payload: dict

class Query(BaseModel):
    type: str
    parameters: dict

api = FastAPI()

def service():
    raise NotImplementedError

@api.post('/commands')
def handle_command(command: Command, service: Service = Depends(service)):
    service.execute(command.type, command.payload)

@api.post('/queries')
def handle_query(query: Query, service: Service = Depends(service)):
    return service.execute(query.type, query.parameters)
```

And that's it. You just created a powerful event-driven system with minimal effort. The HTTP transport layer is completely decoupled from your business logic, and you can override the service port with the one you created.  

## License

This project is licensed under the terms of the MIT license. Feel free to use it in your projects.