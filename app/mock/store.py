"""
内存 Mock 状态：直播流、辩题、票数、AI、观看人数等。
线程安全：简单 threading.Lock。
"""

from __future__ import annotations

import random
import threading
import uuid
from datetime import UTC, datetime
from typing import Any

_lock = threading.Lock()

_streams: list[dict[str, Any]] = []
_debates: dict[str, dict[str, Any]] = {}
# stream_id -> debate_id
_stream_debate: dict[str, str] = {}
# stream_id -> { leftVotes, rightVotes }
_votes: dict[str, dict[str, int]] = {}
# stream_id -> { isLive, liveId, startTime, streamUrl, ... }
_live: dict[str, dict[str, Any]] = {}
# stream_id -> ai status
_ai: dict[str, str] = {}
# stream_id -> viewer count
_viewers: dict[str, int] = {}
# AI 内容
_ai_content: list[dict[str, Any]] = []
# stream_id -> debate flow segments
_debate_flow: dict[str, list[dict[str, Any]]] = {}
# 直播计划（全局简化）
_schedule: dict[str, Any] = {
    "isScheduled": False,
    "scheduledStartTime": None,
    "scheduledEndTime": None,
    "streamId": None,
}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def now_iso() -> str:
    """供路由使用的公开时间戳。"""
    return _now_iso()


def _seed() -> None:
    global _streams, _debates, _stream_debate, _votes, _live, _ai, _viewers, _ai_content
    if _streams:
        return

    sid1 = "stream-default-001"
    sid2 = "stream-test-002"
    _streams = [
        {
            "id": sid1,
            "name": "主赛场 HLS",
            "url": "https://example.com/live/main/index.m3u8",
            "type": "hls",
            "description": "默认直播流",
            "enabled": True,
            "createdAt": _now_iso(),
            "updatedAt": _now_iso(),
        },
        {
            "id": sid2,
            "name": "测试 RTMP",
            "url": "rtmp://127.0.0.1/live/test",
            "type": "rtmp",
            "description": "测试流",
            "enabled": False,
            "createdAt": _now_iso(),
            "updatedAt": _now_iso(),
        },
    ]

    d1 = "debate-default-001"
    _debates[d1] = {
        "id": d1,
        "title": "如果有一个能一键消除痛苦的按钮，你会按吗？",
        "description": "辩题说明 Mock",
        "leftPosition": "正方：不按",
        "rightPosition": "反方：会按",
        "isActive": True,
    }
    _stream_debate[sid1] = d1

    for sid in (sid1, sid2):
        _votes[sid] = {"leftVotes": 120, "rightVotes": 98}
        _live[sid] = {
            "isLive": False,
            "liveId": None,
            "startTime": None,
            "streamUrl": next(s["url"] for s in _streams if s["id"] == sid),
        }
        _ai[sid] = "stopped"
        _viewers[sid] = random.randint(50, 500)

    _debate_flow[sid1] = [
        {"name": "正方发言", "duration": 180, "side": "left"},
        {"name": "反方发言", "duration": 180, "side": "right"},
        {"name": "自由辩论", "duration": 300, "side": "both"},
    ]

    # AI 内容示例
    _ai_content = [
        {
            "id": str(uuid.uuid4()),
            "content": "正方：痛苦是成长的必要经历。",
            "text": "正方：痛苦是成长的必要经历。",
            "side": "left",
            "timestamp": int(datetime.now(UTC).timestamp() * 1000) - 120000,
            "comments": [
                {
                    "commentId": "c1",
                    "id": "c1",
                    "nickname": "观众A",
                    "user": "观众A",
                    "content": "有道理",
                    "text": "有道理",
                    "likes": 3,
                    "timestamp": _now_iso(),
                }
            ],
            "likes": 12,
            "statistics": {"views": 100, "likes": 12, "comments": 1},
        },
        {
            "id": str(uuid.uuid4()),
            "content": "反方：消除痛苦不等于逃避责任。",
            "text": "反方：消除痛苦不等于逃避责任。",
            "side": "right",
            "timestamp": int(datetime.now(UTC).timestamp() * 1000) - 60000,
            "comments": [],
            "likes": 8,
            "statistics": {"views": 80, "likes": 8, "comments": 0},
        },
    ]


def get_streams() -> list[dict[str, Any]]:
    _seed()
    with _lock:
        return [dict(s) for s in _streams]


def get_stream(sid: str) -> dict[str, Any] | None:
    _seed()
    with _lock:
        for s in _streams:
            if s["id"] == sid:
                return dict(s)
        return None


def add_stream(body: dict[str, Any]) -> dict[str, Any]:
    _seed()
    with _lock:
        nid = f"stream-{int(datetime.now(UTC).timestamp())}-{uuid.uuid4().hex[:6]}"
        row = {
            "id": nid,
            "name": body["name"].strip(),
            "url": body["url"].strip(),
            "type": body["type"],
            "description": (body.get("description") or "").strip(),
            "enabled": body.get("enabled", True),
            "createdAt": _now_iso(),
            "updatedAt": _now_iso(),
        }
        _streams.append(row)
        _votes[nid] = {"leftVotes": 0, "rightVotes": 0}
        _live[nid] = {
            "isLive": False,
            "liveId": None,
            "startTime": None,
            "streamUrl": row["url"],
        }
        _ai[nid] = "stopped"
        _viewers[nid] = random.randint(10, 100)
        return dict(row)


def update_stream(sid: str, body: dict[str, Any]) -> dict[str, Any] | None:
    _seed()
    with _lock:
        for s in _streams:
            if s["id"] == sid:
                if "name" in body and body["name"] is not None:
                    s["name"] = str(body["name"]).strip()
                if "url" in body and body["url"] is not None:
                    s["url"] = str(body["url"]).strip()
                if "type" in body and body["type"] is not None:
                    s["type"] = body["type"]
                if "description" in body and body["description"] is not None:
                    s["description"] = str(body["description"]).strip()
                if "enabled" in body and body["enabled"] is not None:
                    s["enabled"] = bool(body["enabled"])
                s["updatedAt"] = _now_iso()
                return dict(s)
        return None


def delete_stream(sid: str) -> bool:
    _seed()
    with _lock:
        global _streams
        new_list = [s for s in _streams if s["id"] != sid]
        if len(new_list) == len(_streams):
            return False
        _streams = new_list
        _votes.pop(sid, None)
        _live.pop(sid, None)
        _ai.pop(sid, None)
        _viewers.pop(sid, None)
        _stream_debate.pop(sid, None)
        return True


def toggle_stream(sid: str) -> dict[str, Any] | None:
    _seed()
    with _lock:
        for s in _streams:
            if s["id"] == sid:
                s["enabled"] = not s.get("enabled", True)
                s["updatedAt"] = _now_iso()
                return dict(s)
        return None


def get_debate_for_stream(sid: str) -> dict[str, Any] | None:
    _seed()
    with _lock:
        did = _stream_debate.get(sid)
        if not did:
            return None
        return dict(_debates[did]) if did in _debates else None


def get_debate(did: str) -> dict[str, Any] | None:
    _seed()
    with _lock:
        return dict(_debates[did]) if did in _debates else None


def upsert_debate_stream(sid: str, debate_id: str | None) -> None:
    _seed()
    with _lock:
        if debate_id:
            _stream_debate[sid] = debate_id
        else:
            _stream_debate.pop(sid, None)


def update_debate(did: str, body: dict[str, Any]) -> dict[str, Any] | None:
    _seed()
    with _lock:
        if did not in _debates:
            return None
        d = _debates[did]
        for k in ("title", "description", "leftPosition", "rightPosition", "isActive"):
            if k in body and body[k] is not None:
                d[k] = body[k]
        return dict(d)


def create_debate(body: dict[str, Any]) -> dict[str, Any]:
    _seed()
    with _lock:
        nid = f"debate-{uuid.uuid4().hex[:12]}"
        row = {
            "id": nid,
            "title": body["title"],
            "description": body.get("description", ""),
            "leftPosition": body.get("leftPosition", ""),
            "rightPosition": body.get("rightPosition", ""),
            "isActive": body.get("isActive", True),
        }
        _debates[nid] = row
        return dict(row)


def delete_stream_debate(sid: str) -> bool:
    _seed()
    with _lock:
        if sid in _stream_debate:
            del _stream_debate[sid]
            return True
        return False


def get_votes(sid: str) -> dict[str, int]:
    _seed()
    with _lock:
        return dict(_votes.get(sid, {"leftVotes": 0, "rightVotes": 0}))


def set_votes(sid: str, left: int, right: int) -> None:
    _seed()
    with _lock:
        _votes[sid] = {"leftVotes": left, "rightVotes": right}


def add_votes(sid: str, left: int, right: int) -> None:
    _seed()
    with _lock:
        cur = _votes.setdefault(sid, {"leftVotes": 0, "rightVotes": 0})
        cur["leftVotes"] += left
        cur["rightVotes"] += right


def get_live(sid: str) -> dict[str, Any]:
    _seed()
    with _lock:
        return dict(_live.setdefault(sid, {"isLive": False, "liveId": None, "startTime": None}))


def set_live(sid: str, live: dict[str, Any]) -> None:
    _seed()
    with _lock:
        _live[sid] = {**_live.get(sid, {}), **live}


def get_ai_status(sid: str) -> str:
    _seed()
    with _lock:
        return _ai.setdefault(sid, "stopped")


def set_ai_status(sid: str, status: str) -> None:
    _seed()
    with _lock:
        _ai[sid] = status


def get_viewers(sid: str | None) -> int:
    _seed()
    with _lock:
        if sid:
            return _viewers.setdefault(sid, random.randint(30, 200))
        return sum(_viewers.values())


def bump_viewers(sid: str) -> int:
    _seed()
    with _lock:
        n = _viewers.get(sid, 100) + random.randint(1, 20)
        _viewers[sid] = n
        return n


def get_all_viewers_map() -> dict[str, int]:
    _seed()
    with _lock:
        return dict(_viewers)


def dashboard_payload(stream_id: str, total_users: int = 128) -> dict[str, Any]:
    """与 admin.js 使用的字段对齐。"""
    _seed()
    with _lock:
        st = next((dict(s) for s in _streams if s["id"] == stream_id), None)
        if not st:
            return {"error": "stream not found", "streamId": stream_id}
        did = _stream_debate.get(stream_id)
        debate = _debates.get(did, {}) if did else {}
        v = _votes.get(stream_id, {"leftVotes": 0, "rightVotes": 0})
        lv, rv = v["leftVotes"], v["rightVotes"]
        total_v = lv + rv
        lp = round(100 * lv / total_v) if total_v else 50
        rp = 100 - lp if total_v else 50
        live_info = _live.get(stream_id, {})
        is_live = bool(live_info.get("isLive"))
        ai_st = _ai.get(stream_id, "stopped")
        viewers = _viewers.get(stream_id, 100)

        live_duration = 0
        if is_live and live_info.get("startTime"):
            try:
                st_t = datetime.fromisoformat(live_info["startTime"].replace("Z", "+00:00"))
                live_duration = int((datetime.now(UTC) - st_t).total_seconds())
            except Exception:
                live_duration = 0

        return {
            "totalUsers": total_users,
            "activeUsers": viewers,
            "isLive": is_live,
            "liveStreamUrl": live_info.get("streamUrl") or st.get("url"),
            "streamId": stream_id,
            "activeStreamUrl": st["url"] if st.get("enabled") else None,
            "activeStreamId": stream_id if st.get("enabled") else None,
            "activeStreamName": st.get("name"),
            "totalVotes": total_v,
            "leftVotes": lv,
            "rightVotes": rv,
            "leftPercentage": lp,
            "rightPercentage": rp,
            "totalComments": 42,
            "totalLikes": 120,
            "aiStatus": ai_st,
            "debateTopic": {
                "title": debate.get("title", "辩题"),
                "leftSide": debate.get("leftPosition", "正方"),
                "rightSide": debate.get("rightPosition", "反方"),
                "description": debate.get("description", ""),
            },
            "liveStartTime": live_info.get("startTime"),
            "liveDuration": max(0, live_duration),
            "liveId": live_info.get("liveId"),
        }


def ai_content_list() -> list[dict[str, Any]]:
    _seed()
    with _lock:
        return [dict(x) for x in _ai_content]


def delete_ai_comment(content_id: str, comment_id: str) -> bool:
    _seed()
    with _lock:
        for item in _ai_content:
            if item["id"] != content_id:
                continue
            comments = item.get("comments") or []
            new_c = [c for c in comments if (c.get("commentId") or c.get("id")) != comment_id]
            if len(new_c) == len(comments):
                return False
            item["comments"] = new_c
            if item.get("statistics"):
                item["statistics"]["comments"] = len(new_c)
            return True
        return False


def get_debate_flow(sid: str) -> list[dict[str, Any]]:
    _seed()
    with _lock:
        return [dict(s) for s in _debate_flow.get(sid, [])]


def save_debate_flow(sid: str, segments: list[dict[str, Any]]) -> None:
    _seed()
    with _lock:
        _debate_flow[sid] = [dict(s) for s in segments]


def get_schedule() -> dict[str, Any]:
    _seed()
    with _lock:
        return dict(_schedule)


def set_schedule(data: dict[str, Any]) -> dict[str, Any]:
    _seed()
    global _schedule
    with _lock:
        _schedule = {**_schedule, **data}
        return dict(_schedule)


def clear_schedule() -> None:
    _seed()
    global _schedule
    with _lock:
        _schedule = {
            "isScheduled": False,
            "scheduledStartTime": None,
            "scheduledEndTime": None,
            "streamId": None,
        }


PRIMARY_DEBATE_ID = "debate-default-001"


def get_primary_debate() -> dict[str, Any]:
    """admin.js GET /api/admin/debate 使用的全局辩题。"""
    _seed()
    with _lock:
        return dict(_debates[PRIMARY_DEBATE_ID])


def update_primary_debate(payload: dict[str, Any]) -> dict[str, Any]:
    _seed()
    with _lock:
        d = _debates[PRIMARY_DEBATE_ID]
        for k in ("title", "description", "leftPosition", "rightPosition"):
            if k in payload and payload[k] is not None:
                d[k] = payload[k]
        return dict(d)


def delete_ai_content_item(content_id: str) -> bool:
    global _ai_content
    _seed()
    with _lock:
        before = len(_ai_content)
        _ai_content = [x for x in _ai_content if x["id"] != content_id]
        return len(_ai_content) < before
