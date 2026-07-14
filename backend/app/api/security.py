from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(prefix="/security", tags=["security"])


@router.get("/transport-key")
def transport_key(request: Request):
    return {
        "algorithm": "RSA-OAEP-SHA256",
        "public_key": request.app.state.transport_crypto.public_key_b64,
    }
