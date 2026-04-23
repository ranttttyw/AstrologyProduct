"""
每日运势模块
"""
from datetime import date
from fastapi import APIRouter, Depends
import json

from api.auth import get_current_user
from models.database import get_user, get_cached_horoscope, save_horoscope_cache
from services.ai import generate_daily_horoscope
from services.astrology import get_today_transits, format_chart_for_prompt, format_transits_for_prompt

router = APIRouter()


@router.get("/horoscope/today")
async def today_horoscope(openid: str = Depends(get_current_user)):
    """
    获取今日个性化运势（带评分维度）
    有缓存则直接返回，没有则调用AI生成
    """
    today = date.today().isoformat()

    # 检查缓存
    cached = get_cached_horoscope(openid, today)
    if cached:
        try:
            data = json.loads(cached)
            return {"horoscope": data, "date": today, "cached": True}
        except json.JSONDecodeError:
            # 旧格式缓存（纯文本），兼容处理
            return {"horoscope": {"summary": cached, "greeting": "", "scores": {}}, "date": today, "cached": True}

    # 获取用户星盘
    user = get_user(openid)
    if not user or not user.get("chart_data"):
        return {
            "horoscope": None,
            "date": today,
            "has_chart": False,
        }

    chart_data = json.loads(user["chart_data"])
    chart_text = format_chart_for_prompt(chart_data)
    nickname = user.get("nickname", "")

    # 获取今日星象
    transits = get_today_transits()
    transits_text = format_transits_for_prompt(transits)

    # 生成运势（结构化数据）
    try:
        horoscope = await generate_daily_horoscope(chart_text, transits_text, nickname)
    except Exception as e:
        print(f"运势生成出错: {e}")
        horoscope = {
            "greeting": f"亲爱的{nickname or '宝'}",
            "summary": "今日星象信号有些模糊，稍后再来看看吧～",
            "scores": {"overall": 3, "love": 3, "career": 3, "finance": 3, "health": 3},
            "tip": "放轻松，明天会更好",
        }

    # 缓存（存JSON字符串）
    save_horoscope_cache(openid, today, json.dumps(horoscope, ensure_ascii=False))

    return {"horoscope": horoscope, "date": today, "cached": False}
