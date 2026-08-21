import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

st.set_page_config(page_title="Graficos Diretoria", layout="wide")
META_MENSAL = 5_000_000


#   LOGIN
# if "user" not in st.session_state:
#     st.session_state.user = None
#     st.session_state.session = None

# if (st.session_state.user == None) or (st.session_state.perfil['status']!='ativo') or (st.session_state.perfil['role'] not in ['administrador', 'usuario']):
#     st.markdown("## :material/Close: Area Restrita")
#     if st.button('Realizar login'):
#         st.switch_page('login.py')
#     st.stop()


def cria_df_consolidado(lista_arquivos):
    lista_df = []
    with st.spinner("Processando arquivos..."):
        for arquivo in lista_arquivos:
            try:
                df_temp = pd.read_excel(arquivo)
                df_temp["Arquivo Origem"] = arquivo.name
                lista_df.append(df_temp)
            except Exception as e:
                st.error(f"Erro ao ler {arquivo.name}: {e}")
                st.stop()

    df_final = pd.concat(lista_df, ignore_index=True)
    return df_final


def valida_empresas(df):
    """
    Valida as empresas e notas fiscais do DataFrame com base em três critérios:
    1. Mais de 2 empresas sendo avaliadas simultaneamente -> ERRO CRÍTICO (para a execução)
    2. Lojas/Empresas diferentes de 10 (010) ou 31 (031) -> ALERTA (exibe aviso e as linhas divergentes)
    3. Notas Fiscais com status pendente -> ALERTA/ERRO (exibe aviso, expander com as notas e filtra-as do DataFrame)

    Args:
        df (pd.DataFrame): DataFrame com os dados.

    Returns:
        pd.DataFrame: DataFrame filtrado (sem as notas fiscais pendentes).
    """

    # 1. Há mais de 2 empresas sendo avaliadas -> ERRO CRÍTICO
    num_empresas = df["Cód. Empresa"].nunique()
    if num_empresas > 1:
        st.error(
            f":material/Close: **ERRO CRÍTICO:** Mais de 2 empresas distintas identificadas nos arquivos "
            f"({num_empresas} encontradas: {list(df['Cód. Empresa'].unique())})."
        )
        st.stop()

    # 2. Valida se as lojas são diferentes de 10 (010) ou 31 (031) -> ALERTA
    df_loja_divergente = df[~df["Cód. Empresa"].isin([10, 31, "010", "031"])]
    if not df_loja_divergente.empty:
        st.warning(
            ":material/Warning: **ALERTA**: Transações com lojas diferentes de 010 e 031 encontradas."
        )
        st.dataframe(
            df_loja_divergente[
                [
                    "Status",
                    "Cód. Empresa",
                    "Referência",
                    "Emissão",
                    "Número",
                    "Operação (Tipo)",
                    "Cliente/Fornecedor",
                    "Total",
                    "Arquivo Origem",
                ]
            ]
        )
        st.divider()

    # 3. Status das NFe está como pendente
    nf_pendente = df[df["Status"] == "NF Pendente"]
    if not nf_pendente.empty:
        st.error(f":material/Close: [{len(nf_pendente)}] NFs Pendentes")
        df = df[df["Status"] != "NF Pendente"]
        with st.expander("Verificar NFs"):
            st.dataframe(
                nf_pendente[
                    [
                        "Status",
                        "Cód. Empresa",
                        "Referência",
                        "Emissão",
                        "Número",
                        "Operação (Tipo)",
                        "Cliente/Fornecedor",
                        "Total",
                        "Arquivo Origem",
                    ]
                ]
            )
        st.divider()

    return df["Cód. Empresa"].unique()


def trata_df(df):
    df["Total"] = df["Total"].astype(str).str.replace(".", "").str.replace(",", ".")
    df["Total"] = pd.to_numeric(df["Total"], errors="raise")
    df["Referência"] = pd.to_datetime(df["Referência"], dayfirst=True, errors="coerce")
    df["Emissão"] = pd.to_datetime(df["Emissão"], dayfirst=True, errors="coerce")

    df_compra = df[df["Operação (Tipo)"] == "Compra"]
    df_venda = df[df["Operação (Tipo)"] == "Venda"]
    df_venda = df_venda[df_venda["Status"].isin(["NFe", "NFCe"])]
    df_entrada = df[df["Operação (Tipo)"] == "Entrada"]
    df_saida = df[df["Operação (Tipo)"] == "Saída"]

    return df_compra, df_venda, df_entrada, df_saida, df


def calcular_dias_uteis(empresas, todos_os_dias, data_limite=None):
    empresa_codes = set()
    for e in empresas:
        try:
            val = int(float(e))
            empresa_codes.add(val)
        except (ValueError, TypeError):
            empresa_codes.add(str(e).strip())

    # Se empresa = 31, conta de domingo a sexta (exclui sábado: weekday != 5)
    # Se empresa = 10 (ou padrão), conta apenas dias de semana (segunda a sexta: weekday < 5)
    is_31 = 31 in empresa_codes or "31" in empresa_codes or "031" in empresa_codes

    if is_31:
        dias = [d for d in todos_os_dias if d.weekday() != 5]
    else:
        dias = [d for d in todos_os_dias if d.weekday() < 5]

    if data_limite is not None:
        dias = [d for d in dias if d <= data_limite]

    return len(dias)


def top10_clientes():
    # 5. Gráfico de Maiores Clientes (Top 10)
    st.subheader("🏆 Top 10 Clientes")
    top_clientes = (
        df_venda.groupby("Cliente/Fornecedor")["Total"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    fig_clientes = px.bar(
        top_clientes,
        x="Total",
        y="Cliente/Fornecedor",
        orientation="h",
        title="Ranking de Clientes por Volume de Compra",
        text_auto=".2s",
        color="Total",
        color_continuous_scale="Viridis",
    )
    fig_clientes.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_clientes, width="stretch")

    st.divider()


st.title(":material/Chart_Data: Relatório Faturamento")
with st.sidebar:

    st.markdown("# Arquivos Excel")
    pegar_manual = st.toggle(
        "Desejo pegar arquivos manualmente", value=True, disabled=True
    )
    st.caption(
        "Selecione os arquivos `.xls` ou `.xlsx` para unir as linhas em um único DataFrame."
    )

    arquivos_carregados = st.file_uploader(
        "Escolha os arquivos Excel",
        type=["xls", "xlsx"],
        accept_multiple_files=True,
        disabled=not (pegar_manual),
    )
    st.divider()

    st.markdown("## Meta")
    meta_input = st.number_input(
        "Digite o valor da meta (em Milhões de R$)",
        min_value=0.0,
        step=0.1,
        format="%0.2f",
    )
    if meta_input:
        META_MENSAL = meta_input * 1_000_000
        st.caption(
            f"Meta personalizada: `R$ {META_MENSAL:,.2f}`".replace(",", "x")
            .replace(".", ",")
            .replace("x", ".")
        )

    st.markdown("## Dias úteis")
    dias_uteis_input = st.number_input(
        "Digite o número de dias úteis", min_value=0, step=1, max_value=31, format="%d"
    )


if not pegar_manual:
    st.error("Em Desenvolimento - Aguarde...")
    st.stop()

if not arquivos_carregados:
    st.info("[aba lateral] Aguardando o upload de arquivos para iniciar...")
    st.divider()
    st.stop()

df = cria_df_consolidado(arquivos_carregados)

empresas = valida_empresas(df)
df_compra, df_venda, df_entrada, df_saida, df = trata_df(df)
with st.sidebar:

    st.markdown("## Periodo")
    anos = df_compra["Referência"].dt.year.unique()
    ano_selecionado = st.multiselect(
        "Selecione o Ano", options=sorted(anos), default=anos
    )
if not ano_selecionado:
    st.info("Selecione o ano que deseja filtrar")
    st.stop()

if False:

    df_compra = df_compra[df_compra["Referência"].dt.year.isin(ano_selecionado)]
    df_venda = df_venda[df_venda["Referência"].dt.year.isin(ano_selecionado)]

    df_compra = df_compra[df_compra["Status"].isin(["NFe", "NFCe"])]
    df_venda = df_venda[df_venda["Status"].isin(["NFe", "NFCe"])]

    total_vendas = df_venda["Total"].sum()
    ticket_medio_venda = df_venda["Total"].mean()
    qtd_clientes = df_venda["Cliente/Fornecedor"].nunique()

    total_compras = df_compra["Total"].sum()
    ticket_medio_compra = df_compra["Total"].mean()
    qtd_fornecedor = df_compra["Cliente/Fornecedor"].nunique()

st.markdown("# Compra/Venda")
periodo_compra_venda = (
    df_venda["Referência"].dt.to_period("M").unique().astype(str).tolist()
)
periodo_compra_venda_select = st.select_slider(
    "Selecione o Mês da Compra/Venda",
    options=periodo_compra_venda,
    value=periodo_compra_venda[-1],
)
periodo_compra_venda_select = pd.to_datetime(periodo_compra_venda_select)
compra_venda_mes = periodo_compra_venda_select.month
compra_venda_ano = periodo_compra_venda_select.year

df_compra_venda = df[
    (df["Referência"].dt.month == compra_venda_mes)
    & (df["Referência"].dt.year == compra_venda_ano)
]

df_compra_venda = df_compra_venda[df_compra_venda["Status"].isin(["NFe", "NFCe"])]
df_compra_venda = df_compra_venda.groupby("Operação (Tipo)")["Total"].sum()

c1, c2, c3 = st.columns(3)
c1.metric(
    "Compra/Venda",
    f"{df_compra_venda["Compra"]/df_compra_venda["Venda"]:,.2%}".replace(",", "X")
    .replace(".", ",")
    .replace("X", "."),
)
c2.metric(
    "Compra No Período",
    f"R$ {df_compra_venda["Compra"]:,.2f}".replace(",", "X")
    .replace(".", ",")
    .replace("X", "."),
)
c3.metric(
    "Vendas No Período",
    f"R$ {df_compra_venda["Venda"]:,.2f}".replace(",", "X")
    .replace(".", ",")
    .replace("X", "."),
)

if False:
    st.markdown("## Vendas")
    m1, m2, m3 = st.columns(3)
    m1.metric(
        "Venda Total",
        f"R$ {total_vendas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    )
    m2.metric(
        "Ticket Médio",
        f"R$ {ticket_medio_venda:,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", "."),
    )
    m3.metric("Clientes Atendidos", qtd_clientes)

    st.markdown("## Compras")
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Compra Total",
        f"R$ {total_compras:,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", "."),
    )
    col2.metric(
        "Ticket Médio",
        f"R$ {ticket_medio_compra:,.2f}".replace(",", "X")
        .replace(".", ",")
        .replace("X", "."),
    )
    col3.metric("Fornecedores", qtd_fornecedor)

st.markdown("# :material/Bar_Chart: Evolução de Vendas")
vendas_mensais = (
    df_venda.set_index("Referência").resample("ME")["Total"].sum().reset_index()
)
vendas_mensais["Mês/Ano"] = vendas_mensais["Referência"].dt.strftime("%m/%Y")

compras_mensais = (
    df_compra.set_index("Referência").resample("ME")["Total"].sum().reset_index()
)
compras_mensais["Mês/Ano"] = compras_mensais["Referência"].dt.strftime("%m/%Y")

fig_evolucao = px.area(
    vendas_mensais,
    x="Mês/Ano",
    y="Total",
    title="Faturamento por Mês",
    markers=True,
    labels={"Total": "Faturamento (R$)", "Mês/Ano": "Período"},
    text="Total",
)
fig_evolucao.update_traces(texttemplate="%{text:.2s}", textposition="top center")
fig_evolucao.add_hline(
    y=META_MENSAL,
    line_dash="dot",
    annotation_text="Meta",
    line_color="red",
    annotation_font_color="red",
)
fig_evolucao.update_xaxes(
    rangeslider_visible=True,
    rangeselector=dict(
        buttons=list(
            [
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1ano", step="year", stepmode="backward"),
                dict(step="all"),
            ]
        )
    ),
)
st.plotly_chart(fig_evolucao, width="stretch")
st.divider()


# top10_clientes()

# --- Configurações da Meta ---
st.markdown("## :material/Target: Indicador de Meta (KPI)")
periodos = df_venda["Referência"].dt.to_period("M").unique().astype(str).tolist()
periodo_selecionado = st.select_slider(
    "Selecione o Mês de Consulta",
    options=periodos,
    value=periodos[-1],  # Começa no mês mais recente
)
ultimo_mes = pd.to_datetime(periodo_selecionado)
mes_atual = ultimo_mes.month
ano_atual = ultimo_mes.year

# 2. Calcular Dias Úteis (Segunda a Sexta)
todos_os_dias = pd.date_range(
    start=f"{ano_atual}-{mes_atual}-01", end=(ultimo_mes + pd.offsets.MonthEnd(0))
)

if dias_uteis_input:
    dias_uteis_totais = dias_uteis_input
else:
    dias_uteis_totais = calcular_dias_uteis(empresas, todos_os_dias)
dias_passados = calcular_dias_uteis(
    empresas, todos_os_dias, data_limite=df_venda["Referência"].max()
)

df_venda_mes_atual = df_venda[
    (df_venda["Referência"].dt.month == mes_atual)
    & (df_venda["Referência"].dt.year == ano_atual)
]

faturamento_mes_atual = df_venda_mes_atual["Total"].sum()

percentual_meta = (faturamento_mes_atual / META_MENSAL) * 100
progresso_tempo = (dias_passados / dias_uteis_totais) * 100

if dias_passados == dias_uteis_totais:
    if percentual_meta >= progresso_tempo:
        status = "✔ Meta Batida"
    else:
        status = "❌ Meta Não foi Batida"
else:
    if percentual_meta >= progresso_tempo + 5:
        status = "Excelente"
    elif percentual_meta > progresso_tempo:
        status = "Bom"
    elif percentual_meta + 3 > progresso_tempo:
        status = "Regular"
    else:
        status = "Ruim"

# --- Visualização: Gráfico de Velocímetro (Gauge) ---
fig_kpi = go.Figure(
    go.Indicator(
        mode="gauge+number+delta",
        value=faturamento_mes_atual,
        domain={"x": [0, 1], "y": [0, 1]},
        title={
            "text": f"Faturamento vs Meta ({mes_atual}/{ano_atual})",
            "font": {"size": 24},
        },
        delta={
            "reference": META_MENSAL,
            "increasing": {"color": "green"},
            "valueformat": ".3s",
            # "valueformat": "R$,.2s",
        },
        gauge={
            "axis": {
                "range": [None, META_MENSAL * 1.2],
                "tickformat": ".3s",
                "dtick": META_MENSAL / 8,
            },
            "bar": {"color": "darkblue"},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "gray",
            "steps": [
                {"range": [0, META_MENSAL], "color": "#ffcfcf"},  # ffcfcf
                {"range": [META_MENSAL * 0.8, META_MENSAL], "color": "#fff3cf"},
                {"range": [META_MENSAL, META_MENSAL * 1.5], "color": "#d9ffcf"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": META_MENSAL,
            },
        },
    )
)


# Cálculos da Projeção
media_diaria = faturamento_mes_atual / dias_passados
projecao_final = media_diaria * dias_uteis_totais
percentual_projecao = (projecao_final / META_MENSAL) - 1


col_gauche, col_projecao = st.columns([2, 1])
with col_gauche:
    st.plotly_chart(fig_kpi, width="stretch")
with col_projecao:
    st.markdown("### Projeção")
    if (dias_uteis_totais - dias_passados) == 0:
        st.info("Projeção indisponível - Mes Finalizado")
    else:
        # Cartão de métrica nativo do Streamlit mostrando o destino final
        st.metric(
            label="Projeção para o Fim do Mês",
            value=f"R$ {projecao_final:,.2f}",
            delta=f"{percentual_projecao:.1%} da Meta",
            # delta_color="normal" if percentual_projecao >= 0 else "inverse",
        )

        # Texto de apoio rápido

        if projecao_final >= META_MENSAL:
            st.success("Mantendo o ritmo, a meta será atingida!")
        else:
            st.error("Atenção: O ritmo atual está abaixo da meta.")

# --- Explicação Detalhada do KPI ---
col_kpi1, colKpi22, col_kpi2, col_kpi3, col_kpi4 = st.columns(5)
col_kpi1.metric("Dias Úteis Decorridos", f"{dias_passados} de {dias_uteis_totais}")
colKpi22.metric("Dias Úteis Restantes", (dias_uteis_totais - dias_passados))
col_kpi2.metric("Meta Atingida", f"{percentual_meta:.1f}%")
col_kpi3.metric("Tempo Decorrido", f"{progresso_tempo:.1f}%")
col_kpi4.metric("Status da Meta", status)

if percentual_meta < progresso_tempo:
    st.error(
        f"Atenção: Você já percorreu {progresso_tempo:.1f}% dos dias úteis, mas atingiu apenas {percentual_meta:.1f}% da meta. Restam apenas {dias_uteis_totais-dias_passados} dias"
    )
elif percentual_meta < progresso_tempo + 5:
    st.info(
        f"Aviso: Ritmo de Vendas {percentual_meta:.1f}% superior ao tempo decorrido {progresso_tempo:.1f}% da meta. Ainda restam {dias_uteis_totais-dias_passados} dias"
    )
else:
    st.success(
        f"Excelente! O ritmo de vendas ({percentual_meta:.1f}%) está superior ao tempo decorrido ({progresso_tempo:.1f}%)."
    )

st.space()
st.header(":material/Calendar_Today: Análise de Faturamento Detalhado")

df_diario = (
    df_venda_mes_atual.set_index("Referência")["Total"]
    .resample("D")
    .sum()
    .reset_index()
)
df_diario["Semana"] = df_diario["Referência"].dt.strftime("%d/%m/%Y")

df_semanal = (
    df_venda_mes_atual.set_index("Referência")["Total"]
    .resample("W", label="left", closed="left")
    .sum()
    .reset_index()
)
df_semanal["Semana"] = df_semanal["Referência"].dt.strftime("%d/%m/%Y")

# Criando o gráfico de barras
fig_semana = px.bar(
    df_semanal,
    x="Semana",
    y="Total",
    title="Faturamento Semanal",
    text_auto=".2s",
    labels={"Total": "Faturamento (R$)", "Referência": "Data"},
    color_discrete_sequence=["#007bff"],  # Cor azul padrão
    color="Total",
    color_continuous_scale="Blues",
)
fig_semana.add_hline(
    y=META_MENSAL / (dias_uteis_totais / 5),
    line_dash="dot",
    annotation_text=f"Meta: {META_MENSAL/(dias_uteis_totais/5):,.2f}",
    annotation_font_color="red",
    line_color="red",
)

# Ajustes finos de layout
fig_semana.update_layout(template="plotly_white", hovermode="x unified")
st.plotly_chart(fig_semana, width="stretch")

# Criando o gráfico de barras
fig_dia = px.bar(
    df_diario,
    x="Semana",
    y="Total",
    title="Faturamento Diário",
    text_auto=".2s",
    labels={"Total": "Faturamento (R$)", "Referência": "Data"},
    color_discrete_sequence=["#007bff"],  # Cor azul padrão
    color="Total",
    color_continuous_scale="Blues",
)
fig_dia.add_hline(
    y=META_MENSAL / dias_uteis_totais,
    line_dash="dot",
    annotation_text=f"Meta: {META_MENSAL/dias_uteis_totais:,.2f}",
    annotation_position="top left",
    annotation_font_color="red",
    line_color="red",
)

# Ajustes finos de layout
fig_dia.update_layout(template="plotly_white", hovermode="x unified")
st.plotly_chart(fig_dia, width="stretch")

# else:
# st.info("Aguardando o upload de arquivos para iniciar...")
# st.divider()
