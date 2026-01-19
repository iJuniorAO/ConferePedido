import streamlit as st
from supabase import create_client, Client
import pandas as pd


url = st.secrets["connections"]["supabase"]["url"]
key = st.secrets["connections"]["supabase"]["key"]

# Inicializa o cliente oficial
supabase: Client = create_client(url, key)

st.title(":material/Local_Mall: Pedidos")

# --- DADOS ---
try:
    resposta = supabase.table("PedidosLojas").select("*").order("id").execute()
    #resposta = supabase.table("PedidosLojas").select("*").order("id", desc=True).execute()
except Exception as e:
    st.error(f"Erro ao buscar dados: {e}")

if resposta.data == []:
    st.info("Não foi possível encontrar nenhuma informação")
    st.stop()
else:
    ultimos_pedidos = pd.DataFrame(resposta.data)

st.markdown("## :material/Filter_Alt: FILTRO -  Lojas que realizaram pedidos ")
data_selecionada = st.date_input("Selecione a data",format="DD/MM/YYYY")
st.space()


ultimos_pedidos["data_pedido"] = pd.to_datetime(ultimos_pedidos["data_pedido"]).dt.strftime("%d/%m/%Y")
ultimos_pedidos["hora_pedido"] = pd.to_datetime(ultimos_pedidos["hora_pedido"]).dt.strftime("%H:%M")

ultimos_pedidos = ultimos_pedidos.drop_duplicates(
    subset=["data_pedido", "loja", "tipo_pedido"],
    keep="first"
)
filtro_tabela = ultimos_pedidos[ultimos_pedidos["data_pedido"] == data_selecionada]
"empty"
filtro_tabela.empty

tabela_lojas = filtro_tabela.pivot_table(
    index="loja",
    columns="tipo_pedido",
    values="id",
    aggfunc="count"
).fillna(0)

#   --- APREENTAÇÃO DE DADOS
st.subheader(":material/history: Pedidos Recentes")

st.dataframe(ultimos_pedidos[['id', 'data_pedido','hora_pedido', 'loja', 'tipo_pedido', 'pedido_erp', 'pedido_original', 'obs']],
            hide_index=True)