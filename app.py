import streamlit as st

# --- CONFIGURAÇÃO PAGINA ---
st.set_page_config(page_title="Sistema Mumix", layout="wide")

st.title(":material/Home: Página inicial")

st.title(":material/Badge: Painel de Controle")
st.write(f"Bem vindo! O que deseja fazer hoje?")

st.divider()

st.markdown("## Acessar páginas:")

#Coluna paginas
col1,col2, col3 = st.columns([2,2,1])
with col1:
    st.markdown("### :green[:material/Cloud_Done:] ATIVOS")

    if st.button("Acessar ERP"):
        st.switch_page("pages/Altera_ERP.py")
    if st.button("Lista"):
        st.switch_page("pages/Lista.py")
with col2:
    st.markdown("## :orange[:material/Upgrade:] Em Progresso")
    st.markdown("Organizados por ordem de prioridade")
    st.write(":orange-badge[:material/Lab_Profile: Previa Financeira]")
    st.write(":red-badge[:material/code: Divisão]")
    st.write(":red-badge[:material/code: Lojas/Carrinho]")
    st.write(":red-badge[:material/code: Lojas/MeusPedidos]")
with col3:
    st.markdown("## :material/Subtitles: Legenda")
    st.markdown(":green[:material/Grading:] Implementação")
    st.markdown(":orange[:material/Lab_Profile:] Etapa de teste")
    st.markdown(":red[:material/code:] Etapa de Codificação")

st.space()

st.divider()