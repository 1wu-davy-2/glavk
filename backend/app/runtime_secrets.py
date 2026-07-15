from __future__ import annotations

import base64
import os
import secrets
import shlex
from collections.abc import Mapping

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

SECRET_NAMES = (
    "AUTH_SECRET_KEY",
    "CREDENTIAL_ENCRYPTION_KEY",
    "TRANSPORT_PRIVATE_KEY_B64",
)


def _generate_transport_private_key() -> str:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    der = private_key.private_bytes(
        serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return base64.b64encode(der).decode("ascii")


def build_runtime_secrets(values: Mapping[str, str]) -> dict[str, str]:
    return {
        "AUTH_SECRET_KEY": values.get("AUTH_SECRET_KEY") or secrets.token_urlsafe(48),
        "CREDENTIAL_ENCRYPTION_KEY": values.get("CREDENTIAL_ENCRYPTION_KEY")
        or Fernet.generate_key().decode("ascii"),
        "TRANSPORT_PRIVATE_KEY_B64": values.get("TRANSPORT_PRIVATE_KEY_B64") or _generate_transport_private_key(),
    }


def render_shell_env(values: Mapping[str, str]) -> str:
    return "".join(f"{name}={shlex.quote(values[name])}\n" for name in SECRET_NAMES)


def main() -> None:
    print(render_shell_env(build_runtime_secrets(os.environ)), end="")


if __name__ == "__main__":
    main()
