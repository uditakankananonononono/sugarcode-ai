import pytest
from cryptography.exceptions import InvalidTag
from sugarcode.extra_doc.encryption527 import encrypt, decrypt

KEY = bytes(32)
NONCE = bytes(12)


def test_aes256_gcm_nist_zero_block_known_answer():
    # Fixed vector only; reusing this key/nonce is never suitable for production.
    want = bytes.fromhex('cea7403d4d606b6e074ec5d3baf39d18d0d1c8a799996bf0265b98b5d48ab919')
    assert encrypt((KEY,NONCE,bytes(16),b'')) == want
    assert decrypt((KEY,NONCE,want,b'')) == bytes(16)


def test_empty_plaintext_known_answer():
    want = bytes.fromhex('530f8afbc74536b9a963b4f1c4cb738b')
    assert encrypt((KEY,NONCE,b'',b'')) == want
    assert decrypt((KEY,NONCE,want,b'')) == b''


@pytest.mark.parametrize('fn',[encrypt,decrypt])
@pytest.mark.parametrize('bad',[None,[],{},'x',1,True])
def test_request_type(fn,bad):
    with pytest.raises(TypeError,match='^exact tuple request required$'): fn(bad)


@pytest.mark.parametrize('fn',[encrypt,decrypt])
@pytest.mark.parametrize('size',[0,3,5])
def test_request_arity_before_slots(fn,size):
    with pytest.raises(ValueError,match='^request arity must be four$'): fn((None,)*size)


@pytest.mark.parametrize('fn',[encrypt,decrypt])
@pytest.mark.parametrize('slot',range(4))
@pytest.mark.parametrize('bad',[None,True,1,'x',bytearray(b'x'),memoryview(b'x'),[]])
def test_per_slot_exact_bytes(fn,slot,bad):
    row=[KEY,NONCE,bytes(16),b''];row[slot]=bad
    with pytest.raises(TypeError,match='^exact bytes required$'): fn(tuple(row))


@pytest.mark.parametrize('fn',[encrypt,decrypt])
@pytest.mark.parametrize('slot,low,high',[(0,32,32),(1,12,12),(3,0,4096)])
def test_slot_length_cap(fn,slot,low,high):
    for n in ([low-1] if low else [])+[high+1]:
        row=[KEY,NONCE,bytes(16),b''];row[slot]=bytes(n)
        with pytest.raises(ValueError,match='^byte length outside declared range$'):fn(tuple(row))


def test_plaintext_and_ciphertext_caps():
    for n in (0,65536):
        data=bytes(n); token=encrypt((KEY,NONCE,data,b'')); assert decrypt((KEY,NONCE,token,b''))==data
    with pytest.raises(ValueError,match='^byte length outside declared range$'):encrypt((KEY,NONCE,bytes(65537),b''))
    for n in (0,15,65553):
        with pytest.raises(ValueError,match='^byte length outside declared range$'):decrypt((KEY,NONCE,bytes(n),b''))


@pytest.mark.parametrize('aad',[b'',b'a',bytes(4096)])
def test_aad_endpoints_and_tamper(aad):
    token=encrypt((KEY,NONCE,b'payload',aad))
    assert decrypt((KEY,NONCE,token,aad))==b'payload'
    for slot,value in [(0,b'x'*32),(1,b'x'*12),(2,bytes([token[0]^1])+token[1:]),(3,aad+b'x')]:
        if len(value)>4096:continue
        row=[KEY,NONCE,token,aad];row[slot]=value
        with pytest.raises(InvalidTag):decrypt(tuple(row))
