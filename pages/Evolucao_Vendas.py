import pandas as pd
from datetime import date, timedelta
import streamlit as st
from utils import pandas_ler_excel


hoje = date.today()


def promover_cabecalho(df):
    colunas = df.iloc[0]
    colunas = colunas.str.split(" ")
    colunas = [" ".join(i[2:]).title() if len(i) > 2 else " ".join(i) for i in colunas]
    df.columns = colunas

    df = df[1:].reset_index(drop=True)
    return df


def filtrar_lojas_obsoletas(df):
    mascara_obsoleto = df["Grand Total"] == 0
    df_obsoleto = df[mascara_obsoleto].copy()
    df = df[~mascara_obsoleto].copy()
    return df, df_obsoleto


def encontra_periodos(hoje):
    def encontra_primeiro_ultimo_dia(hoje):
        if hoje.month == 12:
            ultimo_dia_mes = date(hoje.year + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia_mes = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1)

        primeiro_dia_mes = hoje.replace(day=1)
        return primeiro_dia_mes, ultimo_dia_mes

    primeiro_dia_mes, ultimo_dia_mes = encontra_primeiro_ultimo_dia(hoje)

    datas_mes_total = pd.date_range(start=primeiro_dia_mes, end=ultimo_dia_mes)
    datas_corridas = pd.date_range(start=primeiro_dia_mes, end=hoje)

    # --- 4. CONTAGEM DE DIAS ÚTEIS ---
    # Cenário 1: Centro de Distribuição (Seg a Sex -> menores que 5)
    cd_dias_totais = (datas_mes_total.weekday < 5).sum()
    cd_dias_corridos = (datas_corridas.weekday < 5).sum()

    # Cenário 2: Lojas (Dom a Sex -> diferentes de 5)
    loja_dias_totais = (datas_mes_total.weekday != 5).sum()
    loja_dias_corridos = (datas_corridas.weekday != 5).sum()

    return cd_dias_corridos, cd_dias_totais, loja_dias_corridos, loja_dias_totais


# --- 1. CONFIGURAÇÃO DO STREAMLIT ---
st.set_page_config(page_title="Sistema Mumix - Relatórios", layout="wide")
st.title(":material/Area_Chart: Análise de Fechamento e Projeção")

with st.sidebar:
    arquivo = st.file_uploader("Escolha o arquivo Excel", type=["xlsx"])

if not arquivo:
    st.info("[aba lateral] Aguardando upload do arquivo Excel para gerar o relatório.")
    st.stop()

resposta = pandas_ler_excel(arquivo)

if resposta["erro"]:
    st.error("Não foi possível carregar o arquivo")
    st.stop()

df = resposta["df"]

# if "Grand Total" not in df.columns:
#     st.error("O arquivo não possui a coluna 'Grand Total'")
#     st.stop()

# --- 2. TRATAMENTO/PROCESSAMENTO DE DADOS E FILTROS ---

df = promover_cabecalho(df)
df, df_obsoleto = filtrar_lojas_obsoletas(df)

cd_dias_corridos, cd_dias_totais, loja_dias_corridos, loja_dias_totais = (
    encontra_periodos(hoje)
)

# --- 5. CÁLCULO DE PROJEÇÃO E CRESCIMENTO ---
coluna_atual = df.columns[-2]
previsao_nome_coluna = ("Previa " + coluna_atual).upper()
coluna_ultimo_mes = df.columns[-3]
# coluna_ano_passado = df.columns[-14]


def calcular_previa(row):
    faturamento = row[coluna_atual]

    if row["Loja"] == "CENTRO DE DISTRIBUIÇÃO":
        dias_corridos, dias_totais = cd_dias_corridos, cd_dias_totais
    else:
        dias_corridos, dias_totais = loja_dias_corridos, loja_dias_totais

    if dias_corridos == 0:
        return 0
    return (faturamento / dias_corridos) * dias_totais


df[previsao_nome_coluna] = df.apply(calcular_previa, axis=1)

# Calculando os comparativos (tratando divisões por zero)
df["Crescimento_Ultimo_Mes (%)"] = (
    (df[previsao_nome_coluna] / df[coluna_ultimo_mes].replace(0, pd.NA)) - 1
) * 100

# df["Crescimento_Ano_Passado (%)"] = (
#     (df[previsao_nome_coluna] / df[coluna_ano_passado].replace(0, pd.NA)) - 1
# ) * 100

df_cx = df[df["Loja"] == "CENTRO DE DISTRIBUIÇÃO"]
df_lojas = df[df["Loja"] != "CENTRO DE DISTRIBUIÇÃO"]

# --- 6. EXIBIÇÃO NO DASHBOARD ---
# KPIs Globais (Somatório)
projecao_total = df[previsao_nome_coluna].sum()
realizado_ultimo_mes = df[coluna_ultimo_mes].sum()
crescimento_global = (
    ((projecao_total / realizado_ultimo_mes) - 1) * 100
    if realizado_ultimo_mes > 0
    else 0
)

# KPIs Lojas (Somatório)
projecao_lojas = df_lojas[previsao_nome_coluna].sum()
realizado_lojas = df_lojas[coluna_ultimo_mes].sum()
crescimento_lojas = (
    ((projecao_lojas / realizado_lojas) - 1) * 100 if realizado_lojas > 0 else 0
)


if not df_obsoleto.empty:
    with st.expander(f"[{len(df_obsoleto)}] Lojas inativas - Removidas da Análise"):
        st.caption("As lojas abaixo possuem total vendido igual a 0")
        st.dataframe(df_obsoleto[["Loja", "Grand Total"]], use_container_width=True)

st.markdown("## Dados Globais")
st.caption("CD + Lojas")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        f"Projeção Global :blue[{coluna_atual}]",
        f"R$ {projecao_total:,.2f}",
        f"{crescimento_global:.2f}% vs Julho",
    )
with col2:
    st.metric("Dias Restantes (CD)", f"{cd_dias_totais - cd_dias_corridos} dias")
with col3:
    st.metric("Dias Totais (CD)", f"{cd_dias_totais} dias")


st.markdown("## Dados Lojas")
st.caption("Somente Lojas")

co1, co2, co3 = st.columns(3)
with co1:
    st.metric(
        f"Projeção Loja :blue[{coluna_atual}]",
        f"R$ {projecao_lojas:,.2f}",
        f"{crescimento_lojas:.2f}% vs Julho",
    )

with co2:
    st.metric("Dias Restantes (Loja)", f"{loja_dias_totais - loja_dias_corridos} dias")
with co3:
    st.metric("Dias Totais (Loja)", f"{loja_dias_totais} dias")

st.divider()

# Tabelas
st.subheader(":material/table: Tabela Previsão Ultimo Mes")
# Formatando visualmente as colunas de percentual e moeda
df_display = (
    df_lojas[
        [
            "Loja",
            # df.columns[1],
            coluna_ultimo_mes,
            # coluna_atual,
            previsao_nome_coluna,
            "Crescimento_Ultimo_Mes (%)",
            # "Crescimento_Ano_Passado (%)",
        ]
    ]
    .sort_values(by=previsao_nome_coluna, ascending=False)
    .copy()
)
st.dataframe(
    df_display.style.format(
        {
            # df.columns[1]: "R$ {:,.2f}",
            coluna_ultimo_mes: "R$ {:,.2f}",
            # coluna_atual: "R$ {:,.2f}",
            previsao_nome_coluna: "R$ {:,.2f}",
            "Crescimento_Ultimo_Mes (%)": "{:.2f}%",
            # "Crescimento_Ano_Passado (%)": "{:.2f}%",
        }
    ),
    use_container_width=True,
    hide_index=True,
)
