"""
价格监控脚本（整合版）
- 食时平台 yuegefan.com
- 探探糖 ttt.bjlxkjyxgs.cn
"""

import requests
import json
import os
from datetime import datetime

# ===================== 食时配置 =====================

SHISHI_GOODS_LIST = [
    {"id": "9202509241129140003", "name": "商品1", "shareUid": "9202507292239220004", "uid": "9202507292239220004", "sign": "80da5ff5eea73e6f5f16fdd7602694cd", "lat": 39.904689788818359, "lon": 116.40717315673828},
    {"id": "9202505161043360001", "name": "商品2", "shareUid": "9202507292239220004", "uid": "9202507292239220004", "sign": "08e66b7e0f0a736aea13feb20f90e53a", "lat": 39.904689788818359, "lon": 116.40717315673828, "group": "bej48"},
    {"id": "9202511111247480001", "name": "商品3", "shareUid": "9202507292239220004", "uid": "9202507292239220004", "sign": "90dc3ba93cebd4576298d21b689ae746", "lat": 39.904689788818359, "lon": 116.40717315673828},
    {"id": "9202508071003180001", "name": "商品4", "shareUid": "9202507292239220004", "uid": "9202507292239220004", "sign": "2612b0a5f78f476768b68a740c48e837", "lat": 39.904689788818359, "lon": 116.40717315673828},
    {"id": "9124459592889225020", "name": "商品5", "shareUid": "9202507292239220004", "uid": "9202507292239220004", "sign": "715551a8a8b976e5ef5e9dd3695d3fd9", "lat": 39.904689788818359, "lon": 116.40717315673828},
    {"id": "9202512051326170001", "name": "商品6", "shareUid": "9202507292239220004", "uid": "9202507292239220004", "sign": "a9f60f3f5360caa482c6519d8807fda0", "lat": 39.904689788818359, "lon": 116.40717315673828},
]

SHISHI_PRICE_ALERT = {
    "9202509241129140003": 20,
    # "9202505161043360001": 20,  # 商品2 bej48组，不发邮件
    "9202511111247480001": 80,
    "9202508071003180001": 15,
    "9124459592889225020": 60,
    "9202512051326170001": 60,
}

BEJ48_ENABLED = False  # 改成 True 开启 BEJ48 组监控

# ===================== 探探糖配置 =====================

TANTANG_GOODS_LIST = [
    {"activitygoods_id": 18422, "threshold": 70,  "rqtoken": "dc0f603723711bef0596ae21368f19b4"},  # 鸿宾楼水煮鱼
    {"activitygoods_id": 24270, "threshold": 45,  "rqtoken": "06cbb399d8e46f0dd0b2641f6f9b58de"},
    {"activitygoods_id": 21878, "threshold": 35,  "rqtoken": "3b25e384bd1c0ae3fcbe794a78e457d3"},
    {"activitygoods_id": 39230, "threshold": 70,  "rqtoken": "2a4003e9e58891e855ebaeb2c54455f4"},
    {"activitygoods_id": 35560, "threshold": 55,  "rqtoken": "5b6284f9965b882cfbd2f40e23b3dd28"},
    {"activitygoods_id": 44260, "threshold": 40,  "rqtoken": "a75ad21b6ec8a96f3ab73cc25fb65060"},
    # BEJ48_ENABLED = False  # 改成 True 开启 BEJ48 组
]

TANTANG_TOKEN = "009ad327-dc3d-4f77-91d8-852b9e91eec4"
TANTANG_RQTOKEN_DEFAULT = "5846b7227dc6f87235982ff64b18d13a"

# ===================== 通用配置 =====================

CUT_ALERT_THRESHOLD = 20
DATA_FILE = "price_history.json"
TANTANG_DATA_FILE = "tantang_history.json"

EMAIL_FROM = "ziyuece@163.com"
EMAIL_TO = "ziyuece@163.com"
EMAIL_AUTH_CODE = os.environ.get("EMAIL_AUTH_CODE", "ZBYFh3AUcTCCvX8K")

# ===================== 核心函数 =====================

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def send_email(subject, message):
    if not EMAIL_AUTH_CODE:
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

# ===================== 食时 =====================

SHISHI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf254171e) XWEB/18787",
    "xweb_xhr": "1",
    "Content-Type": "application/json;charset=UTF-8",
    "Accept": "*/*",
    "Referer": "https://servicewechat.com/wxed04ca0f1cd5d04e/43/page-frame.html",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

def shishi_fetch(goods):
    body = {"id": goods["id"], "lat": goods["lat"], "lon": goods["lon"], "shareUid": goods["shareUid"], "sign": goods["sign"], "uid": goods["uid"]}
    try:
        resp = requests.post("https://yuegefan.com/sshi/api/cons/prodetail", headers=SHISHI_HEADERS, json=body, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        d = data.get("data", data)
        if data.get("state") == "ok" or "price" in d:
            return {"name": d.get("name", goods["name"]), "price": float(d.get("price", 0)), "priceSource": float(d.get("priceSource", 0)), "cutAmt": int(d.get("cutAmtTotal", 0))}
        print(f"[{now()}] ⚠️  食时接口异常: {data}")
        return None
    except Exception as e:
        print(f"[{now()}] ❌ 食时请求失败: {e}")
        return None

def check_shishi():
    history = load_json(DATA_FILE)
    for goods in SHISHI_GOODS_LIST:
        gid = goods["id"]
        result = shishi_fetch(goods)
        if result is None:
            continue
        name = result["name"]
        cur_price = result["price"]
        cut_amt = result["cutAmt"]
        if gid in history:
            prev_cut = history[gid].get("cutAmt", 0)
            new_cuts = max(0, cut_amt - prev_cut)
            cut_info = f" | +{new_cuts}人砍价" if new_cuts > 0 else ""
            print(f"[{now()}] 食时 {name}: ¥{cur_price}{cut_info}")
            threshold = SHISHI_PRICE_ALERT.get(gid)
            is_bej48 = goods.get("group") == "bej48"
            if not is_bej48 or BEJ48_ENABLED:
                reasons = []
                if threshold and cur_price < threshold:
                    reasons.append(f"当前价格 ¥{cur_price} 低于目标价 ¥{threshold}")
                if new_cuts >= CUT_ALERT_THRESHOLD:
                    reasons.append(f"180s内新增砍价 {new_cuts} 人")
                if reasons:
                    subject = f"食时-{name[:10]}-价格低于¥{threshold}" if threshold and cur_price < threshold else f"食时-{name[:10]}-{new_cuts}人砍价"
                    send_email(subject, name + "\n当前价格：¥" + str(cur_price) + "\n" + "\n".join(reasons))
        else:
            print(f"[{now()}] 食时 🆕 {name}: ¥{cur_price}（原价¥{result['priceSource']}）")
        history[gid] = {"name": name, "price": cur_price, "priceSource": result["priceSource"], "cutAmt": cut_amt, "last_checked": now()}
    save_json(DATA_FILE, history)

# ===================== 探探糖 =====================

TANTANG_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2541739) XWEB/18955",
    "xweb_xhr": "1",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "*/*",
    "token": TANTANG_TOKEN,
    "Referer": "https://servicewechat.com/wx454addfc6819a2ac/123/page-frame.html",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

def tantang_fetch(goods):
    body = {"activitygoods_id": goods["activitygoods_id"], "lon": 116.40717315673828, "lat": 39.90468978881836, "rqtoken": goods.get("rqtoken", TANTANG_RQTOKEN_DEFAULT)}
    try:
        resp = requests.post("https://ttt.bjlxkjyxgs.cn/api/shop/activity_detail", headers=TANTANG_HEADERS, data=body, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 1:
            d = data.get("data", {})
            return {"name": d.get("title", ""), "price": float(d.get("price", 0)), "y_price": float(d.get("y_price", 0)), "store": d.get("store", 0), "is_sell": d.get("is_sell", 0)}
        print(f"[{now()}] ⚠️  探探糖接口异常: {data.get('msg')}")
        return None
    except Exception as e:
        print(f"[{now()}] ❌ 探探糖请求失败: {e}")
        return None

def check_tantang():
    history = load_json(TANTANG_DATA_FILE)
    for goods in TANTANG_GOODS_LIST:
        gid = str(goods["activitygoods_id"])
        result = tantang_fetch(goods)
        if result is None:
            continue
        name = result["name"]
        cur_price = result["price"]
        store = result["store"]
        threshold = goods.get("threshold", 0)
        if gid in history:
            prev_price = history[gid]["price"]
            drop = round(prev_price - cur_price, 2)
            print(f"[{now()}] 探探糖 {name[:15]}: ¥{cur_price} 库存:{store}" + (f" ↓¥{drop}" if drop > 0 else ""))
        else:
            print(f"[{now()}] 探探糖 🆕 {name[:15]}: ¥{cur_price}（原价¥{result['y_price']}）库存:{store}")
        if threshold and cur_price < threshold:
            send_email(f"探探糖-{name[:10]}-价格低于¥{threshold}", f"{name}\n当前价格：¥{cur_price}\n库存：{store}\n目标价：¥{threshold}")
        history[gid] = {"name": name, "price": cur_price, "y_price": result["y_price"], "store": store, "last_checked": now()}
    save_json(TANTANG_DATA_FILE, history)

# ===================== 导出网页数据 =====================

def export_data():
    shishi_history = load_json(DATA_FILE)
    tantang_history = load_json(TANTANG_DATA_FILE)

    prev = {}
    if os.path.exists("data.json"):
        try:
            with open("data.json", "r", encoding="utf-8") as f:
                old_data = json.load(f)
                for item in old_data.get("items", []):
                    prev[item["id"]] = item
        except:
            pass

    output = {"updated_at": now(), "items": []}

    # 食时商品
    for gid, info in shishi_history.items():
        threshold = SHISHI_PRICE_ALERT.get(gid)
        cur_price = info["price"]
        cur_cut = info.get("cutAmt", 0)
        prev_item = prev.get(gid, {})
        price_change = round(cur_price - prev_item.get("price", cur_price), 2)
        cut_change = max(0, cur_cut - prev_item.get("cutAmt", cur_cut))
        output["items"].append({
            "id": gid, "source": "shishi",
            "name": info["name"], "price": cur_price, "priceSource": info["priceSource"],
            "cutAmt": cur_cut, "cut_change": cut_change, "price_change": price_change,
            "last_checked": info["last_checked"], "threshold": threshold,
            "below_threshold": threshold is not None and cur_price < threshold,
        })

    # 探探糖商品
    for gid, info in tantang_history.items():
        threshold = next((g["threshold"] for g in TANTANG_GOODS_LIST if str(g["activitygoods_id"]) == gid), None)
        cur_price = info["price"]
        prev_item = prev.get("tt_" + gid, {})
        price_change = round(cur_price - prev_item.get("price", cur_price), 2)
        output["items"].append({
            "id": "tt_" + gid, "source": "tantang",
            "name": info["name"], "price": cur_price, "priceSource": info["y_price"],
            "store": info.get("store", 0), "price_change": price_change,
            "last_checked": info["last_checked"], "threshold": threshold,
            "below_threshold": threshold is not None and cur_price < threshold,
        })

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

def main():
    print(f"[{now()}] 开始检查...")
    check_shishi()
    check_tantang()
    export_data()
    print(f"[{now()}] 检查完成")

if __name__ == "__main__":
    main()
