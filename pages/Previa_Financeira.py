import streamlit as st
import pandas as pd
from datetime import timedelta
import openpyxl

#   MELHORIA
#       FLAG filtrar títulos/previa
#       Tabela com títulos que deseja retirar


# --- DEFINIÇÕES DE FUNÇÕES, VARIÁVEIS e CONSTANTES ---
def verifica_corrige_df(dfLocal):
    # Converte vencimento e remove nulos conforme seu script 
    dfLocal["Vencimento"] = pd.to_datetime(dfLocal["Vencimento"], errors='coerce')
    dfLocal = dfLocal[dfLocal["Vencimento"].notnull()]
    return dfLocal
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

HOJE = pd.to_datetime("today").normalize()
ULTIMO_DIA = HOJE + pd.offsets.YearEnd(0)
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
st.set_page_config(page_title="Previsão Financeira", layout="wide")
st.title(":material/Bar_Chart: Controle de Fluxo de Caixa")

# --- BARRA LATERAL (INPUTS) ---
with st.sidebar:
    st.header("Configurações")
    arquivo_upload = st.file_uploader("Suba sua planilha Excel", type=["xlsx"])
    valor_inicial = st.number_input("Saldo Inicial (R$)", step=100.0)

    ignorar_previa = st.toggle("Ignorar Previa")

    col1, col2 = st.columns(2)
    with col1:
        data_i = st.date_input("Data Inicial", value=(HOJE), format="DD/MM/YYYY")
    with col2:
        data_f = st.date_input("Data Final", value=(ULTIMO_DIA), format="DD/MM/YYYY")
    
    

# --- PROCESSAMENTO ---
if arquivo_upload:
    # Carregamento dos dados
    if (data_i > data_f):
        st.error(":material/Warning: Data Inicial deve ser antes que a Data Final")
        st.stop()
    try:
        df = pd.read_excel(arquivo_upload,engine="openpyxl")
    except Exception as e:
        st.error(f"Erro {e}")
        st.warning("Tente abrir o arquivo e salvar novamente")
        st.stop()

    #Validação Colunas
    if df.columns.tolist() != COLUNAS_PLANILHA:
        st.error("O arquivo Excel não possui as colunas esperadas.")
        print(df.columns.tolist)
        st.stop()

    df = verifica_corrige_df(df)
    df['Data_Caixa'] = df.apply(calcular_data_caixa, axis=1)

    if ignorar_previa:
        df = df[df["Prev."] == "N"]

    # 4. Agrupamento e Separação de Colunas
    fluxo_caixa = df.groupby(['Data_Caixa', 'Tipo'])['Valor'].sum().unstack(fill_value=0)

    fluxo_caixa = fluxo_caixa.rename(columns={'P': 'Pagar', 'R': 'Receber'})

    # 5. Reindexação para garantir todos os dias do intervalo (inclusive vazios)
    idx = pd.date_range(data_i, data_f)
    fluxo_dia = fluxo_caixa.reindex(idx, fill_value=0)

    #Filtra o intervalo de acordo com data_i e data_f
    fluxo_dia = fluxo_dia.loc[data_i:data_f]

    # 6. Cálculos de Balanço e saldo considerando valor inciial
    fluxo_dia["Balanço_Diario"] = fluxo_dia['Receber'] - fluxo_dia['Pagar']
    fluxo_dia["Saldo_Dia"] = fluxo_dia['Balanço_Diario'].cumsum() + valor_inicial

    fluxo_dia.index = fluxo_dia.index.date

    # --- EXIBIÇÃO ---
    #Validação DF
    if fluxo_dia.empty:
        st.error(":material/Warning: Nenhuma informação encontrada")
        st.stop()
        print("df vazio")

    diferenca_saldo = fluxo_dia["Saldo_Dia"].iloc[-1] - (valor_inicial)
    
    # Métricas de Resumo 
    m1, m2, m3 = st.columns(3)
    #m1
    m1.metric(":green[:material/Place_Item: Total a Receber]", f"R$ {fluxo_dia['Receber'].sum():,.2f}")
    #m2
    m2.metric(":red[:material/Move_Item: Total a Pagar]", f"R$ {fluxo_dia['Pagar'].sum():,.2f}")   
    #m3 com diferença de cor
    if diferenca_saldo >=0:
        m3.metric(":material/Money_range: Saldo Final Projetado", f"R$ {fluxo_dia['Saldo_Dia'].iloc[-1]:,.2f}", delta=f"+ R$ {abs(diferenca_saldo):,.2f}")
    else:
        m3.metric(":material/Money_range: Saldo Final Projetado", f"R$ {fluxo_dia['Saldo_Dia'].iloc[-1]:,.2f}", delta=f"- R$ {abs(diferenca_saldo):,.2f}")

    st.divider()

    # Gráfico de Evolução do Saldo
    st.subheader(":material/Area_chart: Evolução do Saldo Acumulado")
    if fluxo_dia['Saldo_Dia'].iloc[-1]>0:
        st.area_chart(fluxo_dia["Saldo_Dia"], color="#004777")
    else:
        st.area_chart(fluxo_dia["Saldo_Dia"], color="#E40039")

    # Tabela de Dados
    st.subheader(":material/Unfold_More: Detalhamento Diário")
    #st.dataframe(fluxo_dia.style.format("R$ {:,.2f}"), use_container_width=True)
    num_cols = fluxo_dia.select_dtypes(include="number").columns
    st.dataframe(
        fluxo_dia
            .style.format("R$ {:,.2f}")
            .applymap(negativo_vermelho),
        height=720
            )
else:
    st.info("Aguardando o upload da planilha Excel para processar os dados.")