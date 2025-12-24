import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Previsão Financeira", layout="wide")

st.title("📊 Controle de Fluxo de Caixa")

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
    fluxo_dia['Saldo_Acumulado'] = fluxo_dia['Balanço'].cumsum() + valor_inicial

    # --- EXIBIÇÃO ---
    
    # Métricas de Resumo
    m1, m2, m3 = st.columns(3)
    m1.metric("Total a Receber", f"R$ {fluxo_dia['R'].sum():,.2f}")
    m2.metric("Total a Pagar", f"R$ {fluxo_dia['P'].sum():,.2f}")
    m3.metric("Saldo Final Projetado", f"R$ {fluxo_dia['Saldo_Acumulado'].iloc[-1]:,.2f}")

    st.divider()

    # Gráfico de Evolução do Saldo
    st.subheader("Evolução do Saldo Acumulado")
    st.line_chart(fluxo_dia['Saldo_Acumulado'])

    # Tabela de Dados
    st.subheader("Detalhamento Diário")
    st.dataframe(fluxo_dia.style.format("R$ {:,.2f}"), use_container_width=True)

else:
    st.info("Aguardando o upload da planilha Excel para processar os dados.")