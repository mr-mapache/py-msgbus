from pytest import raises
from pymsgbus.session import Session

db = []

def update_db(e):
    db.append('update')
    return True

def rollback_db(e):
    return False

class UOW:
    def __init__(self):
        self.commited = False
        self.rolledback = False
        self.closed = False
        self.started = False
        self.count = 0

    def commit(self):
        self.commited = True

    def rollback(self):
        self.rolledback = True

    def close(self):
        self.closed = True

    def begin(self):
        self.started = True


def test_sessions():
    resource = UOW()

    with Session(resource) as session:
        assert resource.started == True
        session.on(KeyError)(lambda e: update_db(e))
        raise KeyError('test')
    
    assert db[0] == 'update'
    assert resource.commited == True # Since the exception was handled with positive result
    assert resource.closed == True


    resource = UOW()
    with raises(KeyError):
        with Session(resource) as session:
            assert resource.started == True
            session.on(KeyError)(lambda e: rollback_db(e))
            raise KeyError('test')
        assert resource.commited == False # Since the exception was handled with negative or none result
        assert resource.closed == True
    
    with raises(KeyError):
        resource = UOW()
        with Session() as session:
            raise KeyError('test')
        assert resource.closed == True
    

    resource = UOW()
    with Session(resource) as session:
        session.on(KeyError)(lambda: True) # This will not raise any exception and will be commited
        for count in range(10):
            resource.count = count
            if count == 2:
                raise KeyError('test')
            
    assert count == 2
    assert resource.commited == True
    assert resource.closed == True
    assert resource.count == 2
    assert resource.rolledback == False
    
    resource = UOW()
    with Session(resource) as session:
        session.on(KeyError)(lambda: session.commit()) # This will not raise any exception and will be commited
        for count in range(10):
            resource.count = count
            if count == 2:
                raise KeyError('test')
            
    assert count == 2
    assert resource.commited == True
    assert resource.closed == True
    assert resource.count == 2
    assert resource.rolledback == False