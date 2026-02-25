import streamlit as st
from supabase import create_client, Client
import pandas as pd
import time

@st.dialog("Processando...",dismissible=False)
def rerun_bd(msg="Ação Realizada com Sucesso !"):
    st.success(msg)
    placeholder=st.space()

    for seg in range(3,-1,-1):
        placeholder.metric("Aguarde...",f"{seg}")
        time.sleep(1)
    
    time.sleep(0.5)
    
    st.rerun()
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
        rerun_bd(f"Loja {dados[0]["Filial"]} Cadastrada com sucesso")
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
        resposta = supabase.table("Lojas").select("*").order("Codigo").execute()
        return resposta.data
    except Exception as e:
        print(f"Erro ao buscar lojas: {e}")
        return [] 
def alterar_grupo():
    st.markdown("### Alterar Grupo:")
    col1, col2 = st.columns(2,vertical_alignment="bottom")
    with col1:
        Loja_Selecionada = st.selectbox("Lojas", df_lojas["Filial"],key="2")
    with col2:
        Grupo_Selecionado = st.selectbox("Grupo", df_lojas["Grupo"].unique())
    if st.button("Confirmar Alteração",width="stretch"):
        resposta = (
            supabase.table("Lojas")
            .update({"Grupo":Grupo_Selecionado})
            .eq("Filial", Loja_Selecionada)
            .execute()
        )
        rerun_bd(f":material/Check: {resposta.data[0]["Filial"]} agora é {resposta.data[0]["Grupo"]}")
    st.divider()
def adicionar_loja():

    st.markdown("### Adicionar Loja:")
    Novas_lojas = st.data_editor(
        pd.DataFrame(columns=["Codigo", "Filial", "Razao_Social", "CNPJ", "Grupo"]),
        column_config={
            "Codigo": st.column_config.TextColumn("Codigo", required=True),
            "Filial": st.column_config.TextColumn("Filial", required=True),
            "CNPJ": st.column_config.TextColumn("CNPJ", required=True, max_chars=14),
            "Grupo": st.column_config.TextColumn("Grupo", required=True),
        },
        num_rows="dynamic",
        width="stretch"
    )

    if st.button("Cadastrar Nova Loja", width="stretch"):
        dict_Novas_lojas = valida_nova_loja_to_dict(Novas_lojas)
        cadastra_loja_bd(dict_Novas_lojas)

    st.divider()
def excluir_loja():
    st.markdown("### Excluir Loja")

    loja_excluir = [loja["Filial"] for loja in lojas]

    loja_excluir_selecionada = st.selectbox("Selecione a loja que deseja excluir", loja_excluir)
    if st.button("Excluir", width="stretch"):
        try:
            resposta = supabase.table("Lojas").delete().eq("Filial", loja_excluir_selecionada).execute()
            rerun_bd(f"Loja {loja_excluir_selecionada} excluída com sucesso")
        except Exception as e:
            st.error(f"Erro ao excluir {e}")
            st.stop()
def alterar_fator_porcentagem():
    st.divider()
    st.markdown("### Alterar Fator Porcentagem")

    c1, c2 = st.columns(2)
    with c1:
        Loja_Selecionada = st.selectbox("Lojas", df_lojas["Filial"],key="1")
    with c2:
        novo_fator_porcentagem = st.number_input("Digite Novo Fator de Conversão",min_value=0.0,max_value=100.0,value=0.0,placeholder="Digite Novo Valor",key="3")
    
    if st.button("Altera Fator de Porcentagem",width="stretch"):
        resposta = (
            supabase.table("Lojas")
            .update({"fator_porcentagem":novo_fator_porcentagem})
            .eq("Filial", Loja_Selecionada)
            .execute()
        )
        rerun_bd(f":material/Check: {resposta.data[0]["Filial"]} agora é {resposta.data[0]["fator_porcentagem"]}")
    st.divider()

# --- CONFIGURAÇÃO PAGINA ---
st.set_page_config(page_title="Sistema Mumix", layout="wide", initial_sidebar_state="collapsed")

url=st.secrets["connections"]["supabase"]["url"]
key=st.secrets["connections"]["supabase"]["key"]

supabase: Client = create_client(url,key)

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
    if st.button("Atacado"):
        st.switch_page("pages/3Atacado.py")
    if st.button("Pedidos"):
        st.switch_page("pages/4Pedidos.py")
    if st.button("Calcula_NF"):
        st.switch_page("pages/5Calcula_NF.py")
    if st.button("Previa Financeira"):
        st.switch_page("pages/6Previa_Financeira.py")
with col2:
    st.markdown("## :orange[:material/Upgrade:] Em Progresso")
    st.write(":orange-badge[:material/Lab_Profile: Previa Financeira]")
    st.write(":orange-badge[:material/Lab_Profile: Pedido]")
    st.write(":orange-badge[:material/Lab_Profile: Atacado]")
    st.write(":orange-badge[:material/Lab_Profile: Calula NF]")

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
    df_lojas = pd.DataFrame(lojas)

    st.write(f"{len(df_lojas)-1} Lojas Cadastradas")   # lojas -1 de teste

    fator_porc = df_lojas["fator_porcentagem"].sum()
    if fator_porc!=100:
        st.error(f":material/Close: Soma do Fator de Porcentagem {fator_porc}% o correto é 100%")
        #continuar

    mostrar_grupo_teste = st.toggle("Mostrar Lojas Teste")

    if mostrar_grupo_teste:
        df_lojas
    else:
        df_lojas[df_lojas["Grupo"]!="TESTE"]

    #   Alterar grupo não está alterando no bd
    alterar_grupo()
    adicionar_loja()
    excluir_loja()
    alterar_fator_porcentagem()