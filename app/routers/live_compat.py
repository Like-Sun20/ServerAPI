"""
与 Live/admin 兼容：
- GET /api/admin/miniprogram/users
- GET /api/v1/admin/users（评委选择；不走 apiRequest 时可保留原样）
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.core.responses import ok
from app.schemas.user import User
from app.services import mock_service

router_admin = APIRouter()
router_v1_admin = APIRouter()


def _user_to_miniprogram(u: User) -> dict[str, Any]:
    join_iso = u.created_at.isoformat()
    online = u.status == "active"
    return {
        "userId": str(u.id),
        "nickname": u.username,
        "avatar": None,
        "avatarUrl": None,
        "joinTime": join_iso,
        "status": "online" if online else "offline",
    }


def _user_to_v1_judge(u: User) -> dict[str, str]:
    return {
        "id": str(u.id),
        "nickname": u.username,
        "name": u.username,
        "avatarUrl": "",
    }


@router_admin.get("/admin/miniprogram/users")
def miniprogram_user_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    _status: str = Query("all", alias="status"),
    _order_by: str = Query("joinTime", alias="orderBy"),
) -> dict[str, Any]:
    del _status, _order_by
    result = mock_service.list_users(page=page, page_size=page_size)
    users = [_user_to_miniprogram(u) for u in result.items]
    return ok(
        data={
            "total": result.total,
            "page": result.page,
            "pageSize": result.page_size,
            "users": users,
        },
        include_timestamp=True,
    )


@router_v1_admin.get("/admin/users")
def v1_admin_users_list() -> dict[str, Any]:
    result = mock_service.list_users(page=1, page_size=10_000)
    rows = [_user_to_v1_judge(u) for u in result.items]
    body = ok(data={"users": rows}, include_timestamp=True)
    body["users"] = rows
    return body
