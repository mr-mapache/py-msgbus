from pymsgbus.publisher import Publisher, Subscriber, Depends

subscriber = Subscriber()
nfs = []
db = []

def get_db():
    return db

@subscriber.handler('topic-1', 'topic-2')
def callback(message):
    nfs.append(message)

@subscriber.handler('topic-2')
def second_callback(message, db = Depends(get_db)):
    print(message)
    db.append(message)
    
def test_publisher():
    publisher = Publisher()
    publisher.register(subscriber)
    publisher.publish('Hello', 'topic-1')
    publisher.publish('World', 'topic-2')
    assert db == ['World']
    assert nfs == ['Hello', 'World']