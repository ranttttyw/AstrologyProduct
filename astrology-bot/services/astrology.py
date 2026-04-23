"""
星盘计算模块 — 基于 kerykeion (Swiss Ephemeris)
完整计算太阳、月亮、水星、金星、火星、木星、土星 + 上升点
"""
from datetime import datetime
from kerykeion import AstrologicalSubject

# 中国主要城市经纬度
CITY_COORDS = {
    "北京": (39.9042, 116.4074), "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644), "深圳": (22.5431, 114.0579),
    "杭州": (30.2741, 120.1551), "成都": (30.5728, 104.0668),
    "武汉": (30.5928, 114.3055), "南京": (32.0603, 118.7969),
    "重庆": (29.5630, 106.5516), "西安": (34.3416, 108.9398),
    "苏州": (31.2990, 120.5853), "天津": (39.3434, 117.3616),
    "长沙": (28.2282, 112.9388), "郑州": (34.7466, 113.6253),
    "青岛": (36.0671, 120.3826), "大连": (38.9140, 121.6147),
    "厦门": (24.4798, 118.0894), "昆明": (25.0389, 102.7183),
    "沈阳": (41.8057, 123.4315), "哈尔滨": (45.8038, 126.5350),
    "济南": (36.6512, 117.1201), "福州": (26.0745, 119.2965),
    "合肥": (31.8206, 117.2272), "贵阳": (26.6470, 106.6302),
    "石家庄": (38.0428, 114.5149), "太原": (37.8706, 112.5489),
    "南昌": (28.6820, 115.8579), "南宁": (22.8170, 108.3665),
    "兰州": (36.0611, 103.8343), "呼和浩特": (40.8414, 111.7519),
    "乌鲁木齐": (43.8256, 87.6168), "拉萨": (29.6500, 91.1000),
    "香港": (22.3193, 114.1694), "台北": (25.0330, 121.5654),
    "澳门": (22.1987, 113.5439),
    "宁波": (29.8683, 121.5440), "温州": (28.0015, 120.6722),
    "无锡": (31.4912, 120.3119), "东莞": (23.0208, 113.7518),
    "佛山": (23.0218, 113.1219), "珠海": (22.2710, 113.5767),
}

# 星座英文→中文
SIGN_CN = {
    "Ari": "白羊座", "Tau": "金牛座", "Gem": "双子座",
    "Can": "巨蟹座", "Leo": "狮子座", "Vir": "处女座",
    "Lib": "天秤座", "Sco": "天蝎座", "Sag": "射手座",
    "Cap": "摩羯座", "Aqu": "水瓶座", "Pis": "双鱼座",
    # 也兼容全名
    "Aries": "白羊座", "Taurus": "金牛座", "Gemini": "双子座",
    "Cancer": "巨蟹座", "Virgo": "处女座",
    "Libra": "天秤座", "Scorpio": "天蝎座", "Sagittarius": "射手座",
    "Capricorn": "摩羯座", "Aquarius": "水瓶座", "Pisces": "双鱼座",
}


def _sign_cn(sign_str: str) -> str:
    """星座英文转中文"""
    return SIGN_CN.get(sign_str, sign_str)


def _make_planet_data(planet_obj) -> dict:
    """从 kerykeion 行星对象提取标准数据"""
    return {
        "sign": planet_obj.sign,
        "sign_cn": _sign_cn(planet_obj.sign),
        "degree": round(planet_obj.position, 2),
    }


def calculate_chart(birth_date: str, birth_time: str, birth_city: str) -> dict:
    """
    计算用户完整星盘
    birth_date: "2004-08-02"
    birth_time: "23:30"
    birth_city: "宁波"
    """
    date_str = birth_date.replace("/", "-")
    parts = date_str.split("-")
    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])

    time_parts = birth_time.split(":")
    hour, minute = int(time_parts[0]), int(time_parts[1]) if len(time_parts) > 1 else 0

    lat, lng = CITY_COORDS.get(birth_city, (39.9042, 116.4074))

    subject = AstrologicalSubject(
        "User", year, month, day, hour, minute,
        lng=lng, lat=lat, tz_str="Asia/Shanghai",
    )

    result = {
        "sun": _make_planet_data(subject.sun),
        "moon": _make_planet_data(subject.moon),
        "mercury": _make_planet_data(subject.mercury),
        "venus": _make_planet_data(subject.venus),
        "mars": _make_planet_data(subject.mars),
        "jupiter": _make_planet_data(subject.jupiter),
        "saturn": _make_planet_data(subject.saturn),
        "ascendant": {
            "sign": subject.first_house.sign,
            "sign_cn": _sign_cn(subject.first_house.sign),
            "degree": round(subject.first_house.position, 2),
        },
    }

    # 额外：天王星、海王星、冥王星（高阶行星）
    result["uranus"] = _make_planet_data(subject.uranus)
    result["neptune"] = _make_planet_data(subject.neptune)
    result["pluto"] = _make_planet_data(subject.pluto)

    # 宫位信息
    houses = [
        subject.first_house, subject.second_house, subject.third_house,
        subject.fourth_house, subject.fifth_house, subject.sixth_house,
        subject.seventh_house, subject.eighth_house, subject.ninth_house,
        subject.tenth_house, subject.eleventh_house, subject.twelfth_house,
    ]
    result["houses"] = []
    for i, h in enumerate(houses, 1):
        result["houses"].append({
            "house": i,
            "sign": h.sign,
            "sign_cn": _sign_cn(h.sign),
            "degree": round(h.position, 2),
        })

    return result


def get_today_transits() -> dict:
    """获取今日行星位置（实时行运）"""
    now = datetime.now()

    subject = AstrologicalSubject(
        "Transit", now.year, now.month, now.day, now.hour, now.minute,
        lng=116.4074, lat=39.9042, tz_str="Asia/Shanghai",
    )

    transits = {
        "sun": _make_planet_data(subject.sun),
        "moon": _make_planet_data(subject.moon),
        "mercury": _make_planet_data(subject.mercury),
        "venus": _make_planet_data(subject.venus),
        "mars": _make_planet_data(subject.mars),
        "jupiter": _make_planet_data(subject.jupiter),
        "saturn": _make_planet_data(subject.saturn),
    }

    return transits


def format_chart_for_prompt(chart_data: dict) -> str:
    """把星盘数据格式化为AI可读的文字"""
    lines = []
    mapping = [
        ("sun", "太阳"), ("moon", "月亮"), ("ascendant", "上升"),
        ("mercury", "水星"), ("venus", "金星"), ("mars", "火星"),
        ("jupiter", "木星"), ("saturn", "土星"),
        ("uranus", "天王星"), ("neptune", "海王星"), ("pluto", "冥王星"),
    ]
    for key, name in mapping:
        data = chart_data.get(key)
        if data and isinstance(data, dict):
            sign = data.get("sign_cn", data.get("sign", "未知"))
            degree = data.get("degree", "")
            degree_str = f" {degree}°" if degree else ""
            lines.append(f"{name}：{sign}{degree_str}")

    # 宫位信息
    houses = chart_data.get("houses")
    if houses:
        lines.append("")
        lines.append("宫位：")
        for h in houses:
            lines.append(f"  第{h['house']}宫：{h['sign_cn']} {h['degree']}°")

    return "\n".join(lines) if lines else "用户未设置星盘"


def format_chart_for_display(chart_data: dict) -> dict:
    """格式化星盘数据用于前端展示"""
    display = {}
    mapping = [
        ("sun", "太阳", "☀️"), ("moon", "月亮", "🌙"), ("ascendant", "上升", "⬆️"),
        ("mercury", "水星", "☿"), ("venus", "金星", "♀"), ("mars", "火星", "♂"),
        ("jupiter", "木星", "♃"), ("saturn", "土星", "♄"),
        ("uranus", "天王星", "⛢"), ("neptune", "海王星", "♆"), ("pluto", "冥王星", "♇"),
    ]
    for key, name, emoji in mapping:
        data = chart_data.get(key)
        if data and isinstance(data, dict):
            degree = data.get("degree", 0)
            degree_int = int(degree) if degree else 0
            degree_min = int(round((degree - degree_int) * 60)) if degree else 0
            display[key] = {
                "name": name,
                "emoji": emoji,
                "sign": data.get("sign_cn", data.get("sign", "未知")),
                "degree": degree,
                "degree_text": f"{degree_int}°{degree_min}'",
            }
    return display


def format_transits_for_prompt(transits: dict) -> str:
    """把今日行运格式化为AI可读的文字"""
    lines = [f"今日行星位置（{datetime.now().strftime('%Y年%m月%d日')}）："]
    mapping = [
        ("sun", "太阳"), ("moon", "月亮"), ("mercury", "水星"),
        ("venus", "金星"), ("mars", "火星"), ("jupiter", "木星"),
        ("saturn", "土星"),
    ]
    for key, name in mapping:
        data = transits.get(key)
        if data:
            sign = data.get("sign_cn", data.get("sign", ""))
            lines.append(f"  {name}在{sign} {data.get('degree', '')}°")

    return "\n".join(lines)
