from __future__ import annotations

from fastapi import HTTPException, Request, status

from ..schemas import CredentialData, CredentialEnvelope

PLAINTEXT_DISABLED_DETAIL = (
    "服务端未开启明文凭据传输：HTTP 访问下浏览器不提供 WebCrypto，前端无法加密凭据。"
    "如需在纯 HTTP 环境使用，请在项目根 .env 中设置 ALLOW_PLAINTEXT_CREDENTIALS=true 并重启后端。"
)


def plaintext_credentials_allowed(request: Request) -> bool:
    return bool(request.app.state.settings.allow_plaintext_credentials)


def require_plaintext_credentials(request: Request) -> None:
    if not plaintext_credentials_allowed(request):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=PLAINTEXT_DISABLED_DETAIL)


def resolve_credentials(
    request: Request,
    envelope: CredentialEnvelope | None,
    plaintext: CredentialData | None,
    *,
    required: bool = False,
) -> CredentialData | None:
    """按优先级解出本次请求携带的凭据。

    优先使用加密信封（有 HTTPS 或 localhost 时前端总是走这条路）；只有在
    ALLOW_PLAINTEXT_CREDENTIALS=true 时才接受明文字段。两者都没有时：
    required=True 报错，否则返回 None 表示“本次不改动凭据”。
    """
    if envelope is not None:
        try:
            return CredentialData.model_validate(
                request.app.state.transport_crypto.decrypt_envelope(envelope.model_dump())
            )
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="凭据数据无效") from error
    if plaintext is None:
        if required:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="缺少凭据数据")
        return None
    require_plaintext_credentials(request)
    return plaintext
