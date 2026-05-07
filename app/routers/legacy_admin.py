"""
admin.js 中直接使用 fetch(API_BASE/...) 的接口（非 apiRequest），部分返回原始数组/对象，
部分要求顶层 success。
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Query

from app.core.responses import ok
from app.mock import store

router = APIRouter()


def _enrich_row(s: dict[str, Any]) -> dict[str, Any]:
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


@router.get("/streams")
def legacy_list_streams() -> list[dict[str, Any]]:
    """admin.js：期望响应体为直播流数组。"""
    return [_enrich_row(dict(x)) for x in store.get_streams()]


@router.post("/streams")
def legacy_create_stream(body: dict[str, Any]) -> dict[str, Any]:
    """返回新建流对象（含 id），供 refreshSetupStreams 使用。"""
    return store.add_stream(body)


@router.put("/streams/{stream_id}")
def legacy_put_stream(stream_id: str, body: dict[str, Any]) -> dict[str, Any]:
    row = store.update_stream(stream_id, body)
    if not row:
        return {"success": False, "message": "流不存在"}
    return row


@router.delete("/streams/{stream_id}")
def legacy_delete_stream(stream_id: str) -> dict[str, Any]:
    ok = store.delete_stream(stream_id)
    return {"success": ok, "message": "删除成功" if ok else "不存在"}


@router.post("/streams/{stream_id}/toggle")
def legacy_toggle(stream_id: str) -> dict[str, Any]:
    row = store.toggle_stream(stream_id)
    if not row:
        return {"success": False, "message": "流不存在"}
    return {"success": True, **row}


@router.get("/debate")
def legacy_get_debate() -> dict[str, Any]:
    return store.get_primary_debate()


@router.put("/debate")
def legacy_put_debate(body: dict[str, Any]) -> dict[str, Any]:
    return store.update_primary_debate(body)


@router.get("/live/schedule")
def legacy_get_schedule() -> dict[str, Any]:
    sc = store.get_schedule()
    return {
        "success": True,
        "data": {
            **sc,
            "isScheduled": bool(sc.get("isScheduled")),
        },
    }


@router.post("/live/schedule")
def legacy_post_schedule(body: dict[str, Any]) -> dict[str, Any]:
    data = {
        "isScheduled": True,
        "scheduledStartTime": body.get("scheduledStartTime"),
        "scheduledEndTime": body.get("scheduledEndTime"),
        "streamId": body.get("streamId"),
    }
    store.set_schedule(data)
    return {"success": True, "message": "直播计划已设置", "data": store.get_schedule()}


@router.post("/live/schedule/cancel")
def legacy_cancel_schedule() -> dict[str, Any]:
    store.clear_schedule()
    return {"success": True, "message": "直播计划已取消", "data": store.get_schedule()}


@router.post("/live/setup-and-start")
def legacy_setup_and_start(body: dict[str, Any]) -> dict[str, Any]:
    """
    一键设置并开始：立即开播或仅保存计划。
    """
    stream_id = body.get("streamId")
    start_now = body.get("startNow", False)
    if not stream_id:
        return {"success": False, "error": "缺少 streamId", "message": "缺少 streamId"}

    st = next((x for x in store.get_streams() if x["id"] == stream_id), None)
    if not st:
        return {"success": False, "error": "流不存在", "message": "流不存在"}

    if start_now:
        live_id = str(uuid.uuid4())
        start = store.now_iso()
        store.set_live(
            stream_id,
            {
                "isLive": True,
                "liveId": live_id,
                "startTime": start,
                "streamUrl": st["url"],
            },
        )
        store.clear_schedule()
        return {
            "success": True,
            "message": "直播已开始",
            "data": {
                "isLive": True,
                "streamUrl": st["url"],
                "streamId": stream_id,
                "liveId": live_id,
            },
        }

    sched_start = body.get("scheduledStartTime")
    if not sched_start:
        return {"success": False, "error": "请设置开始时间", "message": "请设置开始时间"}

    store.set_schedule(
        {
            "isScheduled": True,
            "scheduledStartTime": sched_start,
            "scheduledEndTime": body.get("scheduledEndTime"),
            "streamId": stream_id,
        }
    )
    return {
        "success": True,
        "message": "直播计划已设置",
        "data": store.get_schedule(),
    }


@router.get("/debate-flow")
def get_debate_flow_cfg(stream_id: str | None = Query(None, alias="stream_id")) -> dict[str, Any]:
    sid = stream_id or "stream-default-001"
    segs = store.get_debate_flow(sid)
    return ok(data={"segments": segs, "stream_id": sid})


@router.post("/debate-flow")
def save_debate_flow_cfg(body: dict[str, Any]) -> dict[str, Any]:
    sid = body.get("stream_id") or body.get("streamId") or "stream-default-001"
    segments = body.get("segments") or []
    store.save_debate_flow(sid, segments)
    return ok(data={"segments": segments, "stream_id": sid}, message="saved")


@router.post("/debate-flow/control")
def debate_flow_control(body: dict[str, Any]) -> dict[str, Any]:
    action = body.get("action")
    sid = body.get("stream_id") or body.get("streamId")
    return ok(data={"action": action, "stream_id": sid}, message="mock ok")


@router.get("/votes/statistics")
def legacy_votes_statistics(timeRange: str = Query("1h")) -> dict[str, Any]:  # noqa: N803
    """apiRequest：GET /api/admin/votes/statistics"""
    del timeRange
    s1 = "stream-default-001"
    v = store.get_votes(s1)
    lv, rv = v["leftVotes"], v["rightVotes"]
    tot = lv + rv
    lp = round(100 * lv / tot) if tot else 50
    rp = 100 - lp if tot else 50
    return ok(
        data={
            "summary": {
                "totalVotes": tot,
                "leftVotes": lv,
                "rightVotes": rv,
                "leftPercentage": lp,
                "rightPercentage": rp,
                "growthRate": 5.2,
            },
            "timeline": [],
            "topVoters": [],
        },
        include_timestamp=True,
    )


@router.delete("/ai/content/{content_id}")
def delete_ai_content_legacy(content_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    del body
    if store.delete_ai_content_item(content_id):
        return {"success": True, "message": "已删除", "data": {"contentId": content_id}}
    return {"success": False, "message": "内容不存在"}
