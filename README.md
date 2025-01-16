# Welcome to pymsgbus

## Table of contents:

- [Introduction](#introduction)
- [Instalation](#instalation)
- [Documentation](#documentation)
- [Example](#example)
- [License](#license)

## Introduction

pymsgbus is a Python library designed to simplify the creation of event-driven systems. With features like dependency injection, message-based architecture, and seamless data validation via Pydantic, it empowers developers to build scalable and maintainable systems with minimal effort.

## Instalation

To install the package:

```bash
pip install pymsgbus
```

## Documentation

The documentation is available at [mr-mapache.github.io/py-msgbus/](https://mr-mapache.github.io/py-msgbus/) and it contains detailed information about the library's features and how to use them. It also explains the core concepts behind the library.

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
    consumer.consume(UserUpdated(id=command.id, name=command.name))

@consumer.handler
def consume_user_updated(event: UserUpdated):
    subscriber.receive('topic-1', Notification(user_id=event.id, text=f'User {event.id} updated with name {event.name}')) 

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
service.execute(CreateUser(id='1', name='John Doe'))
service.execute(UpdateUser(id='1', name='Jane Doe'))

print(db['1']) # Jane Doe
assert db['1'] == 'Jane Doe'

print(nfs['1']) # User 1 updated with name Jane Doe
assert nfs['1'] == 'User 1 updated with name Jane Doe'

user = service.execute(QueryUser(id='1'))

print(user.id) # '1'
print(user.name) #'Jane Doe'
```

And just like that, you've implemented a powerful event-driven system with minimal setup!. 


## License

This project is licensed under the terms of the MIT license. Feel free to use it in your projects.