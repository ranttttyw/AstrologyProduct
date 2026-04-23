# 星语 — 微信小程序星座决策助手

AI驱动的个性化星座决策助手，帮你在纠结时找到方向。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key

# 3. 启动服务
uvicorn main:app --reload --port 8000

# 4. 查看API文档
# 打开 http://localhost:8000/docs
```

## 技术栈

- **后端**: Python + FastAPI
- **AI**: DeepSeek API
- **星盘计算**: flatlib + Swiss Ephemeris
- **数据库**: SQLite
- **前端**: 微信小程序（原生）

## API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/login` | POST | 小程序登录 |
| `/api/chat` | POST | 发送消息，获取AI回复 |
| `/api/user/bindChart` | POST | 绑定星盘 |
| `/api/user/profile` | GET | 获取用户档案 |
| `/api/horoscope/today` | GET | 获取今日运势 |
