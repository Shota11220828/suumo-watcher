import requests
from bs4 import BeautifulSoup
import os
import time

# LINE Notify トークン（Railway の環境変数に入れる）
LINE_TOKEN = os.getenv("LINE_TOKEN")
LINE_URL = "https://notify-api.line.me/api/notify"

# 通知送信
def send_line(message):
    if LINE_TOKEN is None:
        print("LINE_TOKEN が設定されていません")
        return
    headers = {"Authorization": f"Bearer {LINE_TOKEN}"}
    data = {"message": message}
    requests.post(LINE_URL, headers=headers, data=data)

# SUUMO の駅別URL
URLS = [
    "https://suumo.jp/chintai/tokyo/sc_nakanosakaue/?page=1",
    "https://suumo.jp/chintai/tokyo/sc_nishishinjuku/?page=1"
]

# 条件
MAX_RENT = 250000          # 家賃25万以下（管理費除く）
MIN_SIZE = 45              # 45㎡以上
MAX_SIZE = 55              # 55㎡以下
REQUIRED_MADORI = "2LDK"   # 間取り
MAX_AGE = 3                # 築3年以内

# 重複通知防止用（Railwayは毎回初期化されるので簡易版）
sent_list = set()

def parse_suumo(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    items = soup.select(".cassetteitem")

    results = []

    for item in items:
        title = item.select_one(".cassetteitem_content-title").get_text(strip=True)
        address = item.select_one(".cassetteitem_detail-col1").get_text(strip=True)
        age_text = item.select_one(".cassetteitem_detail-col3").get_text(strip=True)

        # 築年数抽出
        age = 999
        if "築" in age_text:
            try:
                age = int(age_text.replace("築", "").replace("年", "").replace("新築", "0"))
            except:
                pass

        # 部屋情報
        rooms = item.select(".cassetteitem_other")
        for room in rooms:
            rent_text = room.select_one(".cassetteitem_price--rent").get_text(strip=True)
            mng_text = room.select_one(".cassetteitem_price--administration").get_text(strip=True)
            madori = room.select_one(".cassetteitem_madori").get_text(strip=True)
            size_text = room.select_one(".cassetteitem_menseki").get_text(strip=True)
            link = "https://suumo.jp" + room.select_one("a")["href"]

            # 数値変換
            rent = int(float(rent_text.replace("万円", "")) * 10000)
            size = float(size_text.replace("m2", ""))

            # 条件チェック
            if rent > MAX_RENT:
                continue
            if not (MIN_SIZE <= size <= MAX_SIZE):
                continue
            if REQUIRED_MADORI not in madori:
                continue
            if age > MAX_AGE:
                continue

            # 重複チェック
            if link in sent_list:
                continue
            sent_list.add(link)

            results.append(f"{title}\n{address}\n{madori} / {size}㎡\n家賃: {rent_text}（管理費 {mng_text}）\n築年数: {age_text}\n{link}")

    return results


def main():
    all_results = []

    for url in URLS:
        try:
            results = parse_suumo(url)
            all_results.extend(results)
            time.sleep(1)
        except Exception as e:
            print("Error:", e)

    if all_results:
        for msg in all_results:
            send_line(msg)
    else:
        print("該当物件なし")


if __name__ == "__main__":
    main()

