from fastapi import Header, HTTPException, status

from app.core import config


async def require_optional_v1_auth(authorization: str | None = Header(None)) -> None:
    """未配置 MOCK_ADMIN_TOKEN 时不校验；配置了则必须携带正确 Bearer。"""
    token = config.MOCK_ADMIN_TOKEN
    if not token:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 Authorization: Bearer <token>",
        )
    if authorization[7:].strip() != token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="token 无效",
        )
