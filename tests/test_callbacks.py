from pymsgbus.callbacks import Callback

class Flushable:
    def flush(self):
        print(f'flushing')
                
class SomeCallback(Flushable):
    def __call__(self, *args, **kwargs):
        return args
        
class OtherCallback(Flushable):
    def __call__(self, *args, **kwargs):
        return kwargs

callbacks = Callback[Flushable](SomeCallback(), OtherCallback())

def test_callbacks():
    results = callbacks(1, 2, 3, a=4, b=5, c=6)
    assert results == ((1, 2, 3), {'a': 4, 'b': 5, 'c': 6})
    for result in results:
        assert result == (1, 2, 3) or result == {'a': 4, 'b': 5, 'c': 6}