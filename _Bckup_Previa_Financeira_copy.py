import pandas as pd

# --- DEFINIÇÕES E CONSTANTES ---
#Abre excel
def abrir_excel():
    caminho_arquivo = r"C:\Users\Ismael\OneDrive - Mumu\BaseDados\PreviaFinanceira.xlsx"
    df = pd.read_excel(caminho_arquivo)
    return df
#Verificação/Validação do DataFrame
def verifica_corrige_df(dfLocal, mostrar_info):
    #Inserir informações para validação se foi puxado excel correto
    # Empresa == 10
    # Dt.Baixa == ""

    dfLocal["Vencimento"] = pd.to_datetime(dfLocal["Vencimento"], errors='coerce')
    #Remove colunas sujas/em branco
    dfLocal = dfLocal[dfLocal["Vencimento"].notnull()]

    if mostrar_info:
        print("Verificando DataFrame...")
        print(dfLocal.head())
        print(dfLocal.info())
        print(dfLocal.describe())
    
    return dfLocal

COLUNAS = ['Título', 'Emissão', 'Número', 'Vencimento', 'Valor', 'Dt. Baixa', 'Tipo', 'Emp.']

# --- INÍCIO DO SCRIPT ---

data_inicial = pd.to_datetime("2025-12-21")
data_final = pd.to_datetime("2025-12-31")
valor_inicial = -23418.31

#Abre e filtra colunas
df = abrir_excel()
df = df[COLUNAS]

#!!
print(f"🔹 {len(df)}")
df = verifica_corrige_df(df, False)

# Filtrar o intervalo de datas desejado
mask = (df['Vencimento'] >= data_inicial) & (df['Vencimento'] <= data_final)
df_filtrado = df.loc[mask].copy()

#!!
print(f"🔹 {len(df_filtrado)}")

# Tabelas dinâmicas para somar os valores por dia
fluxo_dia = df_filtrado.groupby(['Vencimento', 'Tipo'])['Valor'].sum().unstack(fill_value=0)



#Balanço diario
fluxo_dia["Balanço"] = fluxo_dia.get('R', 0) - fluxo_dia.get('P', 0)

fluxo_dia['Saldo_Acumulado'] = fluxo_dia['Balanço'].cumsum() + valor_inicial

print(f"Valor Inicial: R${valor_inicial:.2f}")
print(fluxo_dia)




