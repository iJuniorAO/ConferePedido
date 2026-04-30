import streamlit as st
st.set_page_config(page_title="Sistema Mumix", layout="wide")


login_page = st.Page("login.py",title="Login",icon=":material/login:")
home_page = st.Page("Home.py",title="Home",icon=":material/home:")
margem_page = st.Page("pages/8Conversor_Margem.py", title="margem x markup", icon=":material/swap_horizontal_circle:")

fazer_pedido_page = st.Page("pages/Fazer_Pedido.py", title="Fazer Pedidos", icon=":material/universal_currency_alt:")
lanca_pedido_page = st.Page("pages/1Lanca_Pedido.py", title="Lança Pedidos",icon=":material/add_shopping_cart:")
divisao_page = st.Page("pages/divisao.py", title="Divisão",icon=":material/prompt_suggestion:")

pedidos_page = st.Page("pages/4Pedidos.py", title="Pedidos Feitos", icon=":material/shopping_cart:")
calcula_nf_page = st.Page("pages/5Calcula_NF.py", title="Calcula NFe", icon=":material/calculate:")
plan_dev_page = st.Page("pages/7Planilha_Dev.py", title="Planilha Devolução", icon=":material/assignment_return:")


lista_loja_page = st.Page("pages/2Lista.py", title="Lista Lojas", icon=":material/shelves:")
lista_atacado_page = st.Page("pages/3Atacado.py", title="Lista Atacado", icon=":material/local_mall:")

previa_financeira_page = st.Page("pages/6Previa_Financeira.py", title="Previa Financeira", icon=":material/wallet:")

pages = {
    'Home': [
        login_page,home_page,margem_page
    ],
    'Administrativo': [
        fazer_pedido_page,lanca_pedido_page,divisao_page,pedidos_page,calcula_nf_page,plan_dev_page
    ],
    'Lista': [
        lista_loja_page,lista_atacado_page
    ],
    'Financeiro': [
        previa_financeira_page
    ]
}


# pages = {
#     "Home":[
#         st.Page("login.py",title="Login",icon=":material/login:"),
#         st.Page("Home.py",title="Home",icon=":material/home:"),
#         st.Page("pages/8Conversor_Margem.py", title="margem x markup", icon=":material/swap_horizontal_circle:"),
#     ],
#     "Administrativo": [
#         st.Page("pages/Fazer_Pedido.py", title="Fazer Pedidos", icon=":material/universal_currency_alt:"),
#         st.Page("pages/1Lanca_Pedido.py", title="Lança Pedidos",icon=":material/add_shopping_cart:"),
#         st.Page("pages/4Pedidos.py", title="Pedidos Feitos", icon=":material/shopping_cart:"),
#         st.Page("pages/5Calcula_NF.py", title="Calcula NFe", icon=":material/calculate:"),
#         st.Page("pages/7Planilha_Dev.py", title="Planilha Devolução", icon=":material/assignment_return:")
#     ],
#     "Lista":[
#         st.Page("pages/2Lista.py", title="Lista Lojas", icon=":material/shelves:"),
#         st.Page("pages/3Atacado.py", title="Lista Atacado", icon=":material/local_mall:")
#     ],
#     "Financeiro":[
#         st.Page("pages/6Previa_Financeira.py", title="Previa Financeira", icon=":material/wallet:")
#     ]
# }

# --- CONFIGURAÇÃO PAGINA ---
pg = st.navigation(pages,position="top")
pg.run()