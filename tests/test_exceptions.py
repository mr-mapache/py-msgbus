from pytest import raises
from pymsgbus.exceptions import Exceptions


def test_exceptions():
    class TestException(Exception):
        def __init__(self, message):
            super().__init__(message)
            
    exceptions = Exceptions()
    exceptions.handlers[TestException] = lambda: None
    exceptions.handlers[KeyError] = lambda t: None
    exceptions.handlers[ValueError] = lambda t, v: None
    exceptions.handlers[StopIteration] = lambda t, v, tb: None
    exceptions.handlers[TypeError] = lambda: False

    with exceptions:
        raise TestException("Test Exception")
    
    with exceptions:
        raise KeyError("Test KeyError")
    
    with exceptions:
        raise ValueError("Test ValueError")
    
    with exceptions:
        with exceptions:
            raise ValueError("Test ValueError")
    
    with raises(TypeError):
        with exceptions:
            raise TypeError("Test TypeError")
        
    with raises(TypeError):
        with exceptions:
            with exceptions:
                raise TypeError("Test TypeError")