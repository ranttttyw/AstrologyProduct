"""
认证模块 — 小程序登录 + JWT
"""
import time
import hashlib
import hmac
import json
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import httpx

from config import WECHAT_APP_ID, WECHAT_APP_SECRET, JWT_SECRET
from models.database import get_user, create_user, update_last_active

router = APIRouter()


class LoginRequest(BaseModel):
    code: str  # 小程序 wx.login() 返回的 code


class LoginResponse(BaseModel):
    token: str
    is_new_user: bool
    has_chart: bool


def create_token(openid: str) -> str:
    """生成简单的JWT token"""
    payload = {
        "openid": openid,
        "exp": int(time.time()) + 7 * 24 * 3600  # 7天过期
    }
    payload_str = json.dumps(payload)
    import base64
    payload_b64 = base64.urlsafe_b64encode(payload_str.encode()).decode()
    signature = hmac.new(JWT_SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def verify_token(token: str) -> str:
    """验证token，返回openid"""
    try:
        import base64
        payload_b64, signature = token.split(".")
        expected_sig = hmac.new(JWT_SECRET.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if signature != expected_sig:
            raise HTTPException(status_code=401, detail="Invalid token")
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload["exp"] < time.time():
            raise HTTPException(status_code=401, detail="Token expired")
        return payload["openid"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(authorization: str = Header(...)) -> str:
    """从Header中提取并验证用户身份，返回openid"""
    token = authorization.replace("Bearer ", "")
    openid = verify_token(token)
    update_last_active(openid)
    return openid


@router.post("/guest-login", response_model=LoginResponse)
async def guest_login():
    """
    Web版访客登录：自动生成一个访客ID，不需要微信
    """
    import uuid
    guest_id = f"guest_{uuid.uuid4().hex[:12]}"

    user = get_user(guest_id)
    is_new = user is None
    if is_new:
        create_user(guest_id)

    token = create_token(guest_id)
    has_chart = False if is_new else bool(user and user.get("chart_data"))

    return LoginResponse(token=token, is_new_user=is_new, has_chart=has_chart)


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """
    小程序登录
    前端调用 wx.login() 获取 code，传给此接口换取 token
    """
    openid = None

    # 开发模式：直接用code生成一个固定的dev openid
    if not WECHAT_APP_ID or not WECHAT_APP_SECRET:
        openid = "dev_user_001"
        print(f"[开发模式] 跳过微信验证，使用openid: {openid}")
    else:
        # 生产模式：用code换取openid
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.weixin.qq.com/sns/jscode2session",
                    params={
                        "appid": WECHAT_APP_ID,
                        "secret": WECHAT_APP_SECRET,
                        "js_code": req.code,
                        "grant_type": "authorization_code",
                    },
                )
            data = resp.json()
            openid = data.get("openid")
            if not openid:
                # 微信返回错误，fallback到开发模式
                openid = "dev_user_001"
                print(f"[微信登录失败] {data.get('errmsg', '')}, 使用开发模式")
        except Exception as e:
            openid = "dev_user_001"
            print(f"[微信登录异常] {e}, 使用开发模式")

    # 检查是否新用户
    user = get_user(openid)
    is_new = user is None
    if is_new:
        create_user(openid)

    has_chart = False
    if not is_new and user.get("chart_data"):
        has_chart = True

    # 生成 token
    token = create_token(openid)

    return LoginResponse(token=token, is_new_user=is_new, has_chart=has_chart)
