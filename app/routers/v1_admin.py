"""Live/admin-api.js 使用的 /api/v1/admin/* 接口（apiRequest 会解包 success.data）。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.core.deps import require_optional_v1_auth
from app.core.responses import ok
from app.mock import store

router = APIRouter(dependencies=[Depends(require_optional_v1_auth)])


def _enrich_stream(s: dict[str, Any]) -> dict[str, Any]:
    sid = s["id"]
    live = store.get_live(sid)
    return {
        **s,
        "playUrls": {"hls": s.get("url"), "flv": None, "rtmp": None},
        "liveStatus": {
            "isLive": bool(live.get("isLive")),
            "liveId": live.get("liveId"),
            "startTime": live.get("startTime"),
            "stopTime": live.get("stopTime"),
            "streamUrl": live.get("streamUrl") or s.get("url"),
        },
    }


@router.get("/dashboard")
def dashboard(
    stream_id: str = Query(..., alias="stream_id"),
) -> dict[str, Any]:
    payload = store.dashboard_payload(stream_id)
    if payload.get("error"):
        return ok(payload, message=payload.get("error", "fail"))
    return ok(payload, include_timestamp=True)


@router.post("/live/start")
def live_start(body: dict[str, Any]) -> dict[str, Any]:
    sid = body.get("streamId") or body.get("stream_id")
    if not sid:
        st_list = store.get_streams()
        sid = next((s["id"] for s in st_list if s.get("enabled")), None)
        if not sid and st_list:
            sid = st_list[0]["id"]
    if not sid:
        return ok({"success": False, "message": "没有可用直播流"}, message="没有可用直播流")

    st = next((x for x in store.get_streams() if x["id"] == sid), None)
    if not st:
        return ok({"success": False, "message": "流不存在"}, message="流不存在")

    live_id = str(uuid.uuid4())
    start = store.now_iso()
    store.set_live(
        sid,
        {
            "isLive": True,
            "liveId": live_id,
            "startTime": start,
            "streamUrl": st["url"],
        },
    )
    if body.get("autoStartAI"):
        store.set_ai_status(sid, "running")

    return ok(
        {
            "liveId": live_id,
            "streamUrl": st["url"],
            "status": "started",
            "startTime": start,
            "notifiedUsers": 0,
        },
        include_timestamp=True,
    )


@router.post("/live/stop")
def live_stop(body: dict[str, Any]) -> dict[str, Any]:
    sid = body.get("streamId") or body.get("stream_id")
    streams = store.get_streams()
    if not sid and streams:
        sid = streams[0]["id"]
    if sid:
        store.set_live(
            sid,
            {
                "isLive": False,
                "liveId": None,
                "startTime": None,
                "streamUrl": next((s["url"] for s in streams if s["id"] == sid), None),
            },
        )
    stop_time = store.now_iso()
    return ok(
        {
            "liveId": None,
            "status": "stopped",
            "stopTime": stop_time,
            "duration": 0,
            "summary": {},
            "notifiedUsers": 0,
        },
        include_timestamp=True,
    )


@router.post("/live/update-votes")
def live_update_votes(body: dict[str, Any]) -> dict[str, Any]:
    action = body.get("action")
    sid = body.get("streamId") or body.get("stream_id") or "stream-default-001"
    v = store.get_votes(sid)
    before = dict(v)
    if action == "set":
        store.set_votes(sid, int(body.get("leftVotes", 0)), int(body.get("rightVotes", 0)))
    elif action == "add":
        store.add_votes(sid, int(body.get("leftVotes", 0)), int(body.get("rightVotes", 0)))
    elif action == "reset":
        store.set_votes(sid, 0, 0)
    v2 = store.get_votes(sid)
    t = v2["leftVotes"] + v2["rightVotes"]
    after = {
        **v2,
        "leftPercentage": round(100 * v2["leftVotes"] / t) if t else 50,
        "rightPercentage": round(100 * v2["rightVotes"] / t) if t else 50,
    }
    return ok({"beforeUpdate": before, "afterUpdate": after, "updateTime": store.now_iso()}, include_timestamp=True)


@router.post("/live/reset-votes")
def live_reset_votes(body: dict[str, Any]) -> dict[str, Any]:
    sid = body.get("streamId") or body.get("stream_id") or "stream-default-001"
    rt = body.get("resetTo") or {}
    if rt:
        store.set_votes(sid, int(rt.get("leftVotes", 0)), int(rt.get("rightVotes", 0)))
    else:
        store.set_votes(sid, 0, 0)
    v = store.get_votes(sid)
    return ok({"backup": None, "currentVotes": v}, include_timestamp=True)


@router.post("/ai/start")
def ai_start(body: dict[str, Any]) -> dict[str, Any]:
    sid = body.get("streamId") or body.get("stream_id") or "stream-default-001"
    store.set_ai_status(sid, "running")
    session_id = str(uuid.uuid4())
    return ok(
        {
            "aiSessionId": session_id,
            "status": "running",
            "startTime": store.now_iso(),
            "settings": body.get("settings") or {},
        },
        include_timestamp=True,
    )


@router.post("/ai/stop")
def ai_stop(body: dict[str, Any]) -> dict[str, Any]:
    sid = body.get("streamId") or body.get("stream_id") or "stream-default-001"
    store.set_ai_status(sid, "stopped")
    return ok(
        {
            "aiSessionId": None,
            "status": "stopped",
            "stopTime": store.now_iso(),
            "duration": 0,
            "summary": {},
        },
        include_timestamp=True,
    )


@router.post("/ai/toggle")
def ai_toggle(body: dict[str, Any]) -> dict[str, Any]:
    action = body.get("action")
    sid = body.get("streamId") or body.get("stream_id") or "stream-default-001"
    cur = store.get_ai_status(sid)
    if action == "pause" and cur == "running":
        store.set_ai_status(sid, "paused")
    elif action == "resume" and cur == "paused":
        store.set_ai_status(sid, "running")
    return ok(
        {
            "aiSessionId": str(uuid.uuid4()),
            "status": store.get_ai_status(sid),
            "actionTime": store.now_iso(),
        },
        include_timestamp=True,
    )


@router.get("/streams")
def list_streams_v1() -> dict[str, Any]:
    raw = [_enrich_stream(dict(s)) for s in store.get_streams()]
    return ok({"streams": raw, "total": len(raw)}, include_timestamp=True)


@router.post("/streams")
def create_stream_v1(body: dict[str, Any]) -> dict[str, Any]:
    row = store.add_stream(body)
    return ok(row, include_timestamp=True)


@router.get("/live/viewers")
def live_viewers(stream_id: str | None = Query(None, alias="stream_id")) -> dict[str, Any]:
    if stream_id:
        n = store.bump_viewers(stream_id)
        return ok({"streamId": stream_id, "viewers": n, "timestamp": store.now_iso()})
    m = store.get_all_viewers_map()
    total = sum(m.values())
    return ok({"streams": m, "totalConnections": total, "timestamp": store.now_iso()})


@router.post("/live/broadcast-viewers")
def broadcast_viewers(body: dict[str, Any]) -> dict[str, Any]:
    sid = body.get("streamId") or body.get("stream_id")
    if not sid:
        return ok({"message": "缺少 streamId"})
    n = store.bump_viewers(sid)
    return ok({"streamId": sid, "viewers": n, "message": "ok"})


@router.get("/ai-content/list")
def ai_content_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    _start_time: str | None = Query(None, alias="startTime"),
    _end_time: str | None = Query(None, alias="endTime"),
    _stream_id: str | None = Query(None, alias="stream_id"),
) -> dict[str, Any]:
    del _start_time, _end_time, _stream_id  # Mock 不按流与时间过滤
    items_all = store.ai_content_list()
    # 简化过滤
    filtered = items_all
    total = len(filtered)
    start = (page - 1) * page_size
    page_items = filtered[start : start + page_size]
    out = []
    for item in page_items:
        ts = item.get("timestamp")
        ts_iso = (
            datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat()
            if isinstance(ts, (int, float))
            else store.now_iso()
        )
        out.append(
            {
                "id": item["id"],
                "content": item.get("content") or item.get("text") or "",
                "type": "summary",
                "timestamp": ts_iso,
                "position": item.get("side") or "left",
                "confidence": 0.95,
                "statistics": item.get("statistics") or {"views": 0, "likes": 0, "comments": len(item.get("comments") or [])},
            }
        )
    return ok({"total": total, "page": page, "items": out})


@router.get("/ai-content/{content_id}/comments")
def ai_content_comments(
    content_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
) -> dict[str, Any]:
    for item in store.ai_content_list():
        if item["id"] != content_id:
            continue
        comments = item.get("comments") or []
        total = len(comments)
        start = (page - 1) * page_size
        chunk = comments[start : start + page_size]
        formatted = []
        for c in chunk:
            formatted.append(
                {
                    "commentId": c.get("commentId") or c.get("id"),
                    "userId": c.get("userId") or "anonymous",
                    "nickname": c.get("nickname") or c.get("user") or "匿名",
                    "avatar": c.get("avatar") or "",
                    "content": c.get("content") or c.get("text") or "",
                    "likes": c.get("likes") or 0,
                    "timestamp": c.get("timestamp") or store.now_iso(),
                }
            )
        return ok(
            {
                "contentId": content_id,
                "contentText": item.get("content") or item.get("text") or "",
                "total": total,
                "page": page,
                "pageSize": page_size,
                "comments": formatted,
            }
        )
    return ok(
        {
            "contentId": content_id,
            "contentText": "",
            "total": 0,
            "page": page,
            "pageSize": page_size,
            "comments": [],
        }
    )


@router.delete("/ai-content/{content_id}/comments/{comment_id}")
def delete_ai_comment(content_id: str, comment_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    del body
    ok_del = store.delete_ai_comment(content_id, comment_id)
    if not ok_del:
        return ok({"deleted": False, "contentId": content_id, "commentId": comment_id}, message="评论不存在")
    return ok({"commentId": comment_id, "contentId": content_id, "deleteTime": None}, message="评论已删除")


@router.get("/streams/{stream_id}/debate")
def get_stream_debate(stream_id: str) -> dict[str, Any]:
    d = store.get_debate_for_stream(stream_id)
    return ok(d)


@router.put("/streams/{stream_id}/debate")
def put_stream_debate(stream_id: str, body: dict[str, Any]) -> dict[str, Any]:
    did = body.get("debate_id") or body.get("debateId")
    if did:
        store.upsert_debate_stream(stream_id, did)
    return ok(store.get_debate_for_stream(stream_id))


@router.delete("/streams/{stream_id}/debate")
def del_stream_debate(stream_id: str) -> dict[str, Any]:
    store.delete_stream_debate(stream_id)
    return ok({}, message="已解除关联")


@router.get("/debates/{debate_id}")
def get_debate(debate_id: str) -> dict[str, Any]:
    d = store.get_debate(debate_id)
    return ok(d)


@router.put("/debates/{debate_id}")
def put_debate(debate_id: str, body: dict[str, Any]) -> dict[str, Any]:
    d = store.update_debate(debate_id, body)
    return ok(d)


@router.post("/debates")
def post_debate(body: dict[str, Any]) -> dict[str, Any]:
    d = store.create_debate(body)
    return ok(d)
