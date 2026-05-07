"""统一 JSON：`success` + `code`(0 成功) + `message` + `data`，兼容 Live/admin `apiRequest` 解包逻辑。"""

from __future__ import annotations

import time
from typing import Any


def ok(data: Any = None, message: str = "success", *, include_timestamp: bool = False) -> dict[str, Any]:
    body: dict[str, Any] = {
        "success": True,
        "code": 0,
        "message": message,
        "data": data if data is not None else {},
    }
    if include_timestamp:
        body["timestamp"] = int(time.time() * 1000)
    return body


def fail(
    code: int,
    message: str,
    data: Any = None,
    *,
    http_compatible: bool = True,
) -> dict[str, Any]:
    del http_compatible  # 占位：便于日后区分业务码与 HTTP 状态
    return {
        "success": False,
        "code": code,
        "message": message,
        "data": data if data is not None else {},
    }
