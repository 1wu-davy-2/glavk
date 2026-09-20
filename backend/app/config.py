from __future__ import annotations

import os
import base64
import hashlib
from dataclasses import dataclass, field
from urllib.parse import quote_plus


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _build_database_url() -> str:
    """Prefer DB_HOST/DB_PORT/DB_USER/DB_PASSWORD; password is percent-encoded,
    so values containing @ : / ? # etc. are safe. Falls back to DATABASE_URL."""
    host = os.getenv("DB_HOST", "").strip()
    if not host:
        return os.getenv(
            "DATABASE_URL",
            "mysql+pymysql://glavk_user:change-me@127.0.0.1:3307/glavk?charset=utf8mb4",
        )
    user = os.getenv("DB_USER", "").strip()
    password = os.getenv("DB_PASSWORD", "")
    port = os.getenv("DB_PORT", "3306").strip() or "3306"
    name = os.getenv("DB_NAME", "glavk").strip() or "glavk"
    return (
        "mysql+pymysql://"
        f"{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}?charset=utf8mb4"
    )


@dataclass(frozen=True)
class Settings:
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    database_url: str = field(default_factory=_build_database_url)
    auth_secret_key: str = field(
        default_factory=lambda: os.getenv("AUTH_SECRET_KEY", "change-this-secret-key")
    )
    auth_token_ttl_days: int = field(
        default_factory=lambda: max(1, int(os.getenv("AUTH_TOKEN_TTL_DAYS", "30")))
    )
    credential_encryption_key: str = field(
        default_factory=lambda: os.getenv("CREDENTIAL_ENCRYPTION_KEY", "")
    )
    transport_private_key_b64: str = field(
        default_factory=lambda: os.getenv("TRANSPORT_PRIVATE_KEY_B64", "")
    )
    admin_username: str = field(default_factory=lambda: os.getenv("ADMIN_USERNAME", "admin"))
    admin_password: str = field(default_factory=lambda: os.getenv("ADMIN_PASSWORD", "admin@123"))
    admin_password_hash: str = field(default_factory=lambda: os.getenv("ADMIN_PASSWORD_HASH", ""))
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            item.strip()
            for item in os.getenv("CORS_ORIGINS", "http://localhost:6222,http://127.0.0.1:6222,http://localhost:5173").split(",")
            if item.strip()
        )
    )
    screenshot_dir: str = field(default_factory=lambda: os.getenv("SCREENSHOT_DIR", "./data/screenshots"))
    screenshot_allow_private_networks: bool = field(
        default_factory=lambda: _as_bool(os.getenv("SCREENSHOT_ALLOW_PRIVATE_NETWORKS"))
    )

    @property
    def auth_token_ttl_seconds(self) -> int:
        return self.auth_token_ttl_days * 24 * 60 * 60

    @property
    def credential_key(self) -> str:
        if self.credential_encryption_key:
            return self.credential_encryption_key
        digest = hashlib.sha256(self.auth_secret_key.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest).decode("ascii")

    @property
    def cors_allow_all(self) -> bool:
        return any(origin in {"*", "0.0.0.0"} for origin in self.cors_origins)

    def validate_production_security(self) -> None:
        if self.app_env != "production":
            return
        if len(self.auth_secret_key) < 32 or self.auth_secret_key == "change-this-secret-key":
            raise RuntimeError("AUTH_SECRET_KEY must be a random value of at least 32 characters in production")
        if not self.credential_encryption_key:
            raise RuntimeError("CREDENTIAL_ENCRYPTION_KEY must be set in production")
        if self.credential_encryption_key == "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=":
            raise RuntimeError("Replace the default CREDENTIAL_ENCRYPTION_KEY before production startup")
        if not self.transport_private_key_b64:
            raise RuntimeError("TRANSPORT_PRIVATE_KEY_B64 must be set in production")
        if not self.admin_username.strip() or not self.admin_password:
            raise RuntimeError("ADMIN_USERNAME and ADMIN_PASSWORD must be set in production")
        try:
            decoded_key = base64.urlsafe_b64decode(self.credential_encryption_key.encode("ascii"))
        except (ValueError, UnicodeEncodeError):
            raise RuntimeError("CREDENTIAL_ENCRYPTION_KEY must be a valid Fernet key") from None
        if len(decoded_key) != 32:
            raise RuntimeError("CREDENTIAL_ENCRYPTION_KEY must be a valid Fernet key")
        if not self.admin_password_hash and self.admin_password in {"admin@123", "change-this-before-start"}:
            raise RuntimeError("Set ADMIN_PASSWORD_HASH or change ADMIN_PASSWORD before production startup")
