import streamlit as st
from supabase import create_client, Client
import pandas as pd

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

resposta = supabase.table("Lojas").select("*").order("Codigo").execute()
Df_Lojas = pd.DataFrame(resposta.data)
Df_Lojas

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
    use_container_width=True
)

if st.button("Cadastrar Nova Loja", width="stretch"):
    print("df")
    print(Novas_lojas)
    if Novas_lojas.empty:
        st.error("Nenhuma loja informada!")
        st.stop()
    
    print("df")
    print(Novas_lojas)

    Novas_lojas = Novas_lojas.dropna()
    Novas_lojas = Novas_lojas.to_dict(orient="records")

    print("------")
    for colunas in Novas_lojas:
        print(colunas)


    st.info(Novas_lojas)
    

    if False:
        reposta = (
            supabase.table("Lojas")
            .insert(Novas_lojas)
            .execute()
        )
        st.info(Novas_lojas)
        st.info(resposta)
