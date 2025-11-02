import requests
import os
import json
import urllib3

# Desabilita warning de requisição HTTPS sem verificação de certificado
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = 'https://api.itauunibancoclube.com.br/notification-service/api/v1/beneficiary/banners?pageId=1'
CACHE_FILE = 'last_banners.json'

def fetch_data():
    resp = requests.get(API_URL, timeout=15, verify=False)
    resp.raise_for_status()
    return resp.json()

def load_last():
    if not os.path.exists(CACHE_FILE):
        return None
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_current(data):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def notify_telegram():
    token = os.getenv("TELEGRAM_BOT_TOKEN2")
    chat_id = os.getenv("TELEGRAM_CHAT_ID2")
    if not (token and chat_id):
        print("Configuração do Telegram ausente")
        return
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    msg = "👍 Atualização detectada nos banners do Itaú."
    data = {"chat_id": chat_id, "text": msg}
    resp = requests.post(url, json=data)
    print("Telegram status:", resp.status_code, resp.text)

if __name__ == "__main__":
    current = fetch_data()
    last = load_last()
    if current != last:
        notify_telegram()
        save_current(current)
    else:
        print("Nenhuma alteração detectada")
