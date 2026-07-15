from __future__ import annotations

import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization

from backend.app.runtime_secrets import build_runtime_secrets, render_shell_env


def test_generates_all_missing_production_secrets():
    values = build_runtime_secrets({})

    assert len(values["AUTH_SECRET_KEY"]) >= 32
    Fernet(values["CREDENTIAL_ENCRYPTION_KEY"].encode("ascii"))
    private_key = serialization.load_der_private_key(
        base64.b64decode(values["TRANSPORT_PRIVATE_KEY_B64"]),
        password=None,
    )
    assert private_key.key_size == 2048


def test_preserves_existing_secrets_and_renders_shell_safe_values():
    existing = {
        "AUTH_SECRET_KEY": "auth secret with spaces and $dollar",
        "CREDENTIAL_ENCRYPTION_KEY": Fernet.generate_key().decode("ascii"),
        "TRANSPORT_PRIVATE_KEY_B64": "existing-transport-key",
    }

    values = build_runtime_secrets(existing)
    rendered = render_shell_env(values)

    assert values == existing
    assert "AUTH_SECRET_KEY='auth secret with spaces and $dollar'" in rendered
    assert "TRANSPORT_PRIVATE_KEY_B64=existing-transport-key" in rendered
