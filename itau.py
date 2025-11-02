import requests
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SITE_URL = 'https://app.itauunibancoclube.com.br'
PHRASE = 'Em breve divulgaremos a data de liberação dos pacotes de Natal e Ano Novo'

def check_phrase():
    resp = requests.get(SITE_URL, timeout=15, verify=False)
    has_phrase = PHRASE in resp.text
    return has_phrase

def send_telegram(msg):
    token = os.getenv("TELEGRAM_BOT_TOKEN2")
    chat_id = os.getenv("TELEGRAM_CHAT_ID2")
    if not (token and chat_id):
        print("Configuração do Telegram ausente")
        return
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    data = {
        "chat_id": chat_id,
        "text": msg
    }
    requests.post(url, json=data)

if __name__ == "__main__":
    if not check_phrase():
        send_telegram("Atenção: Frase sumiu do site do Itaú Clube. Confira os pacotes de Natal/Ano Novo!")
