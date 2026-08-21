import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# RELATORIO CMV


def CMV_fig_TOPFaturamento(df):
    """Gera um gráfico de barras com os 10 produtos que mais faturaram"""
    top_10 = df.nlargest(10, "Total Venda [R$]")
    fig = px.bar(
        top_10,
        x="Total Venda [R$]",
        y="Nome",
        orientation="h",
        title="Top 10 Maior Faturamento",
        labels={"Nome": "Produto"},
        color="Margem (%)",
        text="Total Venda [R$]",
        text_auto=".2f",
        color_discrete_sequence=["#007bff"],  # Cor azul padrão
        color_continuous_scale="Blues",
    )
    fig.update_traces(
        texttemplate="R$ %{text:.2s}",
        textposition="outside",  # Garante que o texto fique fora ou dentro da barra
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return fig


def CMV_fig_TOPMargem(df):
    # def CMV_gerar_grafico_Margem_ceilMargem(df):
    """Gera um gráfico de barras com os 10 produtos que mais faturaram"""
    top_10 = df.nlargest(10, "Margem (%)")
    fig = px.bar(
        top_10,
        x="Margem (%)",
        y="Nome",
        orientation="h",
        title="Top 10 Maiores Margens",
        labels={"Nome": "Produto"},
        color="Total Venda [R$]",
        text="Margem (%)",
        # text_auto=".2f",
        color_discrete_sequence=["#007bff"],  # Cor azul padrão
        color_continuous_scale="Blues",
    )
    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",  # Garante que o texto fique fora ou dentro da barra
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return fig


def CMV_fig_Margem_Margem2(df):
    # 1. Preparar os dados (Top 10)
    # Dica: Inverter a ordem para o maior ficar no topo do gráfico horizontal
    top_10 = df.nlargest(10, "Margem (%)").iloc[::-1]

    # 2. Criar a figura
    fig = go.Figure()

    # Adicionar Barras (Faturamento) - Agora Horizontal
    fig.add_trace(
        go.Bar(
            x=top_10["Total Venda [R$]"],  # Valor no X
            y=top_10["Nome"],  # Nome no Y
            name="Faturamento",
            text=top_10["Total Venda [R$]"],
            texttemplate="R$ %{text:.2s}",
            marker_color="royalblue",
            orientation="h",  # Orientação Horizontal
        )
    )

    # Adicionar Linha (Margem %) - Agora no Eixo X Superior
    fig.add_trace(
        go.Scatter(
            x=top_10["Margem (%)"],  # Valor no X
            y=top_10["Nome"],  # Nome no Y
            name="Margem (%)",
            xaxis="x2",  # Referência ao segundo eixo X
            mode="lines+markers",
            line=dict(color="firebrick", width=3),
        )
    )

    # Configurar o layout com dois eixos X (inferior e superior)
    fig.update_layout(
        title="Top 10 Margem vs Faturamento",
        yaxis=dict(title="Produtos"),
        xaxis=dict(title="Faturamento (R$)"),
        xaxis2=dict(
            title="Margem (%)",
            title_font_color="firebrick",
            tickfont_color="firebrick",
            overlaying="x",
            side="top",  # A linha de margem aparecerá com escala no topo
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="right", x=1),
        margin=dict(l=150),  # Espaço para os nomes dos produtos não cortarem
    )

    return fig


def CMV_fig_Margem_Margem(df):
    # 1. Preparar os dados (Top 10)
    top_10 = df.nlargest(10, "Margem (%)")

    # 2. Criar a figura
    fig = go.Figure()

    # Adicionar Barras (Faturamento)
    fig.add_trace(
        go.Bar(
            x=top_10["Nome"],
            y=top_10["Total Venda [R$]"],
            name="Faturamento",
            text=top_10["Total Venda [R$]"],
            texttemplate="R$ %{text:.2s}",
            marker_color="royalblue",
        )
    )

    # Adicionar Linha (Margem %)
    fig.add_trace(
        go.Scatter(
            x=top_10["Nome"],
            y=top_10["Margem (%)"],
            name="Margem (%)",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color="firebrick", width=3),
        )
    )

    # Configurar o layout com dois eixos Y
    fig.update_layout(
        title="Top 10 Margem vs Faturamento",
        xaxis=dict(title="Produtos"),
        yaxis=dict(title="Faturamento (R$)"),
        yaxis2=dict(title="Margem (%)", overlaying="y", side="right"),
        legend=dict(x=1.1, y=1),
    )
    return fig


def CMV_fig_Fin_Margem(df):
    # 1. Preparar os dados (Top 10)
    top_10 = df.nlargest(10, "Total Venda [R$]")

    # 2. Criar a figura
    fig = go.Figure()

    # Adicionar Barras (Faturamento)
    fig.add_trace(
        go.Bar(
            x=top_10["Nome"],
            y=top_10["Total Venda [R$]"],
            name="Faturamento",
            text=top_10["Total Venda [R$]"],
            texttemplate="R$ %{text:.2s}",
            marker_color="royalblue",
        )
    )

    # Adicionar Linha (Margem %)
    fig.add_trace(
        go.Scatter(
            x=top_10["Nome"],
            y=top_10["Margem (%)"],
            name="Margem (%)",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color="firebrick", width=3),
        )
    )

    # Configurar o layout com dois eixos Y
    fig.update_layout(
        title="Top 10 Faturamento vs Margem",
        xaxis=dict(title="Produtos"),
        yaxis=dict(title="Faturamento (R$)"),
        yaxis2=dict(title="Margem (%)", overlaying="y", side="right"),
        legend=dict(x=1.1, y=1),
    )
    return fig


def CMV_fig_Fin_Margem2(df):
    # 1. Preparar os dados (Top 10 por Faturamento)
    # Invertemos a ordem para que o maior valor apareça no topo do gráfico
    top_10 = df.nlargest(10, "Total Venda [R$]").iloc[::-1]

    # 2. Criar a figura
    fig = go.Figure()

    # Adicionar Barras (Faturamento) - Horizontal
    fig.add_trace(
        go.Bar(
            x=top_10["Total Venda [R$]"],  # Valores no eixo X
            y=top_10["Nome"],  # Nomes no eixo Y
            name="Faturamento",
            text=top_10["Total Venda [R$]"],
            texttemplate="R$ %{text:.2s}",
            marker_color="royalblue",
            orientation="h",  # Orientação Horizontal
        )
    )

    # Adicionar Linha (Margem %) - No segundo eixo X (topo)
    fig.add_trace(
        go.Scatter(
            x=top_10["Margem (%)"],  # Valores no eixo X
            y=top_10["Nome"],  # Nomes no eixo Y (mesma categoria das barras)
            name="Margem (%)",
            xaxis="x2",  # Vincula ao eixo X secundário
            mode="lines+markers",
            line=dict(color="firebrick", width=3),
        )
    )

    # Configurar o layout com eixos horizontais duplos
    fig.update_layout(
        title="Top 10 Faturamento vs Margem",
        yaxis=dict(
            title="Produtos",
            automargin=True,  # Garante que nomes longos não sejam cortados
        ),
        xaxis=dict(title="Faturamento (R$)", side="bottom"),
        xaxis2=dict(
            title="Margem (%)",
            overlaying="x",
            title_font_color="firebrick",
            tickfont_color="firebrick",
            side="top",  # Escala da margem aparece em cima
            showgrid=False,  # Remove o grid secundário para não poluir
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.15, xanchor="right", x=1),
        margin=dict(l=150),  # Espaço extra para os nomes dos produtos
    )

    return fig
