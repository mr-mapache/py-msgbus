from pymsgbus.events import Event, Events
from dataclasses import dataclass

@dataclass
class UserCreated(Event):
    name: str

class CLSEvent(Events):
    ...
    
def test_events():
    names = []
    events = Events()
    events.handlers[UserCreated] = lambda event: names.append(event.name)
    events.publish(UserCreated(name="John"))
    assert names == ["John"]
    events.publish(CLSEvent)

    events.handlers[CLSEvent] = lambda: names.append("CLS")
    events.publish(CLSEvent)
    assert names == ["John", "CLS"]
    names = []
    assert not events.queue

    events.enqueue(UserCreated(name="Alice"))
    events.publish(CLSEvent)
    events.commit()
    assert names == ["Alice", "CLS"]
