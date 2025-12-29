import pandas as pd
from datetime import timedelta

# --- DEFINIÇÕES E CONSTANTES ---
def abrir_excel():
    # Caminho original do seu arquivo 
    caminho_arquivo = r"C:\Users\Ismael\OneDrive - Mumu\BaseDados\PreviaFinanceira.xlsx"
    df = pd.read_excel(caminho_arquivo)
    return df
def verifica_corrige_df(dfLocal):
    # Converte vencimento e remove nulos conforme seu script 
    dfLocal["Vencimento"] = pd.to_datetime(dfLocal["Vencimento"], errors='coerce')
    dfLocal = dfLocal[dfLocal["Vencimento"].notnull()]
    return dfLocal
# Regra de Liquidação Bancária
def calcular_data_caixa(row):
    dt = row['Vencimento']
    wd = dt.weekday() # 0=Segunda, 4=Sexta, 5=Sábado, 6=Domingo
    
    # Regra Pagar (P): Respeitar dia útil (Sáb/Dom -> Segunda)
    if row['Tipo'] == 'P':
        if wd == 5: return dt + timedelta(days=2) # Sábado para Segunda
        if wd == 6: return dt + timedelta(days=1) # Domingo para Segunda
        return dt
    
    # Regra Receber (R): D+1 e Regras de Fim de Semana
    if row['Tipo'] == 'R':
        if wd == 4: return dt + timedelta(days=3) # Sexta para Segunda
        if wd in [5, 6, 0]: # Sábado, Domingo ou Segunda para Terça
            deslocamento = {5: 3, 6: 2, 0: 1}
            return dt + timedelta(days=deslocamento[wd])
        return dt + timedelta(days=1) # Terça, Quarta, Quinta para D+1

COLUNAS = ['Título', 'Emissão', 'Número', 'Vencimento', 'Valor', 'Dt. Baixa', 'Tipo', 'Emp.'] 
# --- INÍCIO DO SCRIPT ---

data_inicial = pd.to_datetime("2025-12-24") 
data_final = pd.to_datetime("2025-12-31")   
valor_inicial = -226_371.53                  

# 1. Carga e Limpeza
df = abrir_excel()
df = df[COLUNAS]
df = verifica_corrige_df(df)

# 2. Aplicação das Regras de Fluxo de Caixa
df['Data_Caixa'] = df.apply(calcular_data_caixa, axis=1)

# 3. Filtragem pelo intervalo de Liquidação (Data_Caixa)
mask = (df['Data_Caixa'] >= data_inicial) & (df['Data_Caixa'] <= data_final)
df_filtrado = df.loc[mask].copy()

# 4. Agrupamento e Separação de Colunas
# Criamos as colunas Pagar e Receber baseadas no Tipo
fluxo_caixa = df_filtrado.groupby(['Data_Caixa', 'Tipo'])['Valor'].sum().unstack(fill_value=0)

# Garantir que as colunas existam para evitar erro no cálculo
if 'P' not in fluxo_caixa: fluxo_caixa['P'] = 0.0
if 'R' not in fluxo_caixa: fluxo_caixa['R'] = 0.0

# Renomear para clareza conforme solicitado
fluxo_caixa = fluxo_caixa.rename(columns={'P': 'Pagar', 'R': 'Receber'})

# 5. Reindexação para garantir todos os dias do intervalo (inclusive vazios)
idx = pd.date_range(data_inicial, data_final)
fluxo_dia = fluxo_caixa.reindex(idx, fill_value=0)

# 6. Cálculos de Balanço e Saldo Acumulado [cite: 5]
fluxo_dia["Balanço_Diario"] = fluxo_dia['Receber'] - fluxo_dia['Pagar']
fluxo_dia['Saldo_Acumulado'] = fluxo_dia['Balanço_Diario'].cumsum() + valor_inicial

# --- RESULTADOS ---
print(f"🔹 Total de registros processados: {len(df_filtrado)}")
print(f"🔹 Saldo Inicial: R${valor_inicial:.2f}")
print("\n--- FLUXO DE CAIXA PROJETADO ---")
print(fluxo_dia[['Pagar', 'Receber', 'Balanço_Diario', 'Saldo_Acumulado']])