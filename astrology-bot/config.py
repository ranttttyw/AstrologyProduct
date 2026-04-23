import os
from dotenv import load_dotenv

load_dotenv()

# DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# 微信小程序
WECHAT_APP_ID = os.getenv("WECHAT_APP_ID", "")
WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET", "")

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "change_me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 168  # 7天

# 数据库
# 默认使用项目目录下的data/，如果不可写则用临时目录
_default_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "astrology.db")
DB_PATH = os.getenv("DB_PATH", _default_db)
