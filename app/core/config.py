import os

# 若设置则要求 /api/v1/* 请求携带 Authorization: Bearer <token>
MOCK_ADMIN_TOKEN: str | None = os.getenv("MOCK_ADMIN_TOKEN") or None
