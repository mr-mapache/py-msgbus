from dataclasses import dataclass
from pymsgbus import Depends
from pymsgbus.consumers import Consumer

@dataclass
class UserCreated:
    id: str
    name: str

@dataclass
class UserUpdated:
    id: str
    name: str

consumer = Consumer(cast=True)

db = {} # Database
nfs = [] # Notification flags

@consumer.handler
def on_user_created(event: UserCreated | UserUpdated):
    db[event.id] = event
    nfs.append(event)


def test_producer():
    consumer.handle(UserCreated(id='1', name='Alice'))
    consumer.handle(UserUpdated(id='1', name='Bob'))
    assert db['1'].name == 'Bob'
    assert nfs[0].name == 'Alice'
    assert nfs[1].name == 'Bob'