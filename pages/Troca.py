import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Política de Trocas - Fornecedores", layout="wide")

# 1. Simulação de Banco de Dados (CSV)
CSV_FILE = 'fornecedores_troca.csv'

def load_data():
    try:
        return pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        # Dados iniciais caso o arquivo não exista
        data = {
            'Fornecedor': ['TechMaster', 'ModaBrasil', 'GlobalGadgets'],
            'Status Troca': ['Sempre permite', 'Nunca permite', 'Avaliar caso a caso'],
            'Observação': ['Troca direta em 7 dias', 'Apenas defeito de fábrica', 'Enviar fotos para o SAC']
        }
        return pd.DataFrame(data)

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# Carregar dados
df = load_data()

st.title("📦 Gestão de Política de Trocas")
st.markdown("Consulte ou altere a política de troca dos nossos fornecedores parceiros.")

# --- SEÇÃO DE CONSULTA ---
st.header("🔍 Consulta Rápida")

# Filtros
col1, col2 = st.columns(2)
with col1:
    busca = st.text_input("Buscar fornecedor por nome")
with col2:
    filtro_status = st.multiselect("Filtrar por Status", options=df['Status Troca'].unique())

df_filtrado = df.copy()
if busca:
    df_filtrado = df_filtrado[df_filtrado['Fornecedor'].str.contains(busca, case=False)]
if filtro_status:
    df_filtrado = df_filtrado[df_filtrado['Status Troca'].isin(filtro_status)]

# Exibição visual (Cards)
cols = st.columns(3)
for index, row in df_filtrado.iterrows():
    with cols[index % 3]:
        cor = "green" if "Sempre" in row['Status Troca'] else "red" if "Nunca" in row['Status Troca'] else "orange"
        st.info(f"**{row['Fornecedor']}**\n\n**Status:** {row['Status Troca']}\n\n*Obs:* {row['Observação']}")


# --- SEÇÃO DE EDIÇÃO ---
st.header("📝 Atualizar Informações")

with st.expander("Clique aqui para editar a lista de fornecedores"):
    # Usando o Editor de Dados nativo do Streamlit
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    
    if st.button("Salvar Alterações"):
        save_data(edited_df)
        st.success("Informações atualizadas com sucesso!")
        st.rerun()