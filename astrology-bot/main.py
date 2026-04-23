"""
星语心事 — AI星座情绪陪伴助手 后端服务
"""
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from models.database import init_db
from api.auth import router as auth_router
from api.chat import router as chat_router
from api.user import router as user_router
from api.horoscope import router as horoscope_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时初始化数据库"""
    init_db()
    print("✨ 星语心事 · 后端启动成功")
    yield
    print("后端已关闭")


app = FastAPI(
    title="星语心事 API",
    description="AI星座情绪陪伴助手后端服务",
    version="1.0.0",
    lifespan=lifespan,
)

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(auth_router, prefix="/api", tags=["认证"])
app.include_router(chat_router, prefix="/api", tags=["聊天"])
app.include_router(user_router, prefix="/api", tags=["用户"])
app.include_router(horoscope_router, prefix="/api", tags=["运势"])


@app.get("/health")
async def health():
    return {"status": "ok"}


# 前端静态文件 — 放在最后，作为 fallback
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))

@app.get("/{path:path}")
async def serve_static(path: str):
    file_path = os.path.join(WEB_DIR, path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    # SPA fallback: 所有未匹配的路径都返回 index.html
    return FileResponse(os.path.join(WEB_DIR, "index.html"))
