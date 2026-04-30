from supabase import create_client, Client
import streamlit as st

@st.cache_resource(show_spinner=True,scope='session')
def inicia_conexao_bancoDados():
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase

def obter_lojas(supabase):
    try:
        resposta = supabase.table("clientes").select("*").execute()
        # resposta = supabase.table("clientes").select("*").neq('grupo','teste').neq('grupo','atacado').execute()
        return {'status': True,
                'resposta': resposta.data,
                }
    except Exception as e:
        print(f"Erro ao buscar lojas: {e}")
        return {
            'status': False,
            'resposta': []
        }
    

def tratar_erros_supabase(e):
    """
    Docstring for tratar_erros_supabase
        Centraliza a tradução de erros para o usuário PT-BR
        Retorna False para ser usado em fluxo de validação
    :param e: Erro 
    """
    erro_msg = str(e)
    traducoes = {
        'New password should be different from the old password':'A nova senha não pode ser igual à senha atual. Por favor, escolha uma senha diferente.',
        'Email not confirmed': 'Necessário confirmar email antes do 1º Acesso.',
        'Invalid login credentials': 'Usuário ou Senha incorretos'
    }

    for ingles, portugues in traducoes.items():
        if ingles in erro_msg:
            st.error(portugues)
            return False
    
    st.error(f'Erro inesperado {erro_msg}')
    return False
