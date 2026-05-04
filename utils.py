import streamlit as st
import requests
import re
import pandas as pd
import io

# carrega dados do banco de dados e retorna pandas
@st.cache_data(ttl=120, scope="session")
def carregar_dados_onedrive(input_texto):
    with st.spinner("Pegando Arquivos txt...",show_time=True):
        try:
            # 1. Limpeza: Se o usuário colou o <iframe>, extrai apenas a URL
            url_match = re.search(r'src="([^"]+)"', input_texto)
            url = url_match.group(1) if url_match else input_texto
            
            # 2. Ajuste para SharePoint Business
            # Se for link de embed do SharePoint, mudamos para o modo de download
            if "sharepoint.com" in url:

                if "embed.aspx" in url:
                    # Transforma o link de embed em um link de ação de download
                    url = url.replace("embed.aspx", "download.aspx")
                elif "download=1" not in url:
                    # Se for link de compartilhamento normal, força o download
                    url = url + ("&" if "?" in url else "?") + "download=1"
            else:
                # Caso seja OneDrive Pessoal
                url = url.replace("embed", "download")

            # 3. Faz a requisição
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            
            return response.text
        except Exception as e:
            st.error(f"Erro ao processar URL: {e}")
            return None

def abrir_arquivo_txt(arquivo, colunas=None):
    try:
        if isinstance(arquivo, str):
            arquivo = io.StringIO(arquivo)
        return pd.read_csv(arquivo, sep="|", header=None, names=colunas, encoding="latin1")
    except Exception as e:
        st.error(f"Erro ao ler arquivo {e}")
        st.stop()

def validar_acesso(roles_permitidas=["administrador"]):
    # 1. Verifica se está logado
    if st.session_state.get('perfil') == 'none':
        st.markdown("# :red[:material/lock: ACESSO NEGADO]")
        st.text("É necessário realizar o login para continuar.")
        if st.button('Ir para Login'):
            st.switch_page('login.py')
        st.stop()

    perfil = st.session_state.perfil

    if perfil.get('status') == 'pendente':
        st.warning("# :material/warning: USUÁRIO COM PENDÊNCIA")
        st.text("Entrar em contato com a equipe técnica.")
        st.stop()

    # 3. Verifica permissão de nível
    if perfil.get('role') not in roles_permitidas:
        st.markdown("# :red[:material/block: ACESSO NEGADO]")
        st.text("Seu usuário não possui permissão para esta página.")
        st.stop()