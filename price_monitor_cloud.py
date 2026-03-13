"""
yuegefan.com 砍价商品价格监控脚本
接口：POST https://yuegefan.com/sshi/api/cons/prodetail
用法：python price_monitor.py
"""

import requests
import json
import os
from datetime import datetime

# ===================== 配置区 =====================

# 监控的商品列表（可添加多个）
GOODS_LIST = [
    {
        "id": "9202509241129140003",
        "name": "商品1",
        "shareUid": "9202507292239220004",
        "uid": "9202507292239220004",
        "sign": "80da5ff5eea73e6f5f16fdd7602694cd",
        "lat": 39.904689788818359,
        "lon": 116.40717315673828,
    },
    {
        "id": "9202505161043360001",
        "name": "商品2",
        "shareUid": "9202507292239220004",
        "uid": "9202507292239220004",
        "sign": "08e66b7e0f0a736aea13feb20f90e53a",
        "lat": 39.904689788818359,
        "lon": 116.40717315673828,
        "group": "bej48",
    },
    {
        "id": "9202511111247480001",
        "name": "商品3",
        "shareUid": "9202507292239220004",
        "uid": "9202507292239220004",
        "sign": "90dc3ba93cebd4576298d21b689ae746",
        "lat": 39.904689788818359,
        "lon": 116.40717315673828,
    },
    {
        "id": "9202508071003180001",
        "name": "商品4",
        "shareUid": "9202507292239220004",
        "uid": "9202507292239220004",
        "sign": "2612b0a5f78f476768b68a740c48e837",
        "lat": 39.904689788818359,
        "lon": 116.40717315673828,
    },
    {
        "id": "9124459592889225020",
        "name": "商品5",
        "shareUid": "9202507292239220004",
        "uid": "9202507292239220004",
        "sign": "715551a8a8b976e5ef5e9dd3695d3fd9",
        "lat": 39.904689788818359,
        "lon": 116.40717315673828,
    },
    {
        "id": "9202512051326170001",
        "name": "商品6",
        "shareUid": "9202507292239220004",
        "uid": "9202507292239220004",
        "sign": "a9f60f3f5360caa482c6519d8807fda0",
        "lat": 39.904689788818359,
        "lon": 116.40717315673828,
    },
]

# 监控间隔（秒），建议不低于 60

# BEJ48 分组开关，True = 监控商品2并发邮件，False = 忽略
BEJ48_ENABLED = False

# 各商品邮件触发价格阈值（低于此价格发邮件）
PRICE_ALERT = {
    "9202509241129140003": 20,   # 商品1
    "9202505161043360001": 20,   # 商品2（bej48组）
    "9202511111247480001": 80,   # 商品3
    "9202508071003180001": 15,   # 商品4
    "9124459592889225020": 60,   # 商品5
    "9202512051326170001": 60,   # 商品6
}
# 180s内砍价人数超过此值也发邮件
CUT_ALERT_THRESHOLD = 4

# 历史价格记录文件
DATA_FILE = "price_history.json"

# ========== 通知配置（可选，填一个即可）==========

# Server酱推送到微信（免费，注册 https://sct.ftqq.com 获取 key）
SERVER_CHAN_KEY = ""  # 填入你的 SendKey，例如 "SCT123456xxx"

# 企业微信机器人 webhook
WECHAT_WORK_WEBHOOK = ""  # 填入 webhook URL

# Ntfy 推送频道
NTFY_TOPIC = "shishikanjiaqun"

# 163邮件推送
EMAIL_FROM = "ziyuece@163.com"
EMAIL_TO = "ziyuece@163.com"
EMAIL_AUTH_CODE = os.environ.get("EMAIL_AUTH_CODE", "ZBYFh3AUcTCCvX8K")

# ===================== 核心逻辑 =====================

API_URL = "https://yuegefan.com/sshi/api/cons/prodetail"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf254171e) XWEB/18787",
    "xweb_xhr": "1",
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "*/*",
    "Referer": "https://servicewechat.com/wxed04ca0f1cd5d04e/43/page-frame.html",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_history():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_history(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_price(goods):
    """查询单个商品当前价格"""
    body = {
        "id": goods["id"],
        "lat": goods["lat"],
        "lon": goods["lon"],
        "shareUid": goods["shareUid"],
        "sign": goods["sign"],
        "uid": goods["uid"],
    }
    try:
        resp = requests.post(API_URL, headers=HEADERS, json=body, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        d = data.get("data", data)  # 实际数据在 data.data 里
        if data.get("state") == "ok" or "price" in d:
            return {
                "name": d.get("name", goods["name"]),
                "price": float(d.get("price", 0)),
                "priceSource": float(d.get("priceSource", 0)),
                "cutAmt": int(d.get("cutAmtTotal", 0)),  # 累计总砍价次数
                "salesAmt": int(d.get("salesAmt", 0)),
            }
        else:
            print(f"[{now()}] ⚠️  接口返回异常: {data}")
            return None
    except Exception as e:
        print(f"[{now()}] ❌ 请求失败 ({goods['name']}): {e}")
        return None

def send_email(subject, message):
    """发送163邮件"""
    if not EMAIL_FROM or not EMAIL_AUTH_CODE:
        return
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.header import Header
        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
        with smtplib.SMTP_SSL("smtp.163.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_AUTH_CODE)
            server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
        print(f"[{now()}] 📧 邮件已发送：{subject}")
    except Exception as e:
        print(f"[{now()}] ❌ 邮件发送失败: {e}")

def check_all():
    history = load_history()
    for goods in GOODS_LIST:
        gid = goods["id"]
        result = fetch_price(goods)
        if result is None:
            continue

        name = result["name"]
        cur_price = result["price"]
        src_price = result["priceSource"]
        cut_amt = result["cutAmt"]

        if gid in history:
            prev_cut = history[gid].get("cutAmt", 0)
            new_cuts = max(0, cut_amt - prev_cut)
            cut_info = f" | +{new_cuts}人砍价" if new_cuts > 0 else ""
            print(f"[{now()}] {name}: ¥{cur_price}{cut_info}")

            # 邮件触发判断
            threshold = PRICE_ALERT.get(gid)
            is_bej48 = gid == "9202505161043360001"
            reasons = []
            if not is_bej48 or BEJ48_ENABLED:
                if threshold and cur_price < threshold:
                    reasons.append(f"当前价格 ¥{cur_price} 低于目标价 ¥{threshold}")
                if new_cuts >= CUT_ALERT_THRESHOLD:
                    reasons.append(f"180s内新增砍价 {new_cuts} 人")
            if reasons:
                short_name = name[:10]
                if threshold and cur_price < threshold:
                    subject = f"食时-{short_name}-价格低于¥{threshold}"
                else:
                    subject = f"食时-{short_name}-{new_cuts}人砍价"
                body = name + "\n\u5f53\u524d\u4ef7\u683c\uff1a\xa5" + str(cur_price) + "\n" + "\n".join(reasons)
                send_email(subject, body)
        else:
            print(f"[{now()}] 🆕 {name}: ¥{cur_price}（原价¥{src_price}）")
            # 首次记录也检查价格阈值
            threshold = PRICE_ALERT.get(gid)
            is_bej48 = gid == "9202505161043360001"
            if threshold and cur_price < threshold and (not is_bej48 or BEJ48_ENABLED):
                subject = f"食时-{name[:10]}-价格低于¥{threshold}"
                body = name + "\n当前价格：¥" + str(cur_price) + "\n首次检测即低于目标价¥" + str(threshold)
                send_email(subject, body)

        history[gid] = {
            "name": name,
            "price": cur_price,
            "priceSource": src_price,
            "cutAmt": cut_amt,
            "last_checked": now()
        }

    save_history(history)



def export_data():
    """把当前价格数据导出为 data.json 供网页展示"""
    history = load_history()

    # 读取上一次的 data.json 做对比
    prev = {}
    if os.path.exists("data.json"):
        try:
            with open("data.json", "r", encoding="utf-8") as f:
                old_data = json.load(f)
                for item in old_data.get("items", []):
                    prev[item["id"]] = item
        except:
            pass

    output = {
        "updated_at": now(),
        "items": []
    }
    for gid, info in history.items():
        threshold = PRICE_ALERT.get(gid)
        cur_price = info["price"]
        cur_cut = info.get("cutAmt", 0)
        prev_item = prev.get(gid, {})
        prev_price = prev_item.get("price", cur_price)
        prev_cut = prev_item.get("cutAmt", cur_cut)
        price_change = round(cur_price - prev_price, 2)
        cut_change = max(0, cur_cut - prev_cut)

        output["items"].append({
            "id": gid,
            "name": info["name"],
            "price": cur_price,
            "priceSource": info["priceSource"],
            "cutAmt": cur_cut,
            "cut_change": cut_change,       # 过去5分钟新增砍价人数
            "price_change": price_change,   # 过去5分钟价格变化
            "last_checked": info["last_checked"],
            "threshold": threshold,
            "below_threshold": threshold is not None and cur_price < threshold,
        })
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

def main():
    print(f"[{now()}] 开始检查...")
    check_all()
    export_data()
    print(f"[{now()}] 检查完成")

if __name__ == "__main__":
    main()
