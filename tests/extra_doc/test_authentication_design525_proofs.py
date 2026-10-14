import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from sugarcode.extra_doc.authentication_design525 import verify_challenge_signature as run


def keypair():
    key=Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    return key,key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)


@pytest.mark.parametrize('n',[16,32,256])
def test_real_signature_and_wrong_key_challenge_signature(n):
    private,public=keypair();challenge=b'a'*n;signature=private.sign(challenge)
    assert run((public,challenge,signature)) is True
    other=Ed25519PrivateKey.from_private_bytes(bytes(reversed(range(32)))).public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    for proof in [(other,challenge,signature),(public,b'b'+challenge[1:],signature),
                  (public,challenge,bytes([signature[0]^1])+signature[1:])]:assert run(proof) is False


@pytest.mark.parametrize('bad',[None,[],{},True,'x'])
def test_outer_type(bad):
    with pytest.raises(TypeError,match='^exact tuple proof required$'):run(bad)


@pytest.mark.parametrize('n',[0,2,4])
def test_arity(n):
    with pytest.raises(ValueError,match='^proof arity must be three$'):run((None,)*n)


@pytest.mark.parametrize('slot',range(3))
@pytest.mark.parametrize('bad',[None,True,1,'x',bytearray(32),memoryview(bytes(32)),[]])
def test_slot_type(slot,bad):
    row=[bytes(32),bytes(16),bytes(64)];row[slot]=bad
    with pytest.raises(TypeError,match='^exact proof bytes required$'):run(tuple(row))


@pytest.mark.parametrize('slot,n',[(0,31),(0,33),(1,15),(1,257),(2,63),(2,65)])
def test_byte_lengths(slot,n):
    row=[bytes(32),bytes(16),bytes(64)];row[slot]=bytes(n)
    with pytest.raises(ValueError,match='^proof byte lengths outside declared range$'):run(tuple(row))
