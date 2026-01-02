import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema ERP Mumix", layout="wide")

# --- FUNÇÕES DE CONFIGURAÇÃO ---
def load_config():
    with open('config.yaml') as file:
        return yaml.load(file, Loader=SafeLoader)
def save_config(config):
    with open('config.yaml', 'w') as file:
        yaml.dump(config, file, default_flow_style=False)


# Carregar dados do YAML
config = load_config()

# Inicializar o autenticador
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- INTERFACE DE LOGIN ---
# Na versão nova, a função login não retorna variáveis diretamente
authenticator.login(location='main')


# Verificação do status de autenticação via Session State
if st.session_state["authentication_status"]:
    # Variáveis úteis
    username = st.session_state["username"]
    name = st.session_state["name"]
    
    # Buscar a Role (permissão) no arquivo config
    user_role = config['credentials']['usernames'][username].get('role')
    st.session_state['role'] = user_role # Salva na sessão para as outras páginas

    # --- SIDEBAR COM LOGOUT ---
    st.sidebar.title(f"Olá, {name}")
    st.sidebar.write(f"Nível de acesso: **{user_role.upper()}**")
    authenticator.logout('Sair do Sistema', 'sidebar')

    # --- LÓGICA DE VISUALIZAÇÃO POR PERMISSÃO ---
    if user_role in ["adm", "user"]:
        st.title("📊 Painel de Controle Interno")
        st.write(f"Bem-vindo ao sistema principal, {name}.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("Utilize o menu lateral para acessar as páginas de ERP, Listas e Previsões.")
        
        # Se for ADM, mostra opção de cadastrar novos usuários
        if user_role == "adm":
            st.divider()
            with st.expander("⚙️ Administração: Cadastrar Novo Usuário"):
                try:
                    if authenticator.register_user('Registrar', preauthorization=False):
                        save_config(config)
                        st.success('Usuário cadastrado com sucesso no sistema!')
                except Exception as e:
                    st.error(e)

    elif user_role == "client":
        st.title("🎯 Área do Cliente")
        st.write("Bem-vindo! Aqui você pode acompanhar seus pedidos.")
        
        # Botão para facilitar a ida para a página de pedidos
        if st.button("Acessar Meus Pedidos"):
            st.switch_page("pages/Pedido.py")

elif st.session_state["authentication_status"] is False:
    st.error('Usuário ou senha incorretos.')
elif st.session_state["authentication_status"] is None:
    st.warning('Por favor, utilize o formulário lateral ou central para entrar.')

# --- RECUPERAÇÃO DE SENHA (OPCIONAL) ---
if not st.session_state["authentication_status"]:
    with st.expander("Esqueci minha senha"):
        try:
            username_forgot, email_forgot, new_pw = authenticator.forgot_password('Recuperar')
            if username_forgot:
                st.success(f'Sua nova senha é: {new_pw}')
                save_config(config)
        except Exception as e:
            st.error(e)
