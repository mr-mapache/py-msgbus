from pymsgbus.publisher import Publisher, Subscriber, Depends

subscriber = Subscriber()
nfs = []
db = []

def get_db():
    return db

@subscriber.subscribe('topic-1', 'topic-2')
def callback(message):
    nfs.append(message)

@subscriber.subscribe('topic-2')
def second_callback(message, db = Depends(get_db)):
    print(message)
    db.append(message)
    
def test_publisher():
    publisher = Publisher()
    publisher.register(subscriber)
    publisher.publish('topic-1', 'Hello')
    publisher.publish('topic-2', 'World')
    assert db == ['World']
    assert nfs == ['Hello', 'World']