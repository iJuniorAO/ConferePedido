import streamlit as st
from supabase import create_client, Client
import pandas as pd

def valida_nova_loja_to_dict(df_validacao):
    if df_validacao.empty:
        st.error(":material/Warning: Preencha: Código, Filial, CNPJ e Grupo")
        st.stop()
        st.stop()
    df_validacao = df_validacao.applymap(lambda x: x[0] if isinstance (x,list) else x)
    df_validacao = df_validacao.applymap(lambda x: x.upper() if isinstance (x,str) else x)
    df_validacao = df_validacao.to_dict(orient="records")
    
    if not df_validacao[0]["CNPJ"].isdigit():
        st.error(":material/Warning: CNPJ deve conter apenas números")
        st.stop()
    if len(df_validacao[0]["CNPJ"])!=14:
        st.error(":material/Warning: CNPJ deve conter 14 números")
        st.stop()
    
    return df_validacao
def cadastra_loja_bd(dados):
    try:
        reposta = (
            supabase.table("Lojas")
            .insert(dados)
            .execute()
        )
        st.success(f"Loja {dados[0]["Filial"]} Cadastrada com sucesso")
    except Exception as e:
        if "uplicate key value violates unique constraint" in str(e) and "Lojas_pkey" in str(e):
            st.error("Erro Código já cadastrado")
        elif "uplicate key value violates unique constraint" in str(e) and "Lojas_CNPJ_key" in str(e):
            st.error("Erro CNPJ já cadastrado")
        elif "uplicate key value violates unique constraint" in str(e) and "unq_lojas_filial" in str(e):
            st.error("Erro Filial já cadastrada")
        else:    
            st.error(f"Erro {e}")
        st.stop()
def obter_todas_lojas():
    try:
        resposta = supabase.table("Lojas").select("Filial").execute()
        return [loja["Filial"] for loja in resposta.data]
    except Exception as e:
        print(f"Erro ao buscar lojas: {e}")
        return [] 

# --- CONFIGURAÇÃO PAGINA ---
st.set_page_config(page_title="Sistema Mumix", layout="wide", initial_sidebar_state="collapsed")

url=st.secrets["connections"]["supabase"]["url"]
key=st.secrets["connections"]["supabase"]["key"]

supabase: Client = create_client(url,key)

if st.query_params.get("debugger") == "true":
    st.session_state.debugger=True
    st.error(":material/Terminal: APP EM TESTE")
st.title(":material/Home: Página inicial")

st.title(":material/Badge: Painel de Controle")
st.write(f"Bem vindo! O que deseja fazer hoje?")

st.divider()

st.markdown("## Acessar páginas:")

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

st.markdown("## Cadastro Lojas:")
if st.toggle("Alterar Cadastro"):
    st.markdown("## :red[:material/Exclamation: AVISO - As Alterações não podem ser desfeitas ]")
    lojas = obter_todas_lojas()

    st.write(f"{len(lojas)-1} Lojas Cadastradas")


    resposta_df = supabase.table("Lojas").select("*").order("Codigo").execute()
    Df_Lojas = pd.DataFrame(resposta_df.data)
    Df_Lojas[Df_Lojas["Grupo"]!="TESTE"]

    st.markdown("### Alterar Grupo:")
    col1, col2 = st.columns(2,vertical_alignment="bottom")
    with col1:
        Loja_Selecionada = st.selectbox("Lojas", Df_Lojas["Filial"])
    with col2:
        Grupo_Selecionado = st.selectbox("Grupo", Df_Lojas["Grupo"].unique())
    if st.button("Confirmar Alteração",width="stretch"):
        resposta = (
            supabase.table("Lojas")
            .update({"Grupo":Grupo_Selecionado})
            .eq("Filial", Loja_Selecionada)
            .execute()
        )
        st.success(f":material/Check: {resposta.data[0]["Filial"]} agora é {resposta.data[0]["Grupo"]}")
    st.divider()

    st.markdown("### Adicionar Loja:")
    Novas_lojas = st.data_editor(
        pd.DataFrame(columns=["Codigo", "Filial", "Razao_Social", "CNPJ", "Grupo"]),
        column_config={
            "Codigo": st.column_config.TextColumn("Codigo", required=True),
            "Filial": st.column_config.TextColumn("Filial", required=True),
            "CNPJ": st.column_config.TextColumn("CNPJ", required=True, max_chars=15),
            "Grupo": st.column_config.TextColumn("Grupo", required=True),
        },
        num_rows="dynamic",
        width="stretch"
    )

    if st.button("Cadastrar Nova Loja", width="stretch"):
        dict_Novas_lojas = valida_nova_loja_to_dict(Novas_lojas)
        cadastra_loja_bd(dict_Novas_lojas)

    st.divider()
    st.markdown("### Excluir Loja")
    lojas.sort()

    loja_excluir = st.selectbox("Selecione a loja que deseja excluir", lojas)
    if st.button("Excluir", width="stretch"):
        try:
            resposta = supabase.table("Lojas").delete().eq("Filial", loja_excluir).execute()
            st.toast(f"Loja {loja_excluir} excluída com sucesso")
            resposta.data
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao excluir {e}")
        "excluir"