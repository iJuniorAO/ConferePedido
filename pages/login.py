import streamlit as st

# 1. Função que verifica as credenciais
def verificar_login(usuario, senha):
    # Aqui você pode conectar a um banco de dados
    # Para o exemplo, usaremos valores fixos:
    return usuario == "admin" and senha == "12345"

# 2. Inicializa o estado de login se não existir
if "logado" not in st.session_state:
    st.session_state.logado = False
    print(st.session_state)

# 3. Interface de Login
def tela_login():
    st.title("🔑 Área de Acesso")
    with st.form("login"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        botao_entrar = st.form_submit_button("Entrar")

        if botao_entrar:
            if verificar_login(usuario, senha):
                st.session_state.logado = True
                st.success("Login efetuado!")
                st.rerun() # Recarrega a página para entrar no sistema
            else:
                st.error("Usuário ou senha incorretos")

# 4. Conteúdo Protegido
def pagina_principal():
    st.title("🚀 Bem-vindo ao Sistema")
    st.write(f"Olá, você está acessando dados confidenciais.")
    
    if st.button("Sair"):
        st.session_state.logado = False
        st.rerun()

# 5. Lógica de Navegação
if st.session_state.logado:
    pagina_principal()
else:
    tela_login()