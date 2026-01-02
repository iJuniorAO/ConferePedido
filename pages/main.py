import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

#   MELHORIAS
#       Login com google ou ms
#   LEMBRAR
#       Passar objeto authenticator para cada página
#       Reinvocar unrendered login widget em cada página
#       update config


# ---- FUNÇÕES E CONSTANTS ---
@st.dialog("Confirmar Alteraçao")
def dupla_confirmacao():
    confirma = st.text_input("Para confirmar digite: CONFIRMO")
    if st.button("Registrar"):
        st.rerun
def carrega_config():
    with open("config.yaml") as file:
        return yaml.load(file, Loader=SafeLoader)
def save_config(config):
    with open("config.yaml", "w") as file:
        yaml.dump(config, file, default_flow_style=False, allow_unicode=True)
ROLES = ["administrador", "usuario", "cliente"]

# --- CONFIGURAÇÃO PAGINA ---
st.set_page_config(page_title="Sistema Mumix", layout="wide")

config = carrega_config()

# Pre-hashing all plain text passwords once
stauth.Hasher.hash_passwords(config['credentials'])


authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

try:
    authenticator.login(
        single_session=True,
        fields={"Username":"Usuário", "Password":"Senha", "Login":"Entrar"}
    )
    #inserir login google
    #inserir login microsoft
except Exception as e:
    st.error(e)

#Somente mostra caso não esteja logado
if not st.session_state.get("authentication_status"):
    
    #esqueci senha
    try:
        username_of_forgotten_password, \
        email_of_forgotten_password, \
        new_random_password = authenticator.forgot_password(
            fields={"Form name":"Esqueci minha senha", "Username":"Usuário","Submit":"Enviar"},
            clear_on_submit=True,
        )
        if username_of_forgotten_password:
            print(f"Usuario: {username_of_forgotten_password}")
            print(f"email: {email_of_forgotten_password}")
            print(f"senha: {new_random_password}")
            save_config(config)
            st.success('Aguarde receber nova senha')
        elif username_of_forgotten_password == False:
            st.error('Usuário não encontrado')
    except Exception as e:
        st.error(e)

#usuário logado
if st.session_state.get("authentication_status"):
    st.title(":material/Home: Página inicial")
    username = st.session_state["username"]

    #Salva as permissões do usuário
    user_role = config["credentials"]["usernames"][username].get("role")
    st.session_state["role"] = user_role

    if user_role == "administrador":
        st.title(":material/Supervisor_Account: Painel de Controle")
        st.write(f"Bem vindo :red[{username}]! O que deseja fazer hoje?")

    elif user_role == "usuario":
        st.title(":material/Badge: Painel de Controle")
        st.write(f"Bem vindo :blue[{username}]! O que deseja fazer hoje?")

    elif user_role == "cliente":
        st.title(":material/Person: Painel de Controle")
        st.write(f"Bem vindo :blue[{username}]! Aqui você pode acompanhar seus pedidos.")
    st.divider()

    #conta SPM
    if user_role in ["administrador", "usuario"]:
        #Header de acordocom usuário:
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
    #administração de contas, somente para adm
        if user_role == "administrador":
            
            st.markdown("# Area Administrador:")
            st.divider()

            #usuarios_ativos = list(config["credentials"]["usernames"].keys())
            cadastro_usuarios = config["credentials"]["usernames"]
            st.markdown(f"## Usuários ativos: :blue[{len(cadastro_usuarios)}]")

            for permissao in ROLES:
                st.markdown(f"### {permissao.title()}")
                for usuario in cadastro_usuarios:
                    if cadastro_usuarios[usuario]["role"] == permissao:
                        st.write(usuario)
            
            st.divider()
            


            #config["credentials"]["usernames"]["role"] == "cliente" ou "usuario"

            usuarios_validos = [
                nome for nome, info in config["credentials"]["usernames"].items()
                if info.get("role") is not None and info.get("role") in ["cliente", "usuario"]
            ]

            usuario_selecionado = st.selectbox("Selecione Usuário",usuarios_validos)
            role_selecionada = st.selectbox("Selecione a Nova Permissão:", ROLES)
            confirmar_alteracao = st.button("Confirmar Alteração")
            #role usuario

            if confirmar_alteracao:
                dupla_confirmacao()
                st.write(cadastro_usuarios[usuario_selecionado])
                st.write(f"Role anterior: {cadastro_usuarios[usuario_selecionado]["role"]}")    
                cadastro_usuarios[usuario_selecionado]["role"] = role_selecionada
                save_config(config)
                st.write(f"Role atual: {cadastro_usuarios[usuario_selecionado]["role"]}")
                st.success("!")



            
            

            st.divider()


            with st.expander(":material/settings: Administração Usuários"):
                #Cadastrar novos usuários
                with st.expander(":material/Person_Add: Cadastro de Novos Usuário"):
                    
                    st.markdown("## Recomendações para Criar Conta:")
                    coluna1,coluna2 = st.columns(2)
                    with coluna1:
                        st.markdown("""
                            CAMPOS:
                            1. Todos campos são obrigatórios:
                            2. Não é permitido criar emails repetidos
                            3. Não é permitido criar usuários repetidos
                                    """)
                    with coluna2:
                        st.markdown("""                             
                            SENHAS:
                            1. Senhas precisam ser iguais
                            2. Entre 8 e 20 caracteres
                            3. Uma letra maiuscula
                            4. Um caracter especial (@$!%*?&)
                            """)
                    try:
                        novo_email, novo_user, novo_name = authenticator.register_user(captcha=False, password_hint=False,
                                                    fields= {'Form name':'Cadastrar Usuário',
                                                            'First name': 'Nome',
                                                            'Last name': 'Sobrenome',
                                                            'Username':'Usuário',
                                                            'Password':'Senha',
                                                            'Repeat password':'Repetir Senha',
                                                            'Password hint':'Dica de Senha',
                                                            'Register':'Registrar'}
                                                            )
                        #save_config(config)
                        if novo_email and novo_user and novo_name:
                            save_config(config)    
                            st.success(f":material/Check: Conta: '{novo_user}' cadastrado com sucesso!")
                    except Exception as e:
                        st.error(e)
                #Redefinir senha
                with st.expander(":material/Person_Edit: Redefinir Senha"):
                    try:
                        if authenticator.reset_password(
                            st.session_state.get("username"),
                            fields={"Form name":"Redefinir Senha", "Current password":"Senha Atual", "New password": "Nova Senha", "Repeat password":"Repetir a Senha"},
                            ):
                            save_config(config)
                            st.success("Senha modificada com sucesso")
                            st.info("aviso")
                    except Exception as e:
                        st.error(e)
    elif user_role == "cliente":


        st.button(":material/Add_Shopping_Cart: Fazer Novo Pedido")
        st.button(":material/Shopping_Cart: Meus Pedidos")



    #   --- CRIAR user_role cliente


    #Logout e sidebar
    with st.sidebar:
        authenticator.logout()
        st.markdown(f"# Bem vindo! **{st.session_state.get("name")}**")
        st.markdown(f"### Nível de acesso: {user_role}")

# erro no login
elif st.session_state.get("authentication_status") is False:
    st.error("Nome e/ou Senha incorreto")

# sem tentativa de login
elif st.session_state.get("authentication_status") is None:
    st.info("Entre com usuário e senha")


if False:
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