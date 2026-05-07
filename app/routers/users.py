from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Path, Query, status
from fastapi.responses import JSONResponse

from app.core.responses import fail, ok
from app.schemas.user import UserCreate, UserUpdate
from app.services import mock_service

router = APIRouter()


def _user_json(u: Any) -> dict[str, Any]:
    return u.model_dump(mode="json")


@router.get("/users")
def list_users(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
) -> dict[str, Any]:
    result = mock_service.list_users(page=page, page_size=page_size)
    return ok(
        data={
            "items": [_user_json(u) for u in result.items],
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
        },
    )


@router.get("/users/{user_id}", response_model=None)
def get_user(
    user_id: int = Path(..., description="用户 ID"),
) -> JSONResponse | dict[str, Any]:
    user = mock_service.get_user_by_id(user_id)
    if user is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=fail(404, "用户不存在"),
        )
    return ok(data=_user_json(user))


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate) -> dict[str, Any]:
    user = mock_service.create_user(body)
    return ok(data=_user_json(user))


@router.patch("/users/{user_id}", response_model=None)
def update_user(
    user_id: int = Path(..., description="用户 ID"),
    body: UserUpdate = ...,
) -> JSONResponse | dict[str, Any]:
    user = mock_service.update_user(user_id, body)
    if user is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=fail(404, "用户不存在"),
        )
    return ok(data=_user_json(user))


@router.delete("/users/{user_id}", response_model=None)
def delete_user(
    user_id: int = Path(..., description="用户 ID"),
) -> JSONResponse | dict[str, Any]:
    if not mock_service.delete_user(user_id):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=fail(404, "用户不存在"),
        )
    return ok(data={"deleted": True, "id": user_id})
