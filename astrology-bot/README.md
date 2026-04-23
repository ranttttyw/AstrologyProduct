# 星语心事 — AI星座情绪陪伴助手

AI驱动的个性化星座决策助手，帮你在纠结时找到方向。

## 快速开始

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
echo "DEEPSEEK_API_KEY=你的key" > .env

# 4. 启动服务（同时serve前端页面和API）
python -m uvicorn main:app --port 8000

# 5. 打开浏览器访问 http://localhost:8000
```

## 技术栈

- **前端**: React 18 SPA（CDN加载，单HTML文件）
- **后端**: Python FastAPI
- **AI**: DeepSeek API
- **RAG**: jieba + TF-IDF 星座知识检索
- **星盘计算**: Kerykeion + Swiss Ephemeris（含纯数学fallback）
- **数据库**: SQLite
- **部署**: Render (Free Tier)

## API接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/guest-login` | POST | 访客登录，返回JWT token |
| `/api/chat` | POST | 发送消息，获取AI回复 |
| `/api/chat/history` | GET | 获取聊天历史 |
| `/api/user/profile` | GET | 获取用户档案 |
| `/api/user/nickname` | POST | 更新昵称 |
| `/api/user/info` | POST | 更新性别/职业 |
| `/api/user/bindChart` | POST | 绑定/更新星盘 |
| `/api/horoscope/today` | GET | 获取今日运势 |
| `/health` | GET | 健康检查 |

## 部署

项目使用 Render 部署。根目录的 `render.yaml` 已配置好：

1. 推到 GitHub
2. 在 Render 创建 Web Service，连接仓库
3. 设置环境变量 `DEEPSEEK_API_KEY` 和 `JWT_SECRET`
4. Deploy
