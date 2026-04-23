"""
AI对话引擎 — DeepSeek API
"""
import os
import json
import httpx
from datetime import datetime
from typing import List, Optional
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "system_prompt.txt")


def _load_system_prompt():
    """每次动态读取 system prompt"""
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def build_system_prompt(user_chart: str, today_transits: str, user_info: dict = None) -> str:
    """构建完整的System Prompt，加入用户资料和当前时间"""
    template = _load_system_prompt()
    prompt = template.format(
        user_chart=user_chart,
        today_transits=today_transits,
    )

    # 根据用户资料调整称呼和语境
    if user_info:
        info_parts = []
        nickname = user_info.get("nickname", "")
        gender = user_info.get("gender", "")
        occupation = user_info.get("occupation", "")

        if nickname:
            info_parts.append(f"昵称：{nickname}")
        if gender:
            info_parts.append(f"性别：{gender}")
        if occupation:
            info_parts.append(f"职业：{occupation}")

        if info_parts:
            prompt += "\n\n用户资料：" + "，".join(info_parts)

        # 称呼指引
        if gender == "男":
            prompt += "\n称呼ta：兄弟/老铁/哥们，语气像男生之间聊天"
        elif gender == "女":
            prompt += "\n称呼ta：姐妹/宝/亲，语气像闺蜜聊天"
        else:
            prompt += '\n称呼ta用昵称或者"你"就好，语气轻松自然'

        if occupation:
            prompt += f"\nta是{occupation}，回答时可以结合ta的生活场景"

    # 加入当前时间，让每次请求的system prompt不同，防止API缓存
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prompt += f"\n\n当前时间：{now}"
    return prompt


async def chat_with_ai(
    user_message: str,
    user_chart: str,
    today_transits: str,
    chat_history: Optional[List[dict]] = None,
    user_info: dict = None,
) -> str:
    """核心对话函数（带RAG检索增强）"""
    system_prompt = build_system_prompt(user_chart, today_transits, user_info)

    # RAG: 根据用户问题检索相关星座知识
    try:
        from services.rag import retrieve_knowledge
        knowledge = retrieve_knowledge(user_message, n_results=3)
        if knowledge:
            system_prompt += f"\n\n相关星座知识（供你参考，不要原文复述）：\n{knowledge}"
            print(f"[RAG] 检索到知识: {knowledge[:80]}...")
        else:
            print("[RAG] 未检索到相关知识")
    except Exception as e:
        print(f"[RAG] 检索出错（不影响回复）: {e}")

    print(f"[CHAT] 用户消息: {user_message}")
    print(f"[CHAT] 星盘数据: {user_chart[:80]}...")

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    # 加入最近3轮对话历史，让AI有上下文
    if chat_history:
        recent = chat_history[-6:]  # 最近3轮（每轮一问一答=2条）
        for msg in recent:
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "max_tokens": 300,
                "temperature": 0.95,
                "top_p": 0.9,
                "frequency_penalty": 1.2,
                "presence_penalty": 1.0,
            },
        )

    if resp.status_code != 200:
        print(f"[CHAT ERROR] {resp.status_code} - {resp.text[:200]}")
        raise Exception(f"DeepSeek API error: {resp.status_code}")

    data = resp.json()
    reply = data["choices"][0]["message"]["content"]
    print(f"[CHAT] AI回复: {reply}")
    return reply


async def generate_daily_horoscope(
    user_chart: str,
    today_transits: str,
    nickname: str = "",
) -> dict:
    """生成每日运势（带维度评分）"""
    name_str = nickname if nickname else "宝"

    horoscope_prompt = f"""你是"今天会中奖吗"的运势助手。
请根据用户星盘和今日星象，生成个性化的每日运势。

要求：
1. 用纯JSON格式输出，不要任何其他文字
2. 根据真实星象判断，不要一味说好话
3. 评分1-5颗星，根据星象真实打分，不要全给高分
4. summary部分100-150字，语气像朋友早安问候，温暖自然
5. emoji控制在2-3个
6. 绝对不要使用markdown

请严格按以下JSON格式输出（不要加```json标记）：
{{
  "greeting": "亲爱的{name_str}",
  "summary": "今日运势概述文字...",
  "scores": {{
    "overall": 4,
    "love": 3,
    "career": 5,
    "finance": 3,
    "health": 4
  }},
  "lucky_color": "紫色",
  "lucky_number": 7,
  "tip": "一句简短的今日小贴士"
}}

用户星盘：
{user_chart}

今日星象：
{today_transits}
"""

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": horoscope_prompt},
                    {"role": "user", "content": "请生成今日运势"},
                ],
                "max_tokens": 600,
                "temperature": 0.8,
            },
        )

    if resp.status_code != 200:
        raise Exception(f"DeepSeek API error: {resp.status_code}")

    data = resp.json()
    content = data["choices"][0]["message"]["content"]

    try:
        clean = content.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1]
        if clean.endswith("```"):
            clean = clean.rsplit("```", 1)[0]
        clean = clean.strip()
        result = json.loads(clean)
        return result
    except (json.JSONDecodeError, KeyError):
        return {
            "greeting": f"亲爱的{name_str}",
            "summary": content,
            "scores": {"overall": 3, "love": 3, "career": 3, "finance": 3, "health": 3},
            "lucky_color": "紫色",
            "lucky_number": 7,
            "tip": "今天保持好心情就好～",
        }
