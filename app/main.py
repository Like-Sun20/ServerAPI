from __future__ import annotations

import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.routers import legacy_admin, live_compat, users, v1_admin

app = FastAPI(
    title="Live Debate Mock API",
    description="与 Live/admin、live-gateway 联调的 FastAPI Mock 服务",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 注意：更具体的前缀先注册，避免与 /api 下子路径冲突
app.include_router(legacy_admin.router, prefix="/api/admin", tags=["legacy-admin"])
app.include_router(v1_admin.router, prefix="/api/v1/admin", tags=["v1-admin"])
app.include_router(live_compat.router_admin, prefix="/api", tags=["live-admin"])
app.include_router(live_compat.router_v1_admin, prefix="/api/v1", tags=["live-compat-v1"])
app.include_router(users.router, prefix="/api", tags=["users"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Mock API (FastAPI). See /docs"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """与 live-gateway 相同路径，供 admin 页 WebSocket 联调（无业务推送，仅保持连接）。"""
    await websocket.accept()
    await websocket.send_text(
        json.dumps(
            {"type": "connected", "message": "已连接到 Mock 实时服务", "data": {}},
            ensure_ascii=False,
        )
    )
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if msg.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        return
