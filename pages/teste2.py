import streamlit as st
import pandas as pd

st.set_page_config(page_title="Divisor de Pedidos Multi-SKU", layout="wide")

st.title("📦 Distribuição em Massa por SKU")

# 1. Simulação/Entrada das Tabelas
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Tabela de Filiais")
    df_filiais = pd.DataFrame({
        'filial': ['Filial A', 'Filial B', 'Filial C'],
        'fator_conversao': [50, 30, 20]
    })
    df_filiais = st.data_editor(df_filiais, key="filiais")
with col_b:
    st.subheader("Tabela de Pedidos (Multi-SKU)")
    df_pedidos = pd.DataFrame({
        'codigo': ['SKU-001', 'SKU-002', 'SKU-003'],
        'total_pedido': [1000, 500, 2500],
        'qt_cx': [10, 5, 50]
    })
    df_pedidos = st.data_editor(df_pedidos, key="pedidos")
# 2. Lógica de Processamento
if st.button("Calcular Divisão de Todos os Produtos"):
    # Criar todas as combinações possíveis de Pedido x Filial
    df_filiais['key'] = 1
    df_pedidos['key'] = 1
    df_final = pd.merge(df_pedidos, df_filiais, on='key').drop("key", axis=1)
    
    # Calcular soma dos fatores por SKU (caso mude dinamicamente)
    soma_fatores = df_filiais['fator_conversao'].sum()
    
    # Cálculo da Divisão
    # Proporção * Total / qt_cx (para achar numero de caixas) -> Arredonda -> Volta para unidades
    df_final['divisao_unidades'] = (
        ((df_final['fator_conversao'] / soma_fatores) * df_final['total_pedido']) / df_final['qt_cx']
    ).round() * df_final['qt_cx']
    
    # 3. Exibição dos Resultados
    st.success("Cálculo concluído!")
    
    # Visão detalhada
    st.subheader("Detalhamento por Item")
    st.dataframe(df_final[['codigo', 'filial', 'total_pedido', 'divisao_unidades']], use_container_width=True)
    
    # Visão Pivotada (Estilo Planilha de Conferência)
    st.subheader("Resumo para Logística (Matriz)")
    matriz = df_final.pivot_table(
        index='codigo', 
        columns='filial', 
        values='divisao_unidades', 
        aggfunc='sum'
    )
    st.dataframe(matriz, use_container_width=True)
    
    # Botão para Download
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button("Baixar Resultado em CSV", csv, "divisao_pedidos.csv", "text/csv")