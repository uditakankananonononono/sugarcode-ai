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


class L525(list): pass
class T525(tuple): pass
class B525(bytes): pass


@pytest.mark.parametrize('container', [L525, T525])
def test_proof_container_subclass_v3(container):
    _, public = keypair()
    with pytest.raises(TypeError, match='^exact tuple proof required$'):
        run(container((public, bytes(16), bytes(64))))


@pytest.mark.parametrize('slot', range(3))
def test_proof_bytes_subclass_v3(slot):
    _, public = keypair()
    proof = [public, bytes(16), bytes(64)]; proof[slot] = B525(proof[slot])
    with pytest.raises(TypeError, match='^exact proof bytes required$'):
        run(tuple(proof))


@pytest.mark.parametrize('n', [16, 32, 256])
def test_identity_universal_forgery_refused_v3(n):
    public = (1).to_bytes(32, 'little')
    with pytest.raises(ValueError, match='^small-order public key refused$'):
        run((public, b'a' * n, public + bytes(32)))


@pytest.mark.parametrize('encoded', ['0100000000000000000000000000000000000000000000000000000000000000', 'c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a', '0000000000000000000000000000000000000000000000000000000000000080', '26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05', 'ecffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f', '26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85', '0000000000000000000000000000000000000000000000000000000000000000', 'c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa'])
def test_all_eight_torsion_public_keys_refused_v3(encoded):
    public = bytes.fromhex(encoded)
    with pytest.raises(ValueError, match='^small-order public key refused$'):
        run((public, bytes(16), public + bytes(32)))
