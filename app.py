import streamlit as st
st.set_page_config(page_title="Sistema Mumix", layout="wide")

pages = {
    "Home":[
        st.Page("Home.py",title="Home",icon=":material/home:"),
        st.Page("pages/8Conversor_Margem.py", title="margem x markup", icon=":material/swap_horizontal_circle:"),
    ],
    "Administrativo": [
        st.Page("pages/1Lanca_Pedido.py", title="Lança Pedidos",icon=":material/add_shopping_cart:"),
        st.Page("pages/4Pedidos.py", title="Pedidos Feitos", icon=":material/shopping_cart:"),
        st.Page("pages/5Calcula_NF.py", title="Calcula NFe", icon=":material/calculate:"),
        st.Page("pages/7Planilha_Dev.py", title="Planilha Devolução", icon=":material/assignment_return:")
    ],
    "Lista":[
        st.Page("pages/2Lista.py", title="Lista Lojas"),
        st.Page("pages/3Atacado.py", title="Lista Atacado")
    ],
    "Financeiro":[
        st.Page("pages/6Previa_Financeira.py", title="Previa Financeira", icon=":material/wallet:")
    ]
    #"MARGEM": st.Page("pages/8Conversor_Margem.py", title="Margem/Markup"),
}


# --- CONFIGURAÇÃO PAGINA ---
pg = st.navigation(pages,position="top")
pg.run()
