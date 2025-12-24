import streamlit as st
import pandas as pd
from datetime import timedelta

#   MELHORIA
#       Coluna Saldo Final Projetado na métrica
#       Coluna Saldo Final por cores
#       Ativar metricas de resumo
#       Opção de escolher data inicial e final


# Configuração da página
st.set_page_config(page_title="Previsão Financeira", layout="wide")

st.title("📊 Controle de Fluxo de Caixa")

# --- DEFINIÇÕES DE FUNÇÕES, VARIÁVEIS e CONSTANTES ---
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

# --- BARRA LATERAL (INPUTS) ---
st.sidebar.header("Configurações")

# Upload do Arquivo
arquivo_upload = st.sidebar.file_uploader("Suba sua planilha Excel", type=["xlsx"])

# Inputs de Valor e Data
valor_inicial = st.sidebar.number_input("Saldo Inicial (R$)", value=-23418.31, step=100.0)

col1, col2 = st.sidebar.columns(2)
with col1:
    data_i = st.date_input("Data Inicial", value=pd.to_datetime("2025-12-21"))
with col2:
    data_f = st.date_input("Data Final", value=pd.to_datetime("2025-12-31"))

# --- PROCESSAMENTO ---
if arquivo_upload:
    # Carregamento dos dados
    df = pd.read_excel(arquivo_upload)

    if True:
        df = verifica_corrige_df(df)

        # 2. Aplicação das Regras de Fluxo de Caixa
        df['Data_Caixa'] = df.apply(calcular_data_caixa, axis=1)

        # 3. Filtragem pelo intervalo de Liquidação (Data_Caixa)
        mask = (df['Data_Caixa'] >= pd.to_datetime(data_i)) & (df['Data_Caixa'] <= pd.to_datetime(data_f))
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
        idx = pd.date_range(data_i, data_f)
        fluxo_dia = fluxo_caixa.reindex(idx, fill_value=0)

        # 6. Cálculos de Balanço e Saldo Acumulado [cite: 5]
        fluxo_dia["Balanço_Diario"] = fluxo_dia['Receber'] - fluxo_dia['Pagar']
        fluxo_dia["Saldo_Dia"] = fluxo_dia['Balanço_Diario'].cumsum() + valor_inicial

    if False:
        COLUNAS = ['Título', 'Emissão', 'Número', 'Vencimento', 'Valor', 'Dt. Baixa', 'Tipo', 'Emp.']
        df = df[COLUNAS]

        # Limpeza e Conversão
        df["Vencimento"] = pd.to_datetime(df["Vencimento"], errors='coerce')
        df = df[df["Vencimento"].notnull()]

        # Filtro de Datas
        mask = (df['Vencimento'] >= pd.to_datetime(data_i)) & (df['Vencimento'] <= pd.to_datetime(data_f))
        df_filtrado = df.loc[mask].copy()

        # Cálculo do Fluxo
        fluxo_dia = df_filtrado.groupby(['Vencimento', 'Tipo'])['Valor'].sum().unstack(fill_value=0)
        
        # Garantir colunas R e P
        if 'R' not in fluxo_dia: fluxo_dia['R'] = 0.0
        if 'P' not in fluxo_dia: fluxo_dia['P'] = 0.0

        # Balanço e Acumulado
        fluxo_dia["Balanço"] = fluxo_dia['R'] - fluxo_dia['P']
        fluxo_dia["Saldo_Dia"] = fluxo_dia['Balanço'].cumsum() + valor_inicial

    # --- EXIBIÇÃO ---
    
    # Métricas de Resumo
    #m1, m2, m3 = st.columns(3)
    #m1.metric("Total a Receber", f"R$ {fluxo_dia['R'].sum():,.2f}")
    #m2.metric("Total a Pagar", f"R$ {fluxo_dia['P'].sum():,.2f}")
    #m3.metric("Saldo Final Projetado", f"R$ {fluxo_dia["Saldo_Dia"].iloc[-1]:,.2f}")

    st.divider()

    # Gráfico de Evolução do Saldo
    st.subheader("Evolução do Saldo Acumulado")
    st.line_chart(fluxo_dia["Saldo_Dia"])

    # Tabela de Dados
    st.subheader("Detalhamento Diário")
    st.dataframe(fluxo_dia.style.format("R$ {:,.2f}"), use_container_width=True)
else:
    st.info("Aguardando o upload da planilha Excel para processar os dados.")