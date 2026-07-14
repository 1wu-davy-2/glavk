from __future__ import annotations

import base64
import json
import os

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from backend.app.transport_crypto import TransportCrypto


def make_client_envelope(transport: TransportCrypto, payload: dict[str, object]) -> dict[str, str]:
    public_key = serialization.load_der_public_key(transport.public_key_der)
    aes_key = AESGCM.generate_key(bit_length=256)
    iv = os.urandom(12)
    ciphertext = AESGCM(aes_key).encrypt(iv, json.dumps(payload).encode("utf-8"), None)
    wrapped_key = public_key.encrypt(
        aes_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    return {
        "version": "v1",
        "wrapped_key": base64.b64encode(wrapped_key).decode("ascii"),
        "iv": base64.b64encode(iv).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
    }


def test_transport_decrypts_client_envelope_and_reencrypts_for_client():
    transport = TransportCrypto()
    client_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client_public = client_private.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    envelope = make_client_envelope(transport, {"username": "admin", "password": "secret"})

    assert transport.decrypt_envelope(envelope) == {"username": "admin", "password": "secret"}
    response_envelope = transport.encrypt_for_client({"username": "admin", "password": "secret"}, client_public)
    assert response_envelope["ciphertext"]
    wrapped = client_private.decrypt(
        base64.b64decode(response_envelope["wrapped_key"]),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    decrypted = AESGCM(wrapped).decrypt(
        base64.b64decode(response_envelope["iv"]),
        base64.b64decode(response_envelope["ciphertext"]),
        None,
    )
    assert json.loads(decrypted) == {"username": "admin", "password": "secret"}


def test_transport_rejects_malformed_envelope():
    with pytest.raises(ValueError, match="凭据数据无效"):
        TransportCrypto().decrypt_envelope({"version": "v1"})
