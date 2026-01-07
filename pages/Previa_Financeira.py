import streamlit as st
import pandas as pd
from datetime import timedelta
import openpyxl

#   MELHORIA
#       Coluna Saldo Final Projetado na métrica ok
#       Coluna Saldo Final por cores ok
#       Ativar metricas de resumo ok


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
def negativo_vermelho(val):
    if isinstance(val, (int, float)) and val < 0:
        return "color: red"
    return ""

#HOJE formato "AAAA-MM-DD"
HOJE = pd.to_datetime("today").normalize()
COLUNAS_PLANILHA = [
    "Título",
    "Nat. Lançamento",
    "Forma Pagto",
    "Número",
    "Vencimento",
    "Valor",
    "Outros*",
    "Dt. Baixa",
    "Valor da Baixa",
    "Tipo",
    "Prev.",
    "Emp."
]


# --- INÍCIO DO SCRIPT STREAMLIT ---
# Configuração da página
st.set_page_config(page_title="Previsão Financeira", layout="wide")
st.title("📊 Controle de Fluxo de Caixa")

# --- BARRA LATERAL (INPUTS) ---
st.sidebar.header("Configurações")

# Upload do Arquivo
arquivo_upload = st.sidebar.file_uploader("Suba sua planilha Excel", type=["xlsx"])

# Inputs de Valor e Data
valor_inicial = st.sidebar.number_input("Saldo Inicial (R$)", step=100.0)

col1, col2 = st.sidebar.columns(2)
with col1:
    #data_i = st.date_input("Data Inicial", value=pd.to_datetime("2025-12-21"))
    data_i = st.date_input("Data Inicial", value=(HOJE), format="DD/MM/YYYY")
with col2:
    data_f = st.date_input("Data Final", value=pd.to_datetime("2025-12-31"), format="DD/MM/YYYY")

# --- PROCESSAMENTO ---
if arquivo_upload:
    # Carregamento dos dados
    try:
        df = pd.read_excel(arquivo_upload, engine="openpyxl")
    except:
        st.error(f"Erro ao ler o arquivo Excel:")
        st.stop()

    #Validação Colunas
    if df.columns.tolist() != COLUNAS_PLANILHA:
        st.error("O arquivo Excel não possui as colunas esperadas.")
        print(df.columns.tolist)
        st.stop()

    df = verifica_corrige_df(df)

    # 2. Aplicação das Regras de Fluxo de Caixa
    df['Data_Caixa'] = df.apply(calcular_data_caixa, axis=1)

    # 3. Filtragem pelo intervalo de Liquidação (Data_Caixa)
    mask = (df['Data_Caixa'] >= pd.to_datetime(data_i)) & (df['Data_Caixa'] <= pd.to_datetime(data_f))
    df_filtrado = df.loc[mask].copy()

    # 4. Agrupamento e Separação de Colunas
    # Colunas Pagar e Receber baseadas no Tipo
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

    # --- EXIBIÇÃO ---
    #Validação DF
    if fluxo_dia.empty:
        st.error(":material/Warning: Nenhuma informação encontrada: Verificar data filtrada")
        st.stop()
        print("df vazio")

    diferenca_saldo = fluxo_dia["Saldo_Dia"].iloc[-1] - (valor_inicial)
    
    # Métricas de Resumo 
    m1, m2, m3 = st.columns(3)
    #m1
    m1.metric("Total a Receber", f"R$ {fluxo_dia['Receber'].sum():,.2f}")
    #m2
    m2.metric("Total a Pagar", f"R$ {fluxo_dia['Pagar'].sum():,.2f}")   
    #m3 com diferença de cor
    if diferenca_saldo >=0:
        m3.metric("Saldo Final Projetado", f"R$ {fluxo_dia['Saldo_Dia'].iloc[-1]:,.2f}", delta=f"+ R$ {abs(diferenca_saldo):,.2f}")
    else:
        m3.metric("Saldo Final Projetado", f"R$ {fluxo_dia['Saldo_Dia'].iloc[-1]:,.2f}", delta=f"- R$ {abs(diferenca_saldo):,.2f}")

    st.divider()

    # Gráfico de Evolução do Saldo
    st.subheader("Evolução do Saldo Acumulado")
    if fluxo_dia['Saldo_Dia'].iloc[-1]>0:
        st.area_chart(fluxo_dia["Saldo_Dia"], color="#004777")
    else:
        st.area_chart(fluxo_dia["Saldo_Dia"], color="#E40039")

    # Tabela de Dados
    st.subheader("Detalhamento Diário")
    #st.dataframe(fluxo_dia.style.format("R$ {:,.2f}"), use_container_width=True)
    num_cols = fluxo_dia.select_dtypes(include="number").columns
    st.dataframe(
        fluxo_dia
            .style.format("R$ {:,.2f}")
            .applymap(negativo_vermelho))
else:
    st.info("Aguardando o upload da planilha Excel para processar os dados.")