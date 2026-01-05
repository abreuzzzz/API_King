import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 🔐 Lê o segredo e salva como credentials.json
gdrive_credentials = os.getenv("GDRIVE_SERVICE_ACCOUNT")
with open("credentials.json", "w") as f:
    json.dump(json.loads(gdrive_credentials), f)

# 📌 Autenticação com Google
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# === IDs das planilhas ===
planilhas_ids = {
    "FInanceiro_contas_a_receber_King": "1yw2j8uUMzFSE8w7HGca2N0OfaYcLD07koql5ch-nV4o",
    "Financeiro_contas_a_pagar_King": "1YY2Svu6VSq0VkCCsu4u3b-i0PXfKWPtvK5Lj0citKMM",
    "Financeiro_Completo_King": "1xwp9gIz0lV4mW5geUBESj1W59QSySdVYipThXAOUgrU"
}

print("🗑️ Iniciando exclusão COMPLETA de todas as linhas das planilhas...")

# 1. Limpa TUDO de Contas a Receber
print("\n📋 Limpando: FInanceiro_contas_a_receber_King")
planilha_receber = client.open_by_key(planilhas_ids["FInanceiro_contas_a_receber_King"])
aba_receber = planilha_receber.sheet1
aba_receber.clear()
print("  ✅ Todas as linhas excluídas (incluindo cabeçalho)")

# 2. Limpa TUDO de Contas a Pagar
print("\n📋 Limpando: Financeiro_contas_a_pagar_King")
planilha_pagar = client.open_by_key(planilhas_ids["Financeiro_contas_a_pagar_King"])
aba_pagar = planilha_pagar.sheet1
aba_pagar.clear()
print("  ✅ Todas as linhas excluídas (incluindo cabeçalho)")

# 3. Limpa TUDO de Financeiro Completo - Aba principal (sheet1)
print("\n📋 Limpando: Financeiro_Completo_King (sheet1)")
planilha_completo = client.open_by_key(planilhas_ids["Financeiro_Completo_King"])
aba_completo = planilha_completo.sheet1
aba_completo.clear()
print("  ✅ Todas as linhas excluídas (incluindo cabeçalho)")

# 4. Limpa TUDO de Financeiro Completo - Aba Dados_Pivotados (se existir)
print("\n📋 Limpando: Financeiro_Completo_King (Dados_Pivotados)")
try:
    aba_pivotada = planilha_completo.worksheet("Dados_Pivotados")
    aba_pivotada.clear()
    print("  ✅ Todas as linhas excluídas (incluindo cabeçalho)")
except:
    print("  ⚠️ Aba 'Dados_Pivotados' não encontrada")

print("\n🎉 Limpeza completa concluída com sucesso!")
print("⚠️ ATENÇÃO: Todas as linhas foram removidas, incluindo os cabeçalhos")
