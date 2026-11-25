import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TRAVELPAYOUTS_TOKEN = os.getenv("TRAVELPAYOUTS_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ORIGIN = "TLV"
NOTIFY_PRICE = 100


def send_telegram_msg(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    requests.post(url, json=payload)


url = "https://api.travelpayouts.com/v2/prices/latest"
params = {
    "origin": ORIGIN,
    "currency": "eur",
    "limit": 30,
    "show_to_affiliates": "true",
    "token": TRAVELPAYOUTS_TOKEN
}

response = requests.get(url, params=params)
data = response.json()

flights = []
alert_messages = []

if response.status_code == 200 and data.get("success"):
    for item in data.get("data", []):
        city_to = item.get("destination")
        price = item.get("value")
        dep_date = item.get("depart_date")
        ret_date = item.get("return_date") or "В одну сторону"

        flights.append({
            "Destination": city_to,
            "Price (EUR)": price,
            "Departure": dep_date,
            "Return": ret_date
        })

        if price <= NOTIFY_PRICE:
            dep_ddmm = datetime.strptime(dep_date, "%Y-%m-%d").strftime("%d%m")
            link = f"https://www.aviasales.com/search/{ORIGIN}{dep_ddmm}{city_to}"

            if ret_date != "В одну сторону":
                ret_ddmm = datetime.strptime(ret_date, "%Y-%m-%d").strftime("%d%m")
                link += f"{ret_ddmm}1"
            else:
                link += "1"

            msg = f"✈️ <b>{ORIGIN} → {city_to}</b> за <b>€{price}</b>\n"
            msg += f"📅 Туда: {dep_date} | Обратно: {ret_date}\n"
            msg += f"🔗 <a href='{link}'>Открыть билет</a>"
            alert_messages.append(msg)

    pd.DataFrame(flights).to_csv("cheap_flights_tlv.csv", index=False)

    if alert_messages:
        full_msg = "🚨 <b>Дешевые билеты из Тель-Авива:</b>\n\n" + "\n\n".join(alert_messages[:10])
        send_telegram_msg(full_msg)
        print("✅ Уведомление отправлено в Telegram.")
    else:
        print("ℹ️ Билетов дешевле заданной цены сейчас нет.")
else:
    print(f"❌ Ошибка API: {response.status_code} — {response.text}")
