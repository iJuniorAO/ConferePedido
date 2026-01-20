import streamlit as st
from supabase import create_client, Client
import pandas as pd

# ---   inicia bd   ---

url = st.secrets["connections"]["supabase"]["url"]
key = st.secrets["connections"]["supabase"]["key"]

supabase: Client = create_client(url, key)


# --- PUXA INFORMAÇÃO E VALIDA ---
try:
    resposta = supabase.table("PedidosLojas").select("*").order("id").execute()
    if resposta.data == []:
        st.info("Não foi possível encontrar nenhuma informação")
        st.stop()
except Exception as e:
    st.error(f"Erro ao buscar dados: {e}")

ultimos_pedidos = pd.DataFrame(resposta.data).sort_values("id", ascending=False)

#   --- MOSTRAR INFORMAÇÕES
st.title(":material/Local_Mall: Pedidos")
st.markdown("## :material/Filter_Alt: FILTRO -  Lojas que realizaram pedidos ")
pedidos_teste = st.toggle("Retirar Pedidos Teste")
data_selecionada = st.date_input("Selecione a data",format="DD/MM/YYYY")

#converte valores
data_selecionada = data_selecionada.strftime("%d/%m/%Y")
ultimos_pedidos["data_pedido"] = pd.to_datetime(ultimos_pedidos["data_pedido"]).dt.strftime("%d/%m/%Y")
ultimos_pedidos["hora_pedido"] = pd.to_datetime(ultimos_pedidos["hora_pedido"]).dt.strftime("%H:%M")

#filtros
filtrado_ultimos_pedidos = ultimos_pedidos[ultimos_pedidos["data_pedido"] == data_selecionada]
if pedidos_teste:
    filtrado_ultimos_pedidos = filtrado_ultimos_pedidos[filtrado_ultimos_pedidos["obs"]!="TESTE"]

pedido_data = filtrado_ultimos_pedidos.pivot_table(
    index="loja",
    columns="tipo_pedido",
    values="id",
    aggfunc="count"
)

#   --- APREENTAÇÃO DE DADOS
st.subheader(":material/history: Ultimos Pedidos")
st.dataframe(ultimos_pedidos[['id', 'data_pedido','hora_pedido', 'loja', 'tipo_pedido', 'pedido_erp', 'pedido_original', 'obs']],
            hide_index=True)

st.subheader(":material/Calendar_Clock: Pedidos Filtrados")
if filtrado_ultimos_pedidos.empty:
    st.info("Não foi possível encontrar nenhum pedido")
else:
    st.dataframe(
        filtrado_ultimos_pedidos[['id', 'data_pedido','hora_pedido', 'loja', 'tipo_pedido', 'pedido_erp', 'pedido_original', 'obs']],
        hide_index=True
    )

st.subheader(":material/Delivery_truck_Speed: Pedidos DATA")
if pedido_data.empty:
    st.info("Não foi possível encontrar nenhum pedido")
else:
    pedido_data = pedido_data.assign(
        Qt_Palete_Seco = None,
        Qt_Palete_CONG = None,
        Qt_Palete_DIVISÃO = None,
        TOTAL_Qt_Palete = None,
    )
    pedido_data