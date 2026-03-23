import streamlit as st
import pandas as pd
import re
import io
import requests

# --- FUNÇÕES E DEFINIÇÕES
def abrir_arquivo_txt(arquivo, colunas=None):
    try:
        if isinstance(arquivo, str):
            arquivo = io.StringIO(arquivo)
        return pd.read_csv(arquivo, sep="|", header=None, names=colunas, encoding="latin1")
    except Exception as e:
        st.error(f"Erro ao ler arquivo {e}")
        st.stop()
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

COLUNAS_PRODUTOS = ["CodProduto", "CodGrupo", "Descricao", "SiglaUn", "MinVenda", "PrecoUnPd", "CodPrincProd", "Estoq", "Obs", "Grade", "Falta", "Novo", "Prom", "DescMax", "Fam"]
COLUNAS_PRODUTOS_EXTRA = ["CodProduto", "Fam", "ListaCodCaract", "DescComplementar"]
GRUPO = ["SECO", "CONG", "REFR" , "PESO"]
FORNECEDORES = marcas = [
    "ATALAIA",
    "AYMORE",
    "BELINHO",
    "CIDINHA",
    "DONDON",
    "ELMA CHIPS",
    "FINI",
    "FRUTTBOM",
    "FUGINI",
    "HELLMANNS",
    "ITAMBE",
    "KIBON",
    "LOBITS",
    "MAMMA DALVA",
    "MAMMAMIA",
    "MARICOTA",
    "MAVI",
    "MINAS MAIS",
    "NESTLE",
    "NINHO",
    "PALHA LEVE",
    "PERDIGAO",
    "PORTO ALEGRE",
    "PULSI",
    "RENATA",
    "SADIA",
    "SEARA",
    "TREVO",
    "UAI",
    "UNIBABY",
    "YPE"
]
link_produto = st.secrets["onedrive"]["links"]["produto"]
link_produto_extra = st.secrets["onedrive"]["links"]["produto_extra"]
desativa_manual = False
produtos_cadastrados = 0

# --- CONF PAGINA
st.set_page_config(
    page_title="Fazer Pedidos",
    layout="wide")

st.title(":material/Universal_Currency_Alt: Criar :red[Pedidos]")

# --- LAYOUT PAGINA
bd_automatico = st.toggle("Deseja pegar arquivos automaticamente?", value=True)
if bd_automatico:
    f_produto_auto = carregar_dados_onedrive(link_produto)
    f_extra_auto = carregar_dados_onedrive(link_produto_extra)
    desativa_manual = True
col1, col2, col3 = st.columns(3)
with col1:
    f_produto = st.file_uploader(":material/Barcode: Arquivo 00001produto.txt", disabled=desativa_manual, type="txt")
with col2:
    f_extra = st.file_uploader(":material/Add: Arquivo 00001produtoextra.txt", disabled=desativa_manual, type="txt")
with col3:
    f_cod_filtro = st.file_uploader(":material/Add: Arquivo TXT para :blue[FILTRO]", type="txt")
if f_cod_filtro:
    st.info("Filtro Ativado")
#if False:
c1, c2 = st.columns(2)
with c1:
    st.markdown("### :material/Toggle_On: Excessões: O que retirar da lista")
    ind_div = st.checkbox("[:material/Safety_Divider:]  Divisão")
with c2:
    st.markdown("### :material/Toggle_On: Filtro")
    ind_grupo = st.pills(":material/Group_Work: Grupo", options=GRUPO, selection_mode="multi",default=GRUPO)
st.divider()


if (f_produto and f_extra) or desativa_manual:

    if desativa_manual:
        df = abrir_arquivo_txt(f_produto_auto, COLUNAS_PRODUTOS)
        df_extra = abrir_arquivo_txt(f_extra_auto, COLUNAS_PRODUTOS_EXTRA)
    else:
        if f_produto.name != "00001produto.txt":
            st.error(":material/Close: 00001produto.txt erro ao carregar")
            st.stop()
        if f_extra.name != "00001produtoextra.txt":
            st.error(":material/Close: 00001produtoextra.txt erro ao carregar")
            st.stop()
        df = abrir_arquivo_txt(f_produto, COLUNAS_PRODUTOS)
        df_extra = abrir_arquivo_txt(f_extra, COLUNAS_PRODUTOS_EXTRA)
    
    if f_cod_filtro:
        conteudo = f_cod_filtro.read().decode("utf-8").split()
        df = df[df["CodProduto"].isin(conteudo)]

    
    produtos_cadastrados = len(df)
    df = df.merge(df_extra[["CodProduto", "ListaCodCaract"]], on="CodProduto", how="left")
    df = df[['CodProduto', 'CodGrupo', 'Descricao', 'Estoq', 'Fam', 'ListaCodCaract']]

    #Cria coluna de fornecedores
    padrao = "|".join(FORNECEDORES)
    df["Fornecedor"] = df["Descricao"].str.extract(f"({padrao})", flags=re.IGNORECASE, expand=False)
    df["Fornecedor"] = df["Fornecedor"].fillna("Outros")
    
    df["TIPO"] = "SECO"
    df.loc[df["CodGrupo"].isin([9]), "TIPO"] = "CONG"
    df.loc[df["CodGrupo"].isin([14]), "TIPO"] = "REFR"
    df.loc[df["ListaCodCaract"].astype(str).str.contains("000002"), "TIPO"] = "PESO"
    
    #   2. FILTRO DATAFRAME
    df = df[df["Estoq"] > 0].copy()
    #filtro divisão
    if ind_div:
        df = df[df["Fam"] != 900000008].copy()
    #filtro grupo
    df = df[df["TIPO"].isin(ind_grupo)].copy()

    #   --- MOSTRAR INFORMAÇÕES
    if df.empty:
        st.error(":material/Cancel: Nenhum Produto selecionado")
        st.stop()

    df["Qt Cx"] = 0

    df["Fator Conversao"] = df["Descricao"].astype(str).str.split()
    df["Fator Conversao"] = df["Fator Conversao"].str[-1]
    df["Fator Conversao"] = pd.to_numeric(df["Fator Conversao"],errors="coerce").fillna(1)
    
    df_editado = st.data_editor(
        df[['CodProduto', 'Descricao', 'Fornecedor', 'TIPO', 'Estoq',"Fator Conversao", "Qt Cx"]],
        hide_index=True,
        column_config={
            "Qt Cx": st.column_config.NumberColumn(
                "Qt Cx",
                help="Digite a quantidade desejada",
                min_value=0,
                max_value=10_000,
                step=10,
                format="%d",
            ),
            "CodProduto": st.column_config.Column(disabled=True),
            "Descricao": st.column_config.Column(disabled=True),
            "Fornecedor": st.column_config.Column(disabled=True),
            "TIPO": st.column_config.Column(disabled=True),
            "Estoq": st.column_config.Column(disabled=True),
            "Fator Conversao": st.column_config.Column(disabled=True),
        },
        width="stretch",
    )
    st.divider()
    st.markdown("# Pedido")
    df_editado = df_editado[df_editado["Qt Cx"] > 0]
    if df_editado.empty:
        st.info("Selecione a quantidade na coluna 'Qt Cx'")
        st.stop()

    df_editado["Qt TXT"] = df_editado["Qt Cx"] * df_editado["Fator Conversao"]
    df_editado["Codigo"] = df_editado["CodProduto"].astype(str).str.rjust(13)

    df_editado["VALOR_STR"] = df_editado["Qt TXT"].apply(lambda x: f"{x:09.3f}".replace(".", ","))

    st.dataframe(df_editado[["CodProduto", "Descricao", "Fornecedor", "TIPO", "Estoq", "Fator Conversao"]])
    df_editado = df_editado[["Codigo", "VALOR_STR"]]

    output = io.StringIO()
    df_editado.to_csv(output, sep="\t", index=False, header=False)

    st.download_button(
    label=f":material/Download: Baixar Pedido",
    data=output.getvalue(),
    file_name=f"PedidoTeste.txt",
    mime="text/plain"
    )
  

else:
    st.info("Insira _'00001produto.txt'_ e _'00001produtoextra.txt'_ para começar a edição")

#   --- SIDEBAR
with st.sidebar:
    with st.expander("Link para arquivo .txt"):
        st.subheader("Link para produto.txt:")
        st.link_button("Clique aqui", link_produto)

        st.subheader("Link para produtoextra.txt:")
        st.link_button("Clique aqui", link_produto_extra)
    st.write(f"Produtos cadastrados: :blue[{produtos_cadastrados}]")
