import requests
import json
import os
from datetime import datetime, timedelta

# Configurações
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
API_URL = 'https://www.purepilates.com.br/obter-agenda-aulas'

def fazer_requisicao_api():
    """Faz requisição à API do Pure Pilates"""
    headers = {
        'Cookie': 'ASP.NET_SessionId=y0xfrbke1wf0rujy5tqadi10'
    }

    data = {
        'idUnidade': '16',
        'origem': 'https://www.purepilates.com.br/vila-carrao/centro'
    }

    try:
        response = requests.post(API_URL, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao fazer requisição: {e}")
        return None

def filtrar_horarios(dados):
    """Filtra horários de terça e quinta, considerando hoje a partir da hora atual e futuro até 6 dias à frente"""
    if not dados or 'horarios' not in dados:
        return []

    agora = datetime.now()
    hoje = agora.date()
    limite = hoje + timedelta(days=6)
    horarios_filtrados = []

    for horario in dados['horarios']:
        dia_semana = horario.get('diaDaSemana', '')
        data_str = horario.get('data', '')
        hora_obj = horario.get('hora', {})
        hora = hora_obj.get('Hours', 0)
        minuto = hora_obj.get('Minutes', 0)

        try:
            data_obj = datetime.strptime(data_str, "%d/%m/%Y").date()
        except ValueError:
            continue

        # Se a data for hoje, considerar horário a partir da hora atual
        if data_obj == hoje:
            if dia_semana in ['Terça-Feira', 'Quinta-Feira'] and (hora > agora.hour or (hora == agora.hour and minuto >= agora.minute)):
                horarios_filtrados.append({
                    'data': horario.get('data'),
                    'diaDaSemana': dia_semana,
                    'horaVisivel': horario.get('horaVisivel'),
                    'professor': horario.get('professor'),
                    'identificador': f"{horario.get('data')}_{horario.get('horaReal')}"
                })
        else:
            # Para datas futuras, filtro padrão >= 13h
            if hoje <= data_obj <= limite and dia_semana in ['Terça-Feira', 'Quinta-Feira'] and hora >= 13:
                horarios_filtrados.append({
                    'data': horario.get('data'),
                    'diaDaSemana': dia_semana,
                    'horaVisivel': horario.get('horaVisivel'),
                    'professor': horario.get('professor'),
                    'identificador': f"{horario.get('data')}_{horario.get('horaReal')}"
                })

    return horarios_filtrados

def carregar_horarios_anteriores():
    """Carrega horários da execução anterior"""
    try:
        if os.path.exists('horarios_anteriores.json'):
            with open('horarios_anteriores.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar horários anteriores: {e}")

    return []

def salvar_horarios_atuais(horarios):
    """Salva horários atuais para próxima comparação"""
    try:
        with open('horarios_anteriores.json', 'w', encoding='utf-8') as f:
            json.dump(horarios, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar horários: {e}")

def detectar_novos_horarios(horarios_atuais, horarios_anteriores):
    """Compara e detecta novos horários disponíveis"""
    ids_anteriores = {h['identificador'] for h in horarios_anteriores}
    novos_horarios = [h for h in horarios_atuais if h['identificador'] not in ids_anteriores]

    return novos_horarios

def enviar_notificacao_telegram(mensagem):
    """Envia notificação via Telegram para multiples chat IDs separados por vírgula"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Token ou Chat ID do Telegram não configurados")
        return False

    chat_ids = [cid.strip() for cid in TELEGRAM_CHAT_ID.split(',') if cid.strip()]
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    sucesso_total = True

    for chat_id in chat_ids:
        payload = {
            'chat_id': chat_id,
            'text': mensagem,
            'parse_mode': 'HTML'
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            print(f"✅ Notificação enviada para {chat_id}")
        except Exception as e:
            print(f"Erro ao enviar para {chat_id}: {e}")
            sucesso_total = False

    return sucesso_total

def formatar_mensagem_novos_horarios(novos_horarios):
    """Formata mensagem com novos horários"""
    mensagem = "🎯 <b>Novos horários disponíveis no Pure Pilates!</b>\n\n"

    for horario in novos_horarios:
        mensagem += f"📅 {horario['data']} - {horario['diaDaSemana']}\n"
        mensagem += f"🕐 {horario['horaVisivel']}\n"
        mensagem += f"👤 {horario['professor']}\n\n"

    mensagem += "🔗 Agende já: gympass://"

    return mensagem

def main():
    print(f"Executando verificação em: {datetime.now()}")

    # 1. Fazer requisição à API
    dados = fazer_requisicao_api()
    if not dados:
        print("Não foi possível obter dados da API")
        return

    # 2. Filtrar horários relevantes
    horarios_atuais = filtrar_horarios(dados)
    print(f"Horários encontrados (filtrados): {len(horarios_atuais)}")

    # 3. Carregar horários anteriores
    horarios_anteriores = carregar_horarios_anteriores()
    print(f"Horários anteriores: {len(horarios_anteriores)}")

    # 4. Detectar novos horários
    novos_horarios = detectar_novos_horarios(horarios_atuais, horarios_anteriores)

    if novos_horarios:
        print(f"🎉 {len(novos_horarios)} novo(s) horário(s) detectado(s)!")
        mensagem = formatar_mensagem_novos_horarios(novos_horarios)
        enviar_notificacao_telegram(mensagem)
    else:
        print("Nenhum novo horário detectado")

    # 5. Salvar horários atuais para próxima execução
    salvar_horarios_atuais(horarios_atuais)

    print("Verificação concluída!")

if __name__ == "__main__":
    main()
