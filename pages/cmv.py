import streamlit as st
from graphPloty import (
    CMV_fig_TOPMargem,
    CMV_fig_TOPFaturamento,
    CMV_fig_Fin_Margem2,
    CMV_fig_Margem_Margem2,
)
from utils import pandas_ler_excel


def calcular_metricas(df, fator_giro, fator_margem):
    colunas_padrao = [
        "Chamada",
        "Nome",
        "Qt Estoque",
        "Qt Venda",
        "Giro",
        "Total Venda [R$]",
        "Total Custo [R$]",
        "Margem (%)",
        "Markup (%)",
    ]

    df["Giro"] = (df["Qt Venda"] / (df["Qt Estoque"] + 0.01)) * 100
    df["Giro"] = round(df["Giro"], 2)

    df["Markup (%)"] = round(df["Margem (%)"], 3)
    df["Margem (%)"] = (df["Vl Financ."] - df["CMV"]) / df["Vl Financ."] * 100

    # Resumo Financeiro
    total_venda = df["Vl Financ."].sum()
    total_cmv = df["CMV"].sum()
    margem_media = (
        ((total_venda - total_cmv) / total_venda * 100) if total_venda != 0 else 0
    )

    # Rename
    df = df.rename(
        columns={"Vl Financ.": "Total Venda [R$]", "CMV": "Total Custo [R$]"}
    )

    # Filter
    alerta_giro = df[(df["Qt Estoque"] > 0) & (df["Giro"] < fator_giro)]

    alerta_margem = alerta_giro[(alerta_giro["Margem (%)"] < margem_media)]
    alerta_margem = alerta_margem[colunas_padrao].sort_values("Margem (%)")

    alerta_margem_filtro = df[df["Margem (%)"] < fator_margem]
    alerta_margem_filtro = alerta_margem_filtro[colunas_padrao].sort_values(
        "Margem (%)", ascending=True
    )

    alerta_giro = alerta_giro[colunas_padrao].sort_values("Giro")

    alerta_prejuizo = df[df["Margem (%)"] < 0].copy()
    alerta_prejuizo = alerta_prejuizo[colunas_padrao]

    alerta_negativo = df[df["Qt Estoque"] < 0]
    alerta_negativo = alerta_negativo[colunas_padrao].sort_values("Qt Estoque")

    resumo = {
        "faturamento": total_venda,
        "cmv_total": total_cmv,
        "margem": margem_media,
    }
    retorno_alerta = {
        "alerta_margem": alerta_margem,
        "alerta_prejuizo": alerta_prejuizo,
        "alerta_giro": alerta_giro,
        "alerta_magem_filtro": alerta_margem_filtro,
        "alerta_negativo": alerta_negativo,
    }

    return df, retorno_alerta, resumo


st.set_page_config(page_title="Relatório CMV", layout="wide")

COLUNAS_EXCEL = [
    "Chamada",
    "Nome",
    "Dt Ult. Movim",
    "Qt Estoque",
    "Qt Venda",
    "Vl Financ.",
    "CMV",
    "Margem (%)",
]

FORMATACAO_ALERTAS = {
    "Qt Estoque": "{:.2f}",
    "Qt Venda": "{:.2f}",
    "Giro": "{:.2f}",
    "Total Venda [R$]": "R$ {:.2f}",
    "Total Custo [R$]": "R$ {:.2f}",
    "Margem (%)": "{:.2f} %",
    "Markup (%)": "{:.2f} %",
}

diclamer_aba = "As informações abaixos poderão ser alteradas conforme o :blue[filtro] na aba lateral"

#   LOGIN
# if "user" not in st.session_state:
#     st.session_state.user = None
#     st.session_state.session = None

# if (st.session_state.user == None) or (st.session_state.perfil['status']!='ativo') or (st.session_state.perfil['role'] not in ['administrador', 'usuario']):
#     st.markdown("## :material/Close: Area Restrita")
#     if st.button('Realizar login'):
#         st.switch_page('login.py')
#     st.stop()

# perfil = st.session_state.perfil

st.title(":material/Bar_Chart: Relatório CMV")
# Sidebar para carregar o arquivo
with st.sidebar:
    #     if st.button("Sair do Sistema"):
    #         st.session_state.user = None
    #         st.rerun()
    #     st.markdown(f"# :blue[{perfil['nome']}]")
    #     st.markdown(f"{perfil['role'].title()}")
    #     st.divider()

    st.markdown("# Configurações")
    st.markdown("## Planilha")
    arquivo = st.file_uploader("Escolha o arquivo Excel", type=["xlsx"])

    st.markdown("## Filtro")
    fator_giro = st.number_input(
        ":blue[Baixo Giro] | Digite a porcentagem desejada do giro do produto",
        0.0,
        100.0,
        2.0,
        format="%.2f",
        step=1.0,
        key="giroInput",
    )

    fator_margem = st.number_input(
        ":blue[Baixa Margem] | Digite a porcentagem desejada da margem",
        0.0,
        100.0,
        3.0,
        format="%.2f",
        step=1.0,
        key="margemInput",
    )

    st.markdown("## Filtro Gráfico")
    ignora_margem_ficticia = st.toggle("Deseja ignorar magem >90%?")

if not arquivo:
    st.info("[aba lateral] Aguardando upload do arquivo Excel para gerar o relatório.")
    st.stop()

# Chama as funções do arquivo de processamento
resposta = pandas_ler_excel(arquivo, COLUNAS_EXCEL)

if resposta["erro"]:
    st.stop("Não foi possível carregar arquivo...")
    st.stop()
else:
    df_bruto = resposta["df"]

if ignora_margem_ficticia:
    df_bruto = df_bruto[df_bruto["Margem (%)"] < 90].copy()

df_processado, alertas, resumo = calcular_metricas(df_bruto, fator_giro, fator_margem)

# Exibição de Métricas (Cards)
col1, col2, col3 = st.columns(3)
col1.metric("Faturamento Total", f"R$ {resumo['faturamento']:,.2f}")
col2.metric("CMV Total", f"R$ {resumo['cmv_total']:,.2f}")
col3.metric("Margem CMV", f"{resumo['margem']:.2f}%")

num_alertas = sum(not alertas[alerta].empty for alerta in alertas)

st.markdown("# :material/Flash_On: Central de Alertas")
st.markdown(f"### :red[{num_alertas}] Tipos de Alertas")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Margem Baixa + Estoque Alto",
        "Baixo Giro",
        "Margem Negativa",
        "Baixa Margem",
        "Estoque Negativo",
    ]
)

with tab1:
    if not alertas["alerta_margem"].empty:
        st.markdown(f"### :blue[{len(alertas['alerta_margem'])}] Margem e Giro Baixo")
        st.write(f"|- Margem abaixo do CMV: :blue[{resumo['margem']:.2f}%]")
        st.write(f"|- Giro de estoque em :blue[{fator_giro}%]")
        st.dataframe(
            alertas["alerta_margem"].style.format(FORMATACAO_ALERTAS),
            width="stretch",
            height="content",
        )
    else:
        st.success("Nenhum produto com estoque crítico e margem baixa.")

with tab2:
    if not alertas["alerta_giro"].empty:
        st.caption(diclamer_aba)
        st.markdown(f"### :blue[{len(alertas['alerta_giro'])}] Produtos com Baixo Giro")
        st.write(f"|- Giro de estoque em :blue[{fator_giro}%]")
        st.dataframe(
            alertas["alerta_giro"].style.format(FORMATACAO_ALERTAS),
            width="stretch",
            height="content",
        )
    else:
        st.success("Excelente! Nenhum produto com giro baixo.")

with tab3:
    if not alertas["alerta_prejuizo"].empty:
        st.markdown(
            f"### :blue[{len(alertas['alerta_prejuizo'])}] Produtos com Margem Negativa"
        )
        st.dataframe(
            alertas["alerta_prejuizo"].style.format(FORMATACAO_ALERTAS),
            width="stretch",
            height="content",
        )
    else:
        st.success("Excelente! Nenhum produto com margem negativa.")

with tab4:
    st.caption(diclamer_aba)
    if not alertas["alerta_magem_filtro"].empty:
        st.markdown(
            f"### :blue[{len(alertas['alerta_magem_filtro'])}] Produtos com Margem abaixo de :blue[{fator_margem:.2f} %]"
        )
        st.dataframe(
            alertas["alerta_magem_filtro"].style.format(FORMATACAO_ALERTAS),
            width="stretch",
            height="content",
        )
    else:
        st.success("Excelente! Nenhum produto com margem baixa.")

with tab5:
    if not alertas["alerta_negativo"].empty:
        st.markdown(
            f"### :blue[{len(alertas["alerta_negativo"])}] Produtos com Estoque Negativo"
        )
        st.dataframe(
            alertas["alerta_negativo"].style.format(FORMATACAO_ALERTAS),
            width="stretch",
            height="content",
        )
    else:
        st.success("Excelente! Nenhum produto com estoque negativo.")

st.divider()
st.markdown("# :material/Bar_Chart: Gráficos")

fig_TopMargem = CMV_fig_TOPMargem(df_processado)
fig_TopFaturamento = CMV_fig_TOPFaturamento(df_processado)
fig_teste = CMV_fig_Fin_Margem2(df_processado)
fig_teste2 = CMV_fig_Margem_Margem2(df_processado)

col1_graph, col2_graph = st.columns(2)
with col1_graph:
    st.plotly_chart(fig_TopMargem, width="stretch", height="content")
    st.plotly_chart(fig_teste2, width="stretch")

with col2_graph:
    st.plotly_chart(fig_TopFaturamento, width="stretch")
    st.plotly_chart(fig_teste, width="stretch")

# Exibição da Tabela
st.divider()
st.markdown("# Detalhamento de Produtos")
st.dataframe(df_processado, hide_index=True)

busca = st.text_input("Filtrar por nome do produto")
if busca:
    df_filtrado = df_processado[df_processado["Nome"].str.contains(busca, case=False)]
    st.write(df_filtrado)
