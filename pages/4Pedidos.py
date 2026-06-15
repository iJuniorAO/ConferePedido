import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

hoje = datetime.now().date()
url = st.secrets["connections"]["supabase"]["url"]
key = st.secrets["connections"]["supabase"]["key"]
supabase: Client = create_client(url, key)

#   --  CONSTANTES --
ROTA1 = ["JARDIM ALTEROSA", "SANTA CRUZ", "SAO LUIZ", "CENTRO BETIM", "NOVA CONTAGEM","LARANJEIRAS", "MUMIX EXPRESS"]
ROTA2 = ["RIBEIRÃO DAS NEVES", "VENDA NOVA", "GOIANIA", "LAGOA SANTA", "CEU AZUL", "PALMITAL"]
ROTA3 = ["CABANA", "CABRAL"]
ROTA4 = ["PEDRA AZUL", "CONFISCO", "SERRANO"]
ROTA5 = ["ABILIO MACHADO", "BRIGADEIRO"]
ROTA6 = ["SILVA LOBO", "SANTA HELENA", "ELDORADO", "IBIRITE"]
ROTA7 = ["LAGUNA", "PROGRESSO", "PINDORAMA"]
ROTA8 = ["PARA DE MINAS", "CAETE"]

Rotas = [ROTA1, ROTA2, ROTA3, ROTA4, ROTA5, ROTA6, ROTA7, ROTA8]

def identificar_rota(loja):
    for i, rota in enumerate(Rotas, 1):
        if loja.upper() in rota:
            return f"ROTA {i}"
    return "SEM ROTA"

st.set_page_config(
    page_title="Confere Pedidos",
    layout="wide")

def buscar_pedido_bd(dt_inicial=None, dt_final=None, dt_igual=None):
    query = supabase.table("PedidosLojas").select("*").order("id", desc=True)   
    with st.spinner("Processando...", show_time=True):
        try:
            if dt_igual:
                dt_igual = datetime(dt_igual.year, dt_igual.month, dt_igual.day)
                query = query.eq("data_pedido",dt_igual)
            else:
                if dt_inicial:
                    dt_inicial = datetime(dt_inicial.year, dt_inicial.month, dt_inicial.day)
                    query = query.gte("data_pedido", dt_inicial)
                else:
                    query = query.gte("data_pedido", datetime(hoje.year,hoje.month,1))
                if dt_final:
                    dt_final = datetime(dt_final.year, dt_final.month, dt_final.day)
                    query = query.lte("data_pedido", dt_final)

            resposta = query.execute()
            #resposta = query.gte("data_pedido",datetime(hoje.year,hoje.month,1)).order("id").execute()
            if resposta.data == []:
                return True, "Não foi possível encontrar nenhuma informação"
            df = pd.DataFrame(resposta.data).sort_values("id", ascending=False)
            df["data_pedido"] = pd.to_datetime(df["data_pedido"])
            df["data_pedido"] = df["data_pedido"].dt.date
            return False, df
        except Exception as e:
            return True, (f"Erro ao buscar dados: {e}")

@st.cache_data(ttl=86400, show_spinner=False)
def carregar_lojas_banco_dados():
    try:
        resposta = supabase.table("Lojas").select("Filial").order("Filial").execute()
        return [loja["Filial"] for loja in resposta.data]
    except Exception as e:
        print(f"Erro ao buscar lojas: {e}")
        return []

falha, ultimos_pedidos = buscar_pedido_bd()
if falha:
    st.markdown("### :material/Close: Erro ao Buscar Pedidos")
    st.error(f"ERRO - {falha}")
    st.stop()

st.markdown("# :material/Local_Mall: Pedidos")
st.markdown("### :material/history: Ultimos Pedidos - Mes Atual")
st.dataframe(
    ultimos_pedidos[['id', 'data_pedido','hora_pedido', 'loja', 'tipo_pedido', 'pedido_erp', 'pedido_original']],
    column_config={
        "data_pedido": st.column_config.DateColumn("data_pedido",format="DD/MM/YYYY"),
        "hora_pedido": st.column_config.TimeColumn("hora_pedido",format="HH:MM")},
    hide_index=True,
    )

st.space()
st.divider()
st.markdown("### :material/Filter_Alt: FILTRO")
col1, col2 = st.columns(2)
with col1:
    data_inicial = st.date_input("Selecione a data inicial",value=None, format="DD/MM/YYYY",key="1")
with col2:
    data_final = st.date_input("Selecione a data final",value=None, format="DD/MM/YYYY",key="2")

pedidos_filtrados = ultimos_pedidos
if data_inicial==None or data_final==None:
    st.info("Inserir valor da Data Inicial e Final")
else:
    prazo = data_final-data_inicial
    if prazo.days<=7:
        if data_inicial<=data_final:
            falha, pedidos_filtrados = buscar_pedido_bd(data_inicial,data_final)
            if falha:
                st.error(f"ERRO - {falha}")
            if not pedidos_filtrados.empty:
                st.dataframe(
                    pedidos_filtrados[['id', 'data_pedido','hora_pedido', 'loja', 'tipo_pedido', 'pedido_erp', 'pedido_original']],
                    column_config={
                        "data_pedido": st.column_config.DateColumn("data_pedido",format="DD/MM/YYYY")},
                    hide_index=True
                )
            else:
                st.info("Nenhum Pedido Encontrado")
        else:
            st.error("Data inicial deve ser antes da Data Final")
    else:
        st.error(f"O prazo deve ser até 7 dias. Prazo selecionado: {prazo.days} dias")

st.space()
st.divider()
st.markdown("# :material/Delivery_truck_Speed: Rotas")
dt_Tipo_Pedido = st.date_input("Selecione a data", format="DD/MM/YYYY",key="3")

falha, pedidos_igual_dt = buscar_pedido_bd("","",dt_Tipo_Pedido)
if falha:
    st.error(f"ERRO - {pedidos_igual_dt}")
    st.stop()

if dt_Tipo_Pedido:
    lojas = carregar_lojas_banco_dados()
    pedidos_igual_dt["loja"] = pedidos_igual_dt["loja"].str.strip()
    pedidos_todos = pedidos_igual_dt.pivot_table(
        index="loja",
        columns="tipo_pedido",
        values="id",
        aggfunc="count"
    )
    if pedidos_todos.empty:
        st.info("Não foi possível encontrar nenhum pedido")
        st.stop()
    if lojas:
        pedidos_todos = pedidos_todos.reindex(lojas)

    pedidos_todos["TemPedido"] = pedidos_todos.notna().any(axis=1)
    lojas_sem_pedido = [loja for loja in pedidos_todos.index if not pedidos_todos.loc[loja, "TemPedido"]]
    
    for tipo_pedido in ["CONG", "SECO", "PESO"]:
        if tipo_pedido in pedidos_todos:
            pedidos_todos[tipo_pedido] = pedidos_todos[tipo_pedido].astype(object)
            pedidos_todos.loc[pedidos_todos[tipo_pedido].notna(), tipo_pedido] = "x"
        else:
            pedidos_todos[tipo_pedido] = ""
    pedidos_todos = pedidos_todos.fillna("")
    pedidos_todos = pedidos_todos.reset_index()
    pedidos_todos["ROTA"] = pedidos_todos["loja"].apply(identificar_rota)

    # Reordena as colunas para facilitar a visualização por rota
    cols = ["ROTA"] + [c for c in pedidos_todos.columns if c not in ["ROTA"]]
    pedidos_todos = pedidos_todos[cols].sort_values(by=["ROTA", "loja"])

    pedidos_feitos = pedidos_todos[pedidos_todos["TemPedido"]].drop(columns=["TemPedido"])

    if lojas_sem_pedido:
        st.info(f"Houveram: {len(lojas_sem_pedido)} lojas que não realizaram pedido")
        with st.expander(":material/visibility: Ver Lojas sem Pedidos"):
            for i in lojas_sem_pedido:
                st.write(f"Loja: '{i}'")
        
    st.space()
    st.info(f"Houveram: {len(pedidos_feitos["loja"].unique())} lojas que realizaram pedido")
    with st.expander(":material/visibility: Ver Lojas com Pedidos"):
        st.dataframe(
            pedidos_feitos,
            width="stretch",
            hide_index=True
        )
    #TODO verificar se iremos utilizar essa visualização
    # if False:
    # pedidos_feitos = pedidos_feitos.assign(
    #     Qt_Palete_Seco = "",
    #     Qt_Palete_CONG = "",
    #     Qt_Palete_DIVISÃO = "",
    #     TOTAL_Qt_Palete = "",
    # )
    
    st.divider()
    st.markdown("### :material/Route: Pedidos por Rota")
    
    # Filtra rotas numeradas e a sem rota
    rotas_numeradas = sorted([r for r in pedidos_todos["ROTA"].unique() if r != "SEM ROTA"])
    tem_sem_rota = "SEM ROTA" in pedidos_feitos["ROTA"].unique()

    # Exibe rotas numeradas em 2 colunas
    col_rota1, col_rota2 = st.columns(2)
    for idx, rota in enumerate(rotas_numeradas):
        target_col = col_rota1 if idx % 2 == 0 else col_rota2
        with target_col:
            df_rota = pedidos_feitos[pedidos_feitos["ROTA"] == rota].copy()
            st.markdown(f"#### :material/Route: {rota}")
            if not df_rota.empty:
                st.dataframe(df_rota, width="stretch", hide_index=True)
            else:
                st.info("Nenhum pedido para essa rota")
                st.space()
    # Exibe SEM ROTA no final
    if tem_sem_rota:
        st.divider()
        df_sem_rota = pedidos_feitos[pedidos_feitos["ROTA"] == "SEM ROTA"].copy()
        st.markdown(f"#### :material/Close: SEM ROTA")
        st.dataframe(df_sem_rota, width="stretch", hide_index=True)

else:
    st.info("Informe uma data para consulta")

st.divider()