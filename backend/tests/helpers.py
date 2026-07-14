from __future__ import annotations

import base64
import json
import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi.testclient import TestClient


def make_envelope(public_key_b64: str, payload: dict[str, object]) -> dict[str, str]:
    public_key = serialization.load_der_public_key(base64.b64decode(public_key_b64))
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


def login_payload(client: TestClient, username: str = "admin", password: str = "admin@123") -> dict[str, object]:
    key = client.get("/api/security/transport-key").json()["public_key"]
    return {"credential_envelope": make_envelope(key, {"username": username, "password": password})}
