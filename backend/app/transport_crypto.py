from __future__ import annotations

import base64
import json
import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class TransportCrypto:
    def __init__(self, private_key_b64: str = ""):
        if private_key_b64:
            try:
                loaded = serialization.load_der_private_key(base64.b64decode(private_key_b64), password=None)
            except Exception as error:
                raise RuntimeError("TRANSPORT_PRIVATE_KEY_B64 无效") from error
            if not isinstance(loaded, rsa.RSAPrivateKey):
                raise RuntimeError("TRANSPORT_PRIVATE_KEY_B64 必须是 RSA 私钥")
            self._private_key = loaded
        else:
            self._private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    @property
    def public_key_der(self) -> bytes:
        return self._private_key.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    @property
    def public_key_b64(self) -> str:
        return base64.b64encode(self.public_key_der).decode("ascii")

    def decrypt_envelope(self, envelope: dict[str, str]) -> dict[str, object]:
        try:
            if envelope.get("version") != "v1":
                raise ValueError
            wrapped_key = base64.b64decode(envelope["wrapped_key"], validate=True)
            iv = base64.b64decode(envelope["iv"], validate=True)
            ciphertext = base64.b64decode(envelope["ciphertext"], validate=True)
            if len(iv) != 12 or not ciphertext:
                raise ValueError
            aes_key = self._private_key.decrypt(
                wrapped_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            payload = json.loads(AESGCM(aes_key).decrypt(iv, ciphertext, None).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError
            return payload
        except Exception as error:
            raise ValueError("凭据数据无效") from error

    def encrypt_for_client(self, payload: dict[str, object], client_public_key_der: bytes) -> dict[str, str]:
        try:
            public_key = serialization.load_der_public_key(client_public_key_der)
            if not isinstance(public_key, rsa.RSAPublicKey):
                raise ValueError
            aes_key = AESGCM.generate_key(bit_length=256)
            iv = os.urandom(12)
            ciphertext = AESGCM(aes_key).encrypt(iv, json.dumps(payload).encode("utf-8"), None)
            wrapped_key = public_key.encrypt(
                aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            return {
                "version": "v1",
                "wrapped_key": base64.b64encode(wrapped_key).decode("ascii"),
                "iv": base64.b64encode(iv).decode("ascii"),
                "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
            }
        except Exception as error:
            raise ValueError("客户端公钥无效") from error
