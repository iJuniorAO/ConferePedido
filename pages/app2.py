import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

st.set_page_config(page_title="Sistema Mumix", layout="wide")

# 1. Carregamento e Auto-Hash
def load_and_hash():
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    
    modified = False
    for user in config['credentials']['usernames']:
        pw = config['credentials']['usernames'][user]['password']
        if not str(pw).startswith('$2b$'):
            config['credentials']['usernames'][user]['password'] = stauth.Hasher.hash_passwords([pw])[0]
            modified = True
    
    if modified:
        with open('config.yaml', 'w') as file:
            yaml.dump(config, file, default_flow_style=False)
    return config

config = load_and_hash()

# 2. Inicialização
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# 3. Renderização do Login
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    username = st.session_state["username"]
    user_role = config['credentials']['usernames'][username].get('role')
    st.session_state['role'] = user_role

    st.sidebar.success(f"Logado como: {st.session_state['name']}")
    authenticator.logout('Sair', 'sidebar')

    # Lógica de Permissões
    if user_role == "adm":
        st.title("Painel Administrador - Mumix")
        st.info("Você tem acesso total ao sistema.")
    elif user_role == "user":
        st.title("Painel do Usuário")
    elif user_role == "client":
        st.switch_page("pages/Pedido.py")

elif st.session_state["authentication_status"] is False:
    st.error('Usuário ou senha incorretos')
elif st.session_state["authentication_status"] is None:
    st.warning('Insira suas credenciais')