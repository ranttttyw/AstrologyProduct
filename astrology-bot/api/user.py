"""
用户模块 — 星盘档案管理 + 昵称
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import json

from api.auth import get_current_user
from models.database import (
    get_user, update_user_chart, update_nickname, update_user_info, clear_horoscope_cache
)
from services.astrology import calculate_chart, format_chart_for_display

router = APIRouter()


class BindChartRequest(BaseModel):
    birth_date: str      # "1998-03-15"
    birth_time: Optional[str] = None  # "10:30" 可以为空
    birth_city: str      # "北京"


class NicknameRequest(BaseModel):
    nickname: str


class UserInfoRequest(BaseModel):
    gender: Optional[str] = None       # "男" / "女" / "其他"
    occupation: Optional[str] = None   # "学生" / "上班族" / 自由输入


class UserProfile(BaseModel):
    has_chart: bool
    nickname: Optional[str] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    birth_city: Optional[str] = None
    chart_summary: Optional[dict] = None


@router.post("/user/bindChart")
async def bind_chart(req: BindChartRequest, openid: str = Depends(get_current_user)):
    """
    绑定星盘：用户输入生日信息，后端计算星盘并存储
    """
    try:
        chart_data = calculate_chart(
            birth_date=req.birth_date,
            birth_time=req.birth_time or "12:00",  # 没有出生时间默认用正午
            birth_city=req.birth_city,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"星盘计算出错：{str(e)}")

    # 保存到数据库
    update_user_chart(
        openid=openid,
        birth_date=req.birth_date,
        birth_time=req.birth_time or "",
        birth_city=req.birth_city,
        chart_data=chart_data,
    )

    # 星盘更新后，清除运势缓存，下次会重新生成
    clear_horoscope_cache(openid)

    # 返回星盘摘要
    display = format_chart_for_display(chart_data)

    return {
        "success": True,
        "message": "星盘已生成",
        "chart": display,
        "has_birth_time": bool(req.birth_time),
    }


@router.post("/user/nickname")
async def set_nickname(req: NicknameRequest, openid: str = Depends(get_current_user)):
    """设置昵称"""
    nickname = req.nickname.strip()[:20]  # 最长20字
    if not nickname:
        raise HTTPException(status_code=400, detail="昵称不能为空")
    update_nickname(openid, nickname)
    return {"success": True, "nickname": nickname}


@router.post("/user/info")
async def set_user_info(req: UserInfoRequest, openid: str = Depends(get_current_user)):
    """设置用户性别和职业"""
    update_user_info(openid, gender=req.gender, occupation=req.occupation)
    return {"success": True}


@router.get("/user/profile", response_model=UserProfile)
async def get_profile(openid: str = Depends(get_current_user)):
    """
    获取用户星盘档案
    """
    user = get_user(openid)
    if not user or not user.get("chart_data"):
        return UserProfile(
            has_chart=False,
            nickname=user.get("nickname", "") if user else "",
            gender=user.get("gender", "") if user else "",
            occupation=user.get("occupation", "") if user else "",
        )

    chart_data = json.loads(user["chart_data"])
    display = format_chart_for_display(chart_data)

    return UserProfile(
        has_chart=True,
        nickname=user.get("nickname", ""),
        gender=user.get("gender", ""),
        occupation=user.get("occupation", ""),
        birth_date=user.get("birth_date"),
        birth_time=user.get("birth_time"),
        birth_city=user.get("birth_city"),
        chart_summary=display,
    )
