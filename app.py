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
ROLES = ["administrador", "usuario", "cliente"]
if "confirmacao_alteracao_permissao" not in st.session_state:
    st.session_state.confirmacao_alteracao_permissao = None
if "confirmacao_alteracao_senha" not in st.session_state:
    st.session_state.confirmacao_alteracao_senha = None
resumo = {
    "ativos": [],
    "inativos": [],
    "logados": [],
    "por_role": {},
}

@st.dialog("Confirmar Alteraçao")
def dupla_confirmacao(registro):
    st.error(":material/Warning: Essa ação não pode ser desfeita")
    confirma = st.text_input("Para confirmar digite: CONFIRMO")
    if registro == "permissao":
        if st.button("Registrar"):
            if confirma == "CONFIRMO":
                st.session_state.confirmacao_alteracao_permissao = True
                st.rerun()
            else:
                st.rerun()
    elif registro == "senha":
        if st.button("Registrar"):
            if confirma == "CONFIRMO":
                st.session_state.confirmacao_alteracao_senha = True
                st.rerun()
            else:
                st.rerun()
def carrega_config():
    with open("config.yaml") as file:
        return yaml.load(file, Loader=SafeLoader)
def save_config(config):
    with open("config.yaml", "w") as file:
        yaml.dump(config, file, default_flow_style=False, allow_unicode=True)

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

#tela login
try:
    authenticator.login(
        fields={"Username":"Usuário", "Password":"Senha", "Login":"Entrar"}
    )
    #inserir login google
    #inserir login microsoft
except Exception as e:
    st.error(e)
    st.session_state
    stauth


#usuário logado
if st.session_state.get("authentication_status"):
    username = st.session_state["username"]
    cadastro_usuarios = config["credentials"]["usernames"]
    st.session_state["usuario_ativo"] = cadastro_usuarios[username]["is_active"]

    if cadastro_usuarios[username]["is_active"]:
        st.title(":material/Home: Página inicial")
        #Marca como usuário logado
        cadastro_usuarios[username]["logged_in"] = True
        save_config(config)

        #Salva as permissões do usuário
        user_role = config["credentials"]["usernames"][username].get("roles")
        st.session_state["roles"] = user_role

        #Cabeçalho conforme conta
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

            #Acessar Páginas e apps em progresso
            col1,col2, col3 = st.columns([2,2,1])
            with col1:
                st.markdown("### :green[:material/Cloud_Done:] ATIVOS")

                if st.button("Acessar ERP"):
                    st.switch_page("pages/Altera_ERP.py")
                if st.button("Lista"):
                    st.switch_page("pages/Lista.py")
            with col2:
                st.markdown(":orange[:material/Upgrade:] Em Progresso")
                st.markdown("Organizados por ordem de prioridade")
                st.write(":orange-badge[:material/Lab_Profile: Login]")
                st.write(":orange-badge[:material/Lab_Profile: Previa Financeira]")
                st.write(":orange-badge[:material/Lab_Profile: Troca]")
                st.write(":red-badge[:material/code: Divisão]")
                st.write(":red-badge[:material/code: Lojas/Carrinho]")
                st.write(":red-badge[:material/code: Lojas/MeusPedidos]")
            with col3:
                st.markdown("## :material/Subtitles: Legenda")
                st.markdown(":green[:material/Grading:] Implementação")
                st.markdown(":orange[:material/Lab_Profile:] Etapa de teste")
                st.markdown(":red[:material/code:] Etapa de Codificação")

        #administração de contas, somente para adm
            if user_role == "administrador":
                #Preenche tabela de resumos
                for user in cadastro_usuarios:
                    #usuarios ativos
                    if cadastro_usuarios[user]["is_active"]:
                        resumo["ativos"].append(user)
                        #usuarios logados
                        if cadastro_usuarios[user]["logged_in"]:
                            resumo["logados"].append(user)
                        for role in ROLES:
                            if cadastro_usuarios[user]["roles"] == role:
                                if role not in resumo["por_role"]:
                                    resumo["por_role"][role] = []
                                resumo["por_role"][role].append(user)
                    else:
                        resumo["inativos"].append(user)

                st.divider()
                st.markdown("# Area Administrador:")
                m1, m2, m3 = st.columns(3, border=False)
                with m1:                    
                    st.markdown(f"### Ativos: :blue[{len(resumo["ativos"])}]")

                with m2:                    
                    st.markdown(f"### Online: :green[{len(resumo["logados"])}]")
                with m3:                    
                    st.markdown(f"### Offline: :red[{len(resumo["ativos"])-len(resumo["logados"])}]")

                with st.expander(":material/User_Attributes: Usuários:"):
                    for permissao in resumo["por_role"]:
                        st.markdown(f"## {permissao.title()}")

                        for nome in resumo["por_role"][permissao]:
                            if nome in resumo["logados"]:
                                st.write(f":green[:material/Radio_Button_Checked: {nome}]")
                            else:
                                st.write(f":red[ :material/Radio_Button_Unchecked: {nome}]")
                st.space()

                with st.expander(":material/settings: Editar Usuários"):
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

                            if novo_email and novo_user and novo_name:
                                config["credentials"]["usernames"][novo_user]["roles"] = "cliente"
                                config["credentials"]["usernames"][novo_user]["logged_in"] = False
                                config["credentials"]["usernames"][novo_user]["is_active"] = True
                                save_config(config)    
                                st.success(f":material/Check: Conta: '{novo_user}' cadastrado com sucesso!")
                        except Exception as e:
                            st.error(e)
                    
                    with st.expander(":material/Person_Edit: Editar Permissão"):
                        usuario_selecionado_permissao = st.selectbox("Selecione Usuário",resumo["ativos"],key=1)
                        role_selecionada = st.selectbox("Selecione a Nova Permissão:", ROLES)
                        confirmar_alteracao_permissao = st.button("Confirmar Alteração")

                        if confirmar_alteracao_permissao:
                            dupla_confirmacao("permissao")
                        if st.session_state.get("confirmacao_alteracao_permissao"):
                            cadastro_usuarios[usuario_selecionado_permissao]["roles"] = role_selecionada
                            save_config(config)
                            st.session_state.confirmacao_alteracao_permissao = False
                            st.rerun()

                    with st.expander(":material/Person_Edit: Reset de Senha"):
                        st.markdown("Após confirmar a senha será redefinida para: ':red[MUMIX123456]'")
                        usuario_selecionado_senha = st.selectbox("Selecione Usuário", resumo["ativos"],key=2)
                        confirmar_alteracao_senha = st.button("Confirmar Senha Padrão")
                        if confirmar_alteracao_senha:
                            dupla_confirmacao("senha")
                        if st.session_state.get("confirmacao_alteracao_senha"):
                            cadastro_usuarios[usuario_selecionado_senha]["password"] = "MUMIX123456"
                            st.session_state.confirmacao_alteracao_senha = False
                            save_config(config)
                            st.success("Senha Alterado com sucesso")

                    with st.expander(":material/No_Accounts: Desativar Usuários"):
                        desativa_usuario_selecionado = st.selectbox("Selecione Usuário", resumo["ativos"],key=3)
                        confirmar_alteracao_ativos = st.button("Confirmar Desativação")
                        if confirmar_alteracao_ativos:
                            cadastro_usuarios[desativa_usuario_selecionado]["is_active"] = False
                            save_config(config)
                            st.success(f"{desativa_usuario_selecionado} Desativado com sucesso")

                    with st.expander(":material/Person_Add_Disabled: Reativar Usuarios"):
                        
                        ativar_usuario_selecionado = st.selectbox("Selecione usuário para ativação", resumo["inativos"], key=4)
                        if resumo["inativos"] == []:
                            confirmar_alteracao_desativado = st.button("Confirmar Ativação", disabled=True)
                        else:
                            confirmar_alteracao_desativado = st.button("Confirmar Ativação")
                        if confirmar_alteracao_desativado:
                            cadastro_usuarios[ativar_usuario_selecionado]["is_active"] = True
                            save_config(config)
                            st.success(f"{ativar_usuario_selecionado} foi ativado com sucesso")

        elif user_role == "cliente":
            st.markdown("# :material/Shopping_Bag: Pedidos:")

            st.button(":material/Add_Shopping_Cart: Fazer Novo Pedido")
            st.button(":material/Shopping_Cart: Meus Pedidos")
        
        st.divider()
        
        #Redefinir senha todos usuários
        st.markdown("# :material/Article_Person: Minha Conta")
        with st.expander(":material/Person_Edit: Redefinir Minha Senha"):
            try:
                if authenticator.reset_password(
                    st.session_state.get("username"),
                    fields={"Form name":"Redefinir Senha", "Current password":"Senha Atual", "New password": "Nova Senha", "Repeat password":"Repetir a Senha"},
                    ):
                    save_config(config)
                    st.success("Senha modificada com sucesso")
            except Exception as e:
                st.error(e)

        #Logout e sidebar
        with st.sidebar:
            
            authenticator.logout("Sair")
            if st.session_state.get("authentication_status") is None:
                    if username in config["credentials"]["usernames"]:
                        config["credentials"]["usernames"][username]["logged_in"] = False 
                        save_config(config)
                        st.rerun()

            st.markdown(f"# Bem vindo! **{st.session_state.get("name")}**")
            st.markdown(f"### Nível de acesso: {user_role}")
    else:
        st.markdown("# :red[:material/Block: Usuário Inativado]")
        st.stop()


# erro no login
elif st.session_state.get("authentication_status") is False:
    st.error("Nome e/ou Senha incorreto")
# sem tentativa de login
elif st.session_state.get("authentication_status") is None:
    st.info("Entre com usuário e senha")