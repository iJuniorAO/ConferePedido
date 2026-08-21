import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np


# Constants
REQUIRED_ROLES = ["administrador", "usuario"]
COMPANY_CODE = 10
PENDING_STATUS = ["NF Pendente"]
OPERATION_TYPES = ["Compra", "Venda", "Entrada", "Saída"]
VALID_STATUSES = ["NFe", "NFCe"]
mapeamento = {
    "MUMU ABILIO MACHADO LTDA": "ABILIO MACHADO",
    "Laticinios Lopes Temponi Ltda": "MUMIX BRIGADEIRO",
    "MUMIX CABANA": "CABANA",
    "MUMIX COMERCIAL PRISMA LTDA": "CABRAL",
    "GOMIDES DISTRIBUIDORA DE ALIMENTOS LTDA": "CAETE",
    "ZS LATICINIOS LTDA": "MUMIX CENTRO BETIM",
    "COMERCIO DE ALIMENTOS F & F LTDA": "MUMIX CEU AZUL",
    "M&E COMERCIO DE OPORTUNIDADES LTDA": "CONFISCO",
    "R&V MIX LTDA": "ELDORADO",
    "MUMU GOIANIA LTDA": "GOIANIA",
    "JOSEMAR AMARAL DA SILVEIRA": "IBIRITE",
    "LACERDA & REIS EMPREENDIMENTOS LTDA": "JARDIM ALTEROSA",
    "OLIVEIRA E SILVA LAGOA SANTA LTDA": "LAGOA SANTA",
    "JM LATICINIOS LTDA": "LAGUNA",
    "CM LATICINIOS LTDA": "LAGUNA",
    "RAV EMPREENDIMENTOS LTDA": "LARANJEIRAS",
    "G4 MIX LTDA": "MUMIX EXPRESS",
    "LATICINIOS MUMU LTDA": "MUMIX NOVA CONTAGEM LTDA",
    "MUMIX NOVO PROGRESSO LTDA": "NOVO PROGRESSO",
    "7X OPORTUNIDADES LTDA": "PALMITAL",
    "MUMIX PARA DE MINAS LTDA": "PARA DE MINAS",
    "MUMIX PEDRA AZUL LTDA": "MUMIX PEDRA AZUL",
    "MUMIX PINDORAMA LTDA": "PINDORAMA",
    "LATICINIOS LOPES TEMPONI LTDA": "RIBEIRÃO DAS NEVES",
    "ZANCHET LATICINIOS LTDA": "MUMU SANTA CRUZ",
    "LATICINIOS JB LTDA": "MUMU SANTA HELENA",
    "RS LATICINIOS LTDA": "SÃO LUIZ",
    "SERRANO PRODUTOS ALIMENTICIOS LTDA": "MUMU SERRANO",
    "LATICINIOS ALVES E SANTANA LTDA": "SILVA LOBO",
    "MUMU VENDA NOVA LTDA": "VENDA NOVA",
}

FINANCIAL_CONDITIONS = [
    lambda df: df["Operação (Tipo)"].str.contains("Compra", case=False, na=False),
    lambda df: df["Operação (Tipo)"].str.contains("Venda", case=False, na=False),
    lambda df: df["Operação (Nome)"].str.contains(
        "LOCAÇÃO|PRATELEIRA", case=False, na=False
    ),
    lambda df: df["Operação (Nome)"].str.contains(
        "SAIDA DE INVENTÁRIO", case=False, na=False
    ),
    lambda df: df["Operação (Nome)"].str.contains(
        "ENTRADA DE INVENTÁRIO", case=False, na=False
    ),
    lambda df: df["Operação (Nome)"].str.contains(
        "AVARIA QUEBRA GALPAO", case=False, na=False
    ),
    lambda df: df["Operação (Nome)"].str.contains(
        "PERDA|AVARIA|BAIXA DE ESTOQUE|SAIDA DE INVENTÁRIO", case=False, na=False
    ),
    lambda df: df["Operação (Nome)"].str.contains(
        "USO E CONSUMO", case=False, na=False
    ),
    lambda df: (
        (df["Operação (Tipo)"] == "Saída")
        & (
            df["Operação (Nome)"].str.contains(
                "DEVOLUÇÃO|DEVOLUCAO", case=False, na=False
            )
        )
    ),
    lambda df: (
        (df["Operação (Tipo)"] == "Entrada")
        & (
            df["Operação (Nome)"].str.contains(
                "DEVOLUÇÃO DE VENDA", case=False, na=False
            )
        )
    ),
    lambda df: (
        (df["Operação (Tipo)"] == "Saída")
        & (
            df["Operação (Nome)"].str.contains(
                "BONIFICAÇAO PARA CLIENTE", case=False, na=False
            )
        )
    ),
    lambda df: (
        (df["Operação (Tipo)"] == "Entrada")
        & (
            df["Operação (Nome)"].str.contains(
                "DOACAO|BONIFICACAO|BONIFICAÇÃO|ENTRADA DE INVENTÁRIO",
                case=False,
                na=False,
            )
        )
    ),
    lambda df: df["Operação (Nome)"].str.contains(
        "SAÍDA PARA DESPESA", case=False, na=False
    ),
]

FINANCIAL_CATEGORIES = [
    "Compra",
    "Venda",
    "Outros",  # locação/prateleira
    "Saída de Inventário",
    "Entrada de Inventário",
    "Retirada CD Samuel",  # avaria quebra galpão
    "Perda e Avaria",
    "Uso e Consumo",
    "Devolução Fornecedor",  # saida & devolução
    "Devolução Loja",  # entrada & devolução
    "Bonificação Loja",
    "Outras Entradas",
    "Retirada CD uso consumo",  # saída para despesa
]

COLUMNS_TO_DROP = [
    "Cliente/Fornecedor",
    "Cód. Empresa",
    "Emissão",
    "Espécie",
    "Eventos",
    "Serie-SubSerie",
    "Situação",
    "Cidade",
]
# Negative categories for balance
NEGATIVE_CATEGORIES = [
    "Bonificação Loja",
    "Compra",
    "Devolução Loja",
    "Perda e Avaria",
    "Uso e Consumo",
]
BALANCE_COLUMNS_TO_REMOVE = ["Outros", "Devolução Fornecedor"]

st.set_page_config(page_title="Graficos Diretoria", layout="wide")


def create_consolidated_dataframe(file_list):
    dataframes = []
    with st.spinner("Processando arquivos...", show_time=True):
        for file in file_list:
            try:
                df_temp = pd.read_excel(file)
                df_temp["Arquivo Origem"] = file.name
                dataframes.append(df_temp)
            except Exception as e:
                st.error(f"Erro ao ler {file.name}: {e}")
                st.stop()

    consolidated_df = pd.concat(dataframes, ignore_index=True)
    consolidated_df["Referência"] = pd.to_datetime(
        consolidated_df["Referência"], dayfirst=True, errors="coerce"
    )
    return consolidated_df


def alert_pending_nfs(df):
    """Handle pending NFs by filtering them out and showing a warning."""
    pending_nfs = df[df["Status"].isin(PENDING_STATUS)]

    if not pending_nfs.empty:
        st.divider()
        st.error(f":material/Close: [{len(pending_nfs)}] NFs Pendentes")
        with st.expander("Verificar NFs"):
            st.dataframe(pending_nfs)
        st.divider()
    return df


def process_dataframe(df):
    """Process the consolidated dataframe: validate, clean, and categorize."""

    def validate_company_code(df):
        """Validate that all records are for the correct company code."""
        df_wrong_company = df[df["Cód. Empresa"] != COMPANY_CODE]
        if not df_wrong_company.empty:
            st.divider()
            st.error(":material/Close: ERRO - Loja diferente da 010")
            st.dataframe(df_wrong_company)
            st.divider()
            st.stop()

    def convert_filial_names(df):
        df["Filial"] = df["Cliente/Fornecedor"].str.replace(".", "").str.strip()
        df["Filial"] = df["Filial"].replace(mapeamento)
        return df

    def convert_total_type(df):
        """Convert data types for specific columns."""
        # df["Número"] = pd.to_numeric(df["Número"], errors="raise")
        df["Total"] = df["Total"].astype(str).str.replace(".", "").str.replace(",", ".")
        df["Total"] = pd.to_numeric(df["Total"], errors="raise")
        return df

    def add_date_columns(df):
        """Add month and year columns for analysis."""
        df["MesAno"] = df["Referência"].dt.to_period("M").dt.to_timestamp()
        df["Mes_Ref"] = df["Referência"].dt.month
        df["Ano_Ref"] = df["Referência"].dt.year
        df["Mes_Ano"] = df["Referência"].dt.strftime("%y/%b").str.upper()
        return df

    def categorize_financial_operations(df):
        conditions = [cond(df) for cond in FINANCIAL_CONDITIONS]
        df["CategoriaFinanceira"] = np.select(
            conditions, FINANCIAL_CATEGORIES, default="Outros"
        )
        return df

    def filter_dataframes(df):
        """Filter the dataframe into operation-specific dataframes."""
        df_purchase = df[df["Operação (Tipo)"] == "Compra"]
        df_sale = df[df["Operação (Tipo)"] == "Venda"]
        df_sale = df_sale[df_sale["Status"].isin(VALID_STATUSES)]
        df_entry = df[df["Operação (Tipo)"] == "Entrada"]
        df_exit = df[df["Operação (Tipo)"] == "Saída"]
        return df_purchase, df_sale, df_entry, df_exit

    validate_company_code(df)
    df = convert_filial_names(df)
    df = df.drop(columns=COLUMNS_TO_DROP)
    df = convert_total_type(df)
    df = add_date_columns(df)
    df = categorize_financial_operations(df)
    df_filter = df[df["Status"].isin(status_selecionados)]
    return filter_dataframes(df_filter) + (df, df_filter)


def criar_balanco_devolucao(df):
    grouped_df = df.pivot_table(
        index="Referência", columns="CategoriaFinanceira", values="Total", aggfunc="sum"
    )

    grouped_df = grouped_df[["Devolução Fornecedor", "Devolução Loja"]]
    grouped_df["Devolução Loja"] = -grouped_df["Devolução Loja"]
    grouped_df["Balanço"] = grouped_df.sum(axis=1)

    df_export = df[
        df["CategoriaFinanceira"].isin(["Devolução Fornecedor", "Devolução Loja"])
    ]

    plot_df = grouped_df.reset_index()

    fig = go.Figure()

    colors = ["#1f77b4" if x >= 0 else "#d62728" for x in plot_df["Balanço"]]

    fig.add_trace(
        go.Bar(
            x=plot_df["Referência"],
            y=plot_df["Balanço"],
            text=plot_df["Balanço"],
            texttemplate="%{y:.2s}",
            textposition="outside",
            marker_color=colors,
            hovertemplate="<b>Mes/Ano:</b> %{x}<br><b>Balanço:</b> R$ %{y:,.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        title="**Balanço Devolução",
        xaxis_title="Mês/Ano",
        yaxis_title="Valor (R$)",
        template="plotly_white",
        showlegend=False,
        xaxis=dict(
            tickformat="%m/%Y",
            dtick="M1",
        ),
    )
    fig.update_xaxes(
        # rangeslider_visible=True,
        rangeselector=dict(
            buttons=[
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1ano", step="year", stepmode="backward"),
                dict(step="all"),
            ]
        )
    )

    grouped_df = grouped_df.sort_index(ascending=False)
    grouped_df.index = grouped_df.index.strftime("%m/%Y")
    return fig, grouped_df


def create_revenue_chart(df):
    """Create a revenue evolution chart."""
    revenue_df = df[df["CategoriaFinanceira"] == "Venda"]
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=revenue_df["Referência"],
            y=revenue_df["Total"],
            text=revenue_df["Total"],
            mode="lines+markers+text",
            texttemplate="%{text:.2s}",
            textposition="top center",
            fill="tozeroy",
            hovertemplate="<b>Mes/Ano:</b> %{x}<br><b>Faturamento:</b> R$ %{y:,.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        title="Faturamento x Mes/Ano",
        xaxis_title="Referência",
        yaxis_title="Valor (R$)",
        template="plotly_white",
        showlegend=False,
        xaxis=dict(
            tickformat="%m/%Y",
            dtick="M1",
        ),
    )
    fig.update_xaxes(
        rangeselector=dict(
            buttons=[
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1ano", step="year", stepmode="backward"),
                dict(step="all"),
            ]
        )
    )
    return fig, revenue_df


def create_losses_chart(df, df_completo):
    colunas_remover = NEGATIVE_CATEGORIES
    colunas_remover.remove("Compra")
    colunas_remover.append("Retirada CD uso consumo")
    colunas_remover.append("Retirada CD Samuel")

    def verDetalhe(df_temp, colunas_remover):
        df_detalhe = df_temp[
            [
                "Filial",
                "Referência",
                "CategoriaFinanceira",
                "Operação (Nome)",
                "Total",
            ]
        ]

        df_detalhe = (
            df_detalhe.groupby(["Referência", "CategoriaFinanceira", "Filial"])["Total"]
            .sum()
            .reset_index()
        )
        df_detalhe = df_detalhe[df_detalhe["CategoriaFinanceira"].isin(colunas_remover)]
        df_detalhe = df_detalhe.set_index("Referência")
        df_detalhe = df_detalhe.sort_index(ascending=False)

        df_detalhe.index = df_detalhe.index.strftime("%m/%Y")

        return df_detalhe

    losses_data = df[df["CategoriaFinanceira"].isin(colunas_remover)]

    # Create a trace for each category
    colors = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3"]

    fig = go.Figure()
    for i, category in enumerate(losses_data["CategoriaFinanceira"].unique()):
        filtered_df = losses_data[losses_data["CategoriaFinanceira"] == category]
        color = colors[i]

        fig.add_trace(
            go.Scatter(
                x=filtered_df["Referência"],
                y=filtered_df["Total"],
                name=category,
                mode="lines+markers+text",
                line=dict(color=color),
                text=filtered_df["Total"],
                texttemplate="%{text:.2s}",
                textposition="top center",
                textfont=dict(color=color),
            )
        )
    fig.update_layout(
        title="Evolução Temporal Perdas por Categoria",
        xaxis_title="Data de Referência",
        yaxis_title="Prejuízo (R$)",
        template="plotly_white",
        hovermode="x unified",
        legend_title="Categorias",
        xaxis=dict(
            tickformat="%m/%Y",
            dtick="M1",
        ),
    )
    fig.update_xaxes(
        rangeselector=dict(
            buttons=[
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1ano", step="year", stepmode="backward"),
                dict(step="all"),
            ]
        )
    )

    losses_sum = losses_data.groupby("Referência")["Total"].sum().to_frame()
    losses_sum = losses_sum.sort_index(ascending=False)
    losses_sum.index = losses_sum.index.strftime("%m/%Y")

    losses_data = losses_data.set_index("Referência")
    losses_data = losses_data.sort_index(ascending=False)
    losses_data.index = losses_data.index.strftime("%m/%Y")

    df_detalhado = verDetalhe(df_completo, colunas_remover)

    return fig, losses_data, losses_sum, df_detalhado


def create_montly_sales_return(df):
    df_filtered = df[df["CategoriaFinanceira"].isin(["Venda", "Devolução Loja"])]
    df_group = (
        df_filtered.groupby(["Referência", "CategoriaFinanceira"])["Total"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )

    # Calculate %: (Returns / Sales) * 100
    df_group["% Retorno"] = (
        (df_group["Devolução Loja"] / df_group["Venda"] * 100)
        .replace([float("inf"), -float("inf")], 0)
        .fillna(0)
    )

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Bar Chart for % Return (Primary Axis)
    fig.add_trace(
        go.Bar(
            x=df_group["Referência"],
            y=df_group["% Retorno"],
            text=df_group["% Retorno"],
            texttemplate="%{y:.2f} %",
            textposition="outside",
            name="% Taxa de Retorno",
            marker_color="crimson",
            hovertemplate="Cliente: %{x}<br>% Retorno: %{y:.2f}%<extra></extra>",
        ),
        secondary_y=False,
    )
    # 2. Line Chart for Sales Volume (Secondary Axis)
    # This helps identify if a high % is a small client or a big one
    fig.add_trace(
        go.Scatter(
            x=df_group["Referência"],
            y=df_group["Venda"],
            text=df_group["Venda"],
            name="Volume de Vendas (R$)",
            mode="lines+markers+text",
            textposition="top center",
            texttemplate="%{y:.2s}",
            marker_color="royalblue",
        ),
        secondary_y=True,
    )
    # Formatting
    fig.update_layout(
        title="Relação Faturamento x Devolução",
        xaxis_title="Período",
        xaxis=dict(
            tickformat="%m/%Y",
            dtick="M1",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=600,
    )

    fig.update_yaxes(
        title_text="<b>%</b> Taxa de Retorno", secondary_y=False, ticksuffix="%"
    )
    fig.update_yaxes(title_text="<b>R$</b> Volume de Vendas", secondary_y=True)

    return fig


def create_montly_stores_sales_return(df):
    df_filtered = df[df["CategoriaFinanceira"].isin(["Venda", "Devolução Loja"])]

    df_group = (
        df_filtered.groupby(["Referência", "Filial", "CategoriaFinanceira"])["Total"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )

    # Filter only clients with returns
    df_group = df_group[df_group["Devolução Loja"] > 0].copy()

    # Calculate %: (Returns / Sales) * 100
    df_group["% Retorno"] = (
        (df_group["Devolução Loja"] / df_group["Venda"] * 100)
        .replace([float("inf"), -float("inf")], 0)
        .fillna(0)
    )

    df_group = df_group.sort_values(by="% Retorno", ascending=False)

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Bar Chart for % Return (Primary Axis)
    fig.add_trace(
        go.Bar(
            x=df_group["Filial"],
            y=df_group["% Retorno"],
            text=df_group["% Retorno"],
            texttemplate="%{y:.2f} %",
            textposition="outside",
            name="% Taxa de Retorno",
            marker_color="crimson",
            hovertemplate="Cliente: %{x}<br>% Retorno: %{y:.2f}%<extra></extra>",
        ),
        secondary_y=False,
    )

    # 2. Line Chart for Sales Volume (Secondary Axis)
    # This helps identify if a high % is a small client or a big one
    fig.add_trace(
        go.Scatter(
            x=df_group["Filial"],
            y=df_group["Venda"],
            text=df_group["Venda"],
            name="Volume de Vendas (R$)",
            mode="lines+markers+text",
            texttemplate="%{y:.2s}",
            marker_color="royalblue",
        ),
        secondary_y=True,
    )

    # Formatting
    fig.update_layout(
        title="Rank de Devoluções por Cliente (Prioridade de Ação)",
        xaxis_title="Clientes (Ordenados por % de Devolução)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=600,
    )

    fig.update_yaxes(
        title_text="<b>%</b> Taxa de Retorno", secondary_y=False, ticksuffix="%"
    )
    fig.update_yaxes(title_text="<b>R$</b> Volume de Vendas", secondary_y=True)

    df_group = df_group.set_index("Filial")
    df_group = df_group.drop(columns="Referência")

    return df_group, fig


def create_inventory_trend_chart(df_clean, chart_format="Linha", selected_years=None):
    """
    Creates a comparison chart of inventory total values per month, colored by year.
    """

    df_filtered = df_clean[df_clean["Ano_Ref"].isin(selected_years)]

    # Group by Year and Month, summing Total
    df_grouped = (
        df_filtered.groupby(["Ano_Ref", "Mes_Ref"])["Total"].sum().reset_index()
    )

    fig = go.Figure()
    MONTHS_PT = [
        "Jan",
        "Fev",
        "Mar",
        "Abr",
        "Mai",
        "Jun",
        "Jul",
        "Ago",
        "Set",
        "Out",
        "Nov",
        "Dez",
    ]

    for year in sorted(df_grouped["Ano_Ref"].unique()):
        df_year = df_grouped[df_grouped["Ano_Ref"] == year].sort_values("Mes_Ref")

        # Align all months 1-12 to make the comparison clean (fill missing with 0)
        df_year = (
            df_year.set_index("Mes_Ref")
            .reindex(range(1, 13), fill_value=0)
            .reset_index()
        )

        x_vals = df_year["Mes_Ref"]
        y_vals = df_year["Total"]
        year_str = str(int(year))

        if chart_format == "Barra":
            fig.add_trace(
                go.Bar(
                    x=x_vals,
                    y=y_vals,
                    name=year_str,
                    text=y_vals,
                    texttemplate="%{text:.2s}",
                    textposition="outside",
                    hovertemplate="<b>Ano:</b> "
                    + year_str
                    + "<br><b>Mês:</b> %{x}<br><b>Total:</b> R$ %{y:,.2f}<extra></extra>",
                )
            )
        elif chart_format == "Área":
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    name=year_str,
                    mode="lines+markers+text",
                    text=y_vals,
                    texttemplate="%{text:.2s}",
                    textposition="top center",
                    fill="tozeroy",
                    hovertemplate="<b>Ano:</b> "
                    + year_str
                    + "<br><b>Mês:</b> %{x}<br><b>Total:</b> R$ %{y:,.2f}<extra></extra>",
                )
            )
        else:  # Linha
            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    name=year_str,
                    mode="lines+markers+text",
                    text=y_vals,
                    texttemplate="%{text:.2s}",
                    textposition="top center",
                    hovertemplate="<b>Ano:</b> "
                    + year_str
                    + "<br><b>Mês:</b> %{x}<br><b>Total:</b> R$ %{y:,.2f}<extra></extra>",
                )
            )

    fig.update_layout(
        title="Evolução do Inventário por Mês",
        xaxis_title="Mês",
        yaxis_title="Valor Total (R$)",
        template="plotly_white",
        xaxis=dict(
            tickmode="array", tickvals=list(range(1, 13)), ticktext=MONTHS_PT, dtick=1
        ),
        hovermode="x unified",
        barmode="group" if chart_format == "Barra" else None,
    )

    return fig


st.markdown("# :material/Chart_Data: Apresentação de Resultados")
with st.sidebar:
    st.markdown("## Arquivos Excel")
    pegar_manual = st.toggle(
        "Desejo pegar arquivos manualmente", value=True, disabled=True
    )
    st.markdown(
        "Selecione os arquivos `.xls` ou `.xlsx` para unir as linhas em um único DataFrame."
    )
    arquivos_carregados = st.file_uploader(
        "Escolha os arquivos Excel",
        type=["xls", "xlsx"],
        accept_multiple_files=True,
        disabled=not (pegar_manual),
    )

if not arquivos_carregados:
    st.info("Aguardando o upload de arquivos para iniciar...")
    st.stop()

df = create_consolidated_dataframe(arquivos_carregados)
alert_pending_nfs(df)

st.markdown("# Filtro:")

opcoes_status = df["Status"].unique().tolist()
status_selecionados = st.segmented_control(
    "Selecione os Status para análise:",
    selection_mode="multi",
    options=opcoes_status,
    default=["NFe"],
)
st.divider()

df_compra, df_venda, df_entrada, df_saida, df_original, df = process_dataframe(df)

df["Referência"] = df["Referência"].dt.to_period("M").dt.to_timestamp()
df_grouped = (
    df.groupby(["Referência", "CategoriaFinanceira"])["Total"].sum().reset_index()
)

st.markdown("## Faturamento")
fig_Faturamento, df_Faturamento = create_revenue_chart(df_grouped)
st.plotly_chart(fig_Faturamento, width="stretch")
with st.expander(":material/Settings: Detalhes dados"):
    st.dataframe(df)

if False:
    st.divider()
    st.markdown("### Evolução Balanço Financeiro")

    columns_to_remove = BALANCE_COLUMNS_TO_REMOVE
    fig_Balanco_Financeiro, df_EvolucaoFinanceiro = create_financial_balance_evolution(
        df_grouped, columns_to_remove
    )

    st.plotly_chart(fig_Balanco_Financeiro, width="stretch")
    with st.expander(":material/Settings: Detalhes Financeiros"):
        st.markdown(f"### {len(columns_to_remove)} Colunas Ignoradas:")
        for col in columns_to_remove:
            st.write(col)
        st.markdown("### Gráfico em Tabela:")
        st.dataframe(
            df_EvolucaoFinanceiro.style.map(
                lambda x: "color: red;" if x < 0 else None
            ).format(
                lambda x: (
                    f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                )
            ),
            width="stretch",
        )

st.space()
st.divider()

st.markdown("## Erro de Inventário")
df_inventario = df_original[
    df_original["Operação (Nome)"].str.contains("INVENT", case=False, na=False)
]

if not df_inventario.empty:
    anos_disponiveis = sorted(
        df_inventario["Ano_Ref"].dropna().unique().astype(int).tolist()
    )

    if anos_disponiveis:
        col_format, col_years = st.columns([1, 2])
        with col_format:
            tipo_grafico = st.segmented_control(
                "Formato do Gráfico",
                options=["Linha", "Barra", "Área"],
                default="Linha",
                key="tipo_grafico_inventario",
            )
        with col_years:
            anos_selecionados = st.segmented_control(
                "Selecione os Anos para o Gráfico",
                options=anos_disponiveis,
                default=anos_disponiveis,
                selection_mode="multi",
                key="anos_selecionados_inventario",
            )

        if not anos_selecionados:
            st.error("Selecione pelo menos um ano para visualizar o gráfico.")
        else:
            fig_inventario = create_inventory_trend_chart(
                df_inventario,
                chart_format=tipo_grafico,
                selected_years=anos_selecionados,
            )
            st.plotly_chart(fig_inventario, width="stretch")
    else:
        st.info("Nenhum dado de ano disponível para o gráfico de inventário.")
else:
    st.info("Nenhum dado de inventário disponível.")

st.divider()


st.markdown("## Saídas")
fig_losses, df_losses, df_losses_sum, df_losses_detail = create_losses_chart(
    df_grouped, df
)

st.plotly_chart(fig_losses, width="stretch")

with st.expander(":material/Settings: Detalhes Perdas"):
    col_loss_a, col_loss_b = st.columns(2)
    with col_loss_a:
        st.write("Valores Totais")
        st.dataframe(
            df_losses_sum.style.format(
                {
                    "Total": "R$ {:.,2f}".replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                }
            )
        )
    with col_loss_b:
        st.write("Tabela Gráfico")
        st.dataframe(
            df_losses.style.format(
                {
                    "Total": "R$ {:.,2f}".replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                }
            )
        )
    st.write("Tabela Mais Detalhada")
    losses_options = st.segmented_control(
        "Selecione qual categoria deseja filtrar",
        options=df_losses_detail["CategoriaFinanceira"].unique(),
        selection_mode="multi",
        default=df_losses_detail["CategoriaFinanceira"].unique(),
    )
    df_losses_detail = df_losses_detail[
        df_losses_detail["CategoriaFinanceira"].isin(losses_options)
    ]
    if df_losses_detail.empty:
        st.info("Nenhuma Opção Escolhida")
    else:
        st.dataframe(
            df_losses_detail.style.format(
                {
                    "Total": "R$ {:.,2f}".replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                }
            )
        )


def create_sales_return_gauge(df):
    # 2. Filter for the last 12 months from the most recent date in the dataset
    last_date = df["Referência"].max()
    start_date = last_date - pd.DateOffset(months=12)
    df_last_12 = df[df["Referência"] > start_date].copy()

    # 4. Filter categories and group
    df_filtered = df_last_12[
        df_last_12["CategoriaFinanceira"].isin(["Venda", "Devolução Loja"])
    ]

    # Pivot to get Sales and Returns as columns per month
    df_monthly = (
        df_filtered.groupby(["Referência", "CategoriaFinanceira"])["Total"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )

    # 5. Calculate monthly percentage
    df_monthly["% Retorno"] = (
        df_monthly["Devolução Loja"] / df_monthly["Venda"] * 100
    ).fillna(0)

    # Sort chronologically
    df_monthly = df_monthly.sort_values("Referência")

    latest_data = df_monthly.iloc[-1]  # Get the most recent month
    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=latest_data["% Retorno"],
            number={"valueformat": ".3", "suffix": "%"},
            title={
                "text": f"Taxa de Devolução - {latest_data['Referência'].strftime('%m/%Y')}"
            },
            gauge={
                "axis": {
                    "range": [0, 1],
                    "tickmode": "array",
                    "tickvals": [x / 10 for x in range(0, 21)],
                    "tickformat": ".3f",
                    "ticksuffix": "%",
                },
                "steps": [
                    {"range": [0, 0.25], "color": "lightgreen"},
                    {"range": [0.25, 0.75], "color": "yellow"},
                    {"range": [0.75, 1], "color": "red"},
                ],
                "threshold": {"line": {"color": "black", "width": 4}, "value": 0.75},
            },
        )
    )
    return fig_gauge


st.divider()
st.markdown("## Devoluções")

fig_sales_return = create_montly_sales_return(df)
st.plotly_chart(fig_sales_return, width="stretch")

# fig_gauche_sales_gauge = create_sales_return_gauge(df_grouped)

# st.markdown("### Taxa Devolução Média")
# st.plotly_chart(fig_gauche_sales_gauge, width="stretch")
st.divider()
st.markdown("## Análise por Loja")
meses = df[["Referência"]].copy()
meses = df["Referência"].unique().strftime("%m/%Y")
mes_selecionado = st.segmented_control(
    "Selecione o Mês", options=meses, default=meses[0]
)

if not mes_selecionado:
    st.info("Nenhum Período Selecionado")
else:
    df_store_sales_return, fig_store_sales_return = create_montly_stores_sales_return(
        df[df["Referência"] == mes_selecionado]
    )

    st.plotly_chart(fig_store_sales_return, width="stretch")

    # Display "Top Offenders" table
    st.markdown("### Top 5 Clientes com Maior Índice de Devolução")
    st.table(
        # df_store_sales_return.style.format(
        df_store_sales_return.head(5).style.format(
            {
                "Venda": "R$ {:.,2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", "."),
                "Devolução Loja": "R$ {:.,2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", "."),
                "% Retorno": "{:.,2f} %".replace(",", "X")
                .replace(".", ",")
                .replace("X", "."),
            }
        )
    )
st.divider()
if False:
    st.markdown("### Balanço Devolução")
    st.caption("Os valores de devolução de Entrada são os as devoluções das lojas")
    st.caption("Os valores de devolução de Saída são: ")
    st.caption("-Recebimento: NFs de Compra que foi emitido devolução")
    st.caption("-Devolução: Produtos Avariados que teremos reposição")
    fig_balanco_dev, df_balanco_dev = criar_balanco_devolucao(df_grouped)
    st.plotly_chart(fig_balanco_dev, width="stretch")
    with st.expander(":material/Settings: Detalhes Balanço Devolução"):
        st.dataframe(
            df_balanco_dev.style.format(
                lambda x: (
                    f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                )
            )
        )
