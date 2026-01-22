import streamlit as st

# --- CONFIGURAÇÃO PAGINA ---

st.set_page_config(page_title="Sistema Mumix", layout="wide", initial_sidebar_state="collapsed")

if st.query_params.get("debugger") == "true":
    st.session_state.debugger=True
    st.error(":material/Terminal: APP EM TESTE")

st.title(":material/Home: Página inicial")

st.title(":material/Badge: Painel de Controle")
st.write(f"Bem vindo! O que deseja fazer hoje?")

st.divider()

st.markdown("## Acessar páginas:")

#Coluna paginas
col1,col2, col3 = st.columns([2,2,1])
with col1:
    st.markdown("### :green[:material/Cloud_Done:] ATIVOS")

    if st.button("Altera ERP"):
        st.switch_page("pages/1Altera_ERP.py")
    if st.button("Lista"):
        st.switch_page("pages/2Lista.py")
    if st.button("Pedidos"):
        st.switch_page("pages/3Pedidos.py")
    if st.button("Previa Financeira"):
        st.switch_page("pages/4Previa_Financeira.py")
with col2:
    st.markdown("## :orange[:material/Upgrade:] Em Progresso")
    st.write(":orange-badge[:material/Lab_Profile: Previa Financeira]")
    st.write(":orange-badge[:material/Lab_Profile: Pedido]")

    st.write(":red-badge[:material/code: Atacado]")
    st.write(":red-badge[:material/code: Troca]")
    st.write(":red-badge[:material/code: Divisão]")
    st.write(":red-badge[:material/code: Login]")
    st.write(":red-badge[:material/code: Lojas/Carrinho]")
    st.write(":red-badge[:material/code: Lojas/MeusPedidos]")
with col3:
    st.markdown("## :material/Subtitles: Legenda")
    st.markdown(":green[:material/Grading:] Implementação")
    st.markdown(":orange[:material/Lab_Profile:] Etapa de teste")
    st.markdown(":red[:material/code:] Etapa de Codificação")

st.space()

st.divider()