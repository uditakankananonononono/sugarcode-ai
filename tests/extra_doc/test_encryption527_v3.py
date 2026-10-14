import pytest
from sugarcode.extra_doc.encryption527 import encrypt, decrypt, encrypt_random_nonce

class L(list): pass
class T(tuple): pass
class B(bytes): pass

@pytest.mark.parametrize('operation', [encrypt, decrypt])
@pytest.mark.parametrize('container', [L, T])
def test_request_container_subclasses(operation, container):
    row = (bytes(32), bytes(12), bytes(16), b'aad')
    with pytest.raises(TypeError, match='^exact tuple request required$'):
        operation(container(row))

@pytest.mark.parametrize('operation', [encrypt, decrypt])
@pytest.mark.parametrize('slot', range(4))
def test_request_bytes_subclasses(operation, slot):
    row = [bytes(32), bytes(12), bytes(16), b'aad']; row[slot] = B(row[slot])
    with pytest.raises(TypeError, match='^exact bytes required$'):
        operation(tuple(row))

@pytest.mark.parametrize('container', [L, T])
def test_random_nonce_container_subclasses_before_randomness(monkeypatch, container):
    import os
    monkeypatch.setattr(os, 'urandom', lambda n: pytest.fail('randomness before validation'))
    with pytest.raises(TypeError, match='^exact tuple encryption input required$'):
        encrypt_random_nonce(container((bytes(32), b'data', b'aad')))

@pytest.mark.parametrize('slot', range(3))
def test_random_nonce_bytes_subclasses_before_randomness(monkeypatch, slot):
    import os
    monkeypatch.setattr(os, 'urandom', lambda n: pytest.fail('randomness before validation'))
    row = [bytes(32), b'data', b'aad']; row[slot] = B(row[slot])
    with pytest.raises(TypeError, match='^exact bytes required$'):
        encrypt_random_nonce(tuple(row))
