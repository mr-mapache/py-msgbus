from dataclasses import dataclass
from pymsgbus import Service
from pymsgbus.models import Command, Query

@dataclass
class CreateUser[ID](Command):
    id: ID
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

service = Service()
db = {}

@service.handler
def handle_put_user(command: CreateUser[str] | UpdateUser):
    db[command.id] = command.name

@service.handler
def handle_query_user(query: QueryUser) -> User: # Performs pydantic validation
    return User(id=query.id, name=db.get(query.id))

def test_service():
    service.execute(CreateUser(id='1', name='Alice'))
    service.execute(UpdateUser(id='1', name='Bob'))
    user = service.execute(QueryUser(id='1'))
    assert user.name == 'Bob'
    assert user.id == '1'