import os
import json
import gspread
import pandas as pd
from gspread_dataframe import get_as_dataframe, set_with_dataframe
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

# === Função para abrir e ler planilha por ID ===
def ler_planilha_por_id(nome_arquivo):
    planilha = client.open_by_key(planilhas_ids[nome_arquivo])
    aba = planilha.sheet1
    df = get_as_dataframe(aba).dropna(how="all")
    return df

# Lê os dados das planilhas principais
print("📥 Lendo planilhas de contas a receber e contas a pagar...")
df_receber = ler_planilha_por_id("FInanceiro_contas_a_receber_King")
df_pagar = ler_planilha_por_id("Financeiro_contas_a_pagar_King")

# Adiciona a coluna tipo
df_receber["tipo"] = "Receita"
df_pagar["tipo"] = "Despesa"

# Junta os dois dataframes
print("🔗 Consolidando dados de receitas e despesas...")
df_completo = pd.concat([df_receber, df_pagar], ignore_index=True)

# === CONVERSÃO DAS DATAS PARA FORMATO YYYY-MM-DD ===
campos_data = ['lastAcquittanceDate', 'financialEvent.competenceDate', 'dueDate']

print("📅 Convertendo campos de data para formato YYYY-MM-DD...")
for campo in campos_data:
    if campo in df_completo.columns:
        df_completo[campo] = pd.to_datetime(
            df_completo[campo], 
            format='mixed',
            dayfirst=True,
            errors='coerce'
        )
        df_completo[campo] = df_completo[campo].dt.strftime('%Y-%m-%d')
        df_completo[campo] = df_completo[campo].replace('NaT', '')

# Corrige valores da coluna categoriesRatio.value com base na condição
if 'categoriesRatio.value' in df_completo.columns and 'paid' in df_completo.columns:
    print("💰 Corrigindo valores de categoriesRatio.value...")
    df_completo['categoriesRatio.value'] = df_completo.apply(
        lambda row: row['paid'] if pd.notna(row['categoriesRatio.value']) and pd.notna(row['paid']) and row['categoriesRatio.value'] > row['paid'] else row['categoriesRatio.value'],
        axis=1
    )

# Estatísticas finais
print(f"\n📊 Resumo dos dados processados:")
print(f"  Total de registros: {len(df_completo)}")
if 'tipo' in df_completo.columns:
    print(f"  Receitas: {len(df_completo[df_completo['tipo'] == 'Receita'])}")
    print(f"  Despesas: {len(df_completo[df_completo['tipo'] == 'Despesa'])}")
if 'categoriesRatio.costCentersRatio.0.costCenter' in df_completo.columns:
    centros_custo = df_completo['categoriesRatio.costCentersRatio.0.costCenter'].nunique()
    print(f"  Centros de custo únicos: {centros_custo}")

# 📄 Abrir a planilha de saída
print("\n📤 Atualizando planilha consolidada...")
planilha_saida = client.open_by_key(planilhas_ids["Financeiro_Completo_King"])
aba_saida = planilha_saida.sheet1

# Limpa a aba e sobrescreve
aba_saida.clear()
set_with_dataframe(aba_saida, df_completo)

print("✅ Planilha consolidada atualizada com sucesso!")
print(f"📋 Total de colunas exportadas: {len(df_completo.columns)}")

# === NOVA ETAPA: PIVOTAGEM DOS CENTROS DE CUSTO ===
print("\n🔄 Iniciando pivotagem dos centros de custo...")

# Identifica as colunas de centro de custo e valor
colunas_centro_custo = [col for col in df_completo.columns if col.startswith("Centro de Custo ") and not col.startswith("Valor no Centro de Custo ")]
colunas_valor = [col for col in df_completo.columns if col.startswith("Valor no Centro de Custo ")]

print(f"  Encontradas {len(colunas_centro_custo)} colunas de centro de custo")
print(f"  Encontradas {len(colunas_valor)} colunas de valor")

if len(colunas_centro_custo) > 0 and len(colunas_valor) > 0:
    # Cria lista com todas as outras colunas que não são centro de custo
    colunas_id = [col for col in df_completo.columns if col not in colunas_centro_custo + colunas_valor]
    
    # Adiciona índice único para facilitar o merge
    df_completo_indexed = df_completo.reset_index(drop=False)
    df_completo_indexed = df_completo_indexed.rename(columns={'index': 'row_id'})
    
    # Atualiza colunas_id para incluir row_id
    colunas_id_merge = ['row_id'] + colunas_id
    
    # Melt dos centros de custo
    df_melted_cc = pd.melt(
        df_completo_indexed,
        id_vars=colunas_id_merge,
        value_vars=colunas_centro_custo,
        var_name='Centro_de_Custo_Temp',
        value_name='Centro_de_Custo_Unificado'
    )
    
    # Melt dos valores
    df_melted_valor = pd.melt(
        df_completo_indexed,
        id_vars=colunas_id_merge,
        value_vars=colunas_valor,
        var_name='Valor_Temp',
        value_name='paid_new'
    )
    
    # Extrai o número do centro de custo de cada coluna para fazer o match
    df_melted_cc['num'] = df_melted_cc['Centro_de_Custo_Temp'].str.extract(r'(\d+)$').astype(int)
    df_melted_valor['num'] = df_melted_valor['Valor_Temp'].str.extract(r'(\d+)$').astype(int)
    
    # Junta os dois dataframes pelo row_id e número do centro de custo
    df_final = df_melted_cc.merge(
        df_melted_valor[['row_id', 'num', 'paid_new']],
        on=['row_id', 'num'],
        how='left'
    )
    
    # Remove colunas temporárias
    df_final = df_final.drop(columns=['Centro_de_Custo_Temp', 'row_id', 'num'])
    
    # Converte valores negativos em positivos
    if 'paid_new' in df_final.columns:
        df_final['paid_new'] = df_final['paid_new'].abs()
        print("  ✅ Valores negativos convertidos para positivos")
    
    # Remove linhas onde centro de custo está vazio
    df_final = df_final[df_final['Centro_de_Custo_Unificado'].notna() & (df_final['Centro_de_Custo_Unificado'] != '')]
    
    print(f"  Total de registros após pivotagem: {len(df_final)}")
    
    # Cria nova aba ou atualiza aba existente
    try:
        aba_pivotada = planilha_saida.worksheet("Dados_Pivotados")
        aba_pivotada.clear()
    except:
        aba_pivotada = planilha_saida.add_worksheet(title="Dados_Pivotados", rows=len(df_final)+1, cols=len(df_final.columns))
    
    set_with_dataframe(aba_pivotada, df_final)
    print("✅ Planilha pivotada criada/atualizada com sucesso!")
    print(f"📋 Total de colunas na planilha pivotada: {len(df_final.columns)}")
else:
    print("⚠️ Nenhuma coluna de centro de custo encontrada para pivotagem")

