import pytest
from sugarcode.extra_doc.encryption527 import encrypt_random_nonce as run, decrypt


def test_os_nonce_length_payload_and_aad_forwarding(monkeypatch):
    import os
    calls=[]
    def fake(n):calls.append(n);return b'x'*n
    monkeypatch.setattr(os,'urandom',fake)
    for data,aad in [(b'',b''),(b'payload',b'context'),(bytes(65536),bytes(4096))]:
        nonce,token=run((bytes(32),data,aad))
        assert nonce==b'x'*12 and len(token)==len(data)+16
        assert decrypt((bytes(32),nonce,token,aad))==data
    assert calls==[12,12,12]


@pytest.mark.parametrize('bad',[None,[],True,'x',{}])
def test_outer(bad):
    with pytest.raises(TypeError,match='^exact tuple encryption input required$'):run(bad)


@pytest.mark.parametrize('n',[0,2,4])
def test_arity(n):
    with pytest.raises(ValueError,match='^encryption input arity must be three$'):run((None,)*n)


@pytest.mark.parametrize('slot',range(3))
@pytest.mark.parametrize('bad',[None,True,1,'x',bytearray(32),[]])
def test_types_before_randomness(monkeypatch,slot,bad):
    import os
    monkeypatch.setattr(os,'urandom',lambda n:pytest.fail('randomness before validation'))
    row=[bytes(32),b'',b''];row[slot]=bad
    with pytest.raises(TypeError,match='^exact bytes required$'):run(tuple(row))


@pytest.mark.parametrize('slot,n',[(0,31),(0,33),(1,65537),(2,4097)])
def test_caps_before_randomness(monkeypatch,slot,n):
    import os
    monkeypatch.setattr(os,'urandom',lambda n:pytest.fail('randomness before validation'))
    row=[bytes(32),b'',b''];row[slot]=bytes(n)
    with pytest.raises(ValueError,match='^byte length outside declared range$'):run(tuple(row))
