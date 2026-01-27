import streamlit as st
import pandas as pd
import numpy as np

# Configuração da página
st.set_page_config(page_title="Divisor de Pedidos", layout="wide")

st.title("📦 Distribuidor Proporcional de Pedidos")
st.markdown("Divida as quantidades dos pedidos entre filiais com base no fator de conversão.")

# --- SIDEBAR: Entrada de Dados ---
st.sidebar.header("Configurações")

# Simulando entrada de dados das Filiais
st.sidebar.subheader("1. Dados das Filiais")
data_filiais = {
    'filial': ['Filial A', 'Filial B', 'Filial C', 'Filial D'],
    'fator_conversao': [50, 30, 20, 10]
}
df_filiais = st.sidebar.data_editor(pd.DataFrame(data_filiais))

# Simulando entrada de dados do Pedido
st.sidebar.subheader("2. Dados do Pedido")
pedido_cod = st.sidebar.text_input("Código do Produto", "SKU-12345")
pedido_total = st.sidebar.number_input("Quantidade Total do Pedido", min_value=0, value=1000)
qt_por_cx = st.sidebar.number_input("Quantidade por Caixa (Múltiplo)", min_value=1, value=10)

# --- CÁLCULO ---
def calcular_divisao(df, total, multiplo):
    # Calcula a soma total dos fatores para criar a proporção
    soma_fatores = df['fator_conversao'].sum()
    
    # Aplica a regra de três
    df['qt_teorica'] = (df['fator_conversao'] / soma_fatores) * total
    
    # Ajusta para o múltiplo da caixa (arredondamento matemático)
    df['qt_sugerida_cx'] = (df['qt_teorica'] / multiplo).round() * multiplo
    
    return df

# --- EXECUÇÃO E DISPLAY ---
if st.button("Calcular Distribuição"):
    res = calcular_divisao(df_filiais.copy(), pedido_total, qt_por_cx)
    
    # Métricas de resumo
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Solicitado", pedido_total)
    col2.metric("Total Distribuído", int(res['qt_sugerida_cx'].sum()))
    col3.metric("Diferença (Sobra/Falta)", int(pedido_total - res['qt_sugerida_cx'].sum()))

    st.subheader("Tabela de Divisão")
    st.dataframe(res[['filial', 'fator_conversao', 'qt_teorica', 'qt_sugerida_cx']], 
                 use_container_width=True)
    
    # Gráfico para visualização rápida
    st.bar_chart(res.set_index('filial')['qt_sugerida_cx'])