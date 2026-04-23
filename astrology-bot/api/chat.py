"""
聊天模块 — 核心决策咨询对话
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json

from api.auth import get_current_user
from models.database import get_user, save_message, get_recent_messages
from services.ai import chat_with_ai
from services.astrology import get_today_transits, format_chart_for_prompt, format_transits_for_prompt

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    has_chart: bool


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, openid: str = Depends(get_current_user)):
    """
    核心聊天接口
    用户发送消息 → 结合星盘+星象 → AI生成个性化回复
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    # 1. 获取用户星盘
    user = get_user(openid)
    chart_data = None

    if user and user.get("chart_data"):
        chart_data = json.loads(user["chart_data"])
        chart_text = format_chart_for_prompt(chart_data)
        print(f"[CHAT] 用户 {openid} 有星盘，包含字段: {list(chart_data.keys())}")
    else:
        # 没有星盘，直接返回提醒，不调用AI
        print(f"[CHAT] 用户 {openid} 没有星盘数据，提醒设置")
        save_message(openid, "user", req.message, message_type="decision")
        nudge = "你还没有设置星盘呢～先去「星盘」页面填一下你的出生信息，我才能根据你的星座给你更准的分析呀 ✨"
        save_message(openid, "assistant", nudge, message_type="decision")
        return ChatResponse(reply=nudge, has_chart=False)

    # 2. 获取今日星象（实时计算）
    transits = get_today_transits()
    transits_text = format_transits_for_prompt(transits)
    print(f"[CHAT] 今日行运: {transits_text[:80]}...")

    # 3. 获取最近对话历史
    history = get_recent_messages(openid, limit=10)
    print(f"[CHAT] 历史消息数: {len(history)}")

    # 4. 用户资料（性别、职业等）
    user_info = {}
    if user:
        user_info = {
            "nickname": user.get("nickname", ""),
            "gender": user.get("gender", ""),
            "occupation": user.get("occupation", ""),
        }

    # 5. 调用AI
    try:
        reply = await chat_with_ai(
            user_message=req.message,
            user_chart=chart_text,
            today_transits=transits_text,
            chat_history=history,
            user_info=user_info,
        )
    except Exception as e:
        print(f"[CHAT ERROR] AI调用出错: {e}")
        reply = "星象信号有点不稳定，请稍后再试～"

    # 5. 保存聊天记录
    save_message(openid, "user", req.message, message_type="decision")
    save_message(openid, "assistant", reply, message_type="decision")

    return ChatResponse(reply=reply, has_chart=chart_data is not None)


@router.get("/chat/history")
async def get_history(limit: int = 20, openid: str = Depends(get_current_user)):
    """获取聊天历史"""
    messages = get_recent_messages(openid, limit=limit)
    return {"messages": messages}


@router.post("/chat/rebuild-knowledge")
async def rebuild_knowledge():
    """重建RAG知识库索引（更新知识后调用）"""
    try:
        from services.rag import rebuild_index
        count = rebuild_index()
        return {"success": True, "count": count}
    except Exception as e:
        return {"success": False, "error": str(e)}
