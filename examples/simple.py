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
    
from pymsgbus import Consumer, Subscriber, Service, Depends

consumer = Consumer() 
service = Service(cast=False) # cast=False disables automatic casting
subscriber = Subscriber(cast=False) # this is necessary since we are using python data structures
                                    # that become empty when casted. Shouldn't be a problem with real
                                    # adapters

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

nfs = {}
db = {}

def database_adapter():
    return db

def notification_adapter():
    return nfs

service.dependency_overrides[database_dependency] = database_adapter
subscriber.dependency_overrides[notifications_dependency] = notification_adapter

service.handle(CreateUser(id='1', name='John Doe'))
service.handle(UpdateUser(id='1', name='Jane Doe'))

print(db['1']) # Jane Doe
assert db['1'] == 'Jane Doe'

print(nfs['1']) # User 1 updated with name Jane Doe
assert nfs['1'] == 'User 1 updated with name Jane Doe'

user = service.handle(QueryUser(id='1'))

print(user.id) # '1'
print(user.name) #'1'