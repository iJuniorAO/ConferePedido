import streamlit as st
import pandas as pd
import re
import io
import requests
import numpy as np

# --- FUNÇÕES E DEFINIÇÕES
def abrir_arquivo_txt(arquivo, colunas=None):
    try:
        if isinstance(arquivo, str):
            arquivo = io.StringIO(arquivo)
        return pd.read_csv(arquivo, sep="|", header=None, names=colunas, encoding="latin1")
    except Exception as e:
        st.error(f"Erro ao ler arquivo {e}")
        st.stop()
@st.cache_data(ttl=7200, show_spinner=True)
def carregar_dados_onedrive(input_texto):
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
COLUNAS_PRODUTOS_PRECO = ["Tabela", "CodProduto", "Preco"]
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
link_tabela_preco = st.secrets["onedrive"]["links"]["tabela_preco"]
desativa_manual = False
produtos_cadastrados = 0
habilita_preco_cx = False


# --- CONF PAGINA
st.set_page_config(
    page_title="Lista Atacado",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.title(":material/Shopping_Cart: Tabela de Produtos para :red[Atacado]")

# --- LAYOUT PAGINA
bd_automatico = st.toggle("Deseja pegar arquivos automaticamente?",value=True)
if bd_automatico:
    f_produto_auto = carregar_dados_onedrive(link_produto)
    f_extra_auto = carregar_dados_onedrive(link_produto_extra)
    f_tabela_preco_auto = carregar_dados_onedrive(link_tabela_preco)
    desativa_manual = True
col1, col2, col3 = st.columns(3)
with col1:
    f_produto = st.file_uploader(":material/Barcode: Arquivo 00001produto.txt", disabled=desativa_manual, type="txt")
with col2:
    f_extra = st.file_uploader(":material/Add: Arquivo 00001produtoextra.txt", disabled=desativa_manual, type="txt")
with col3:
    f_tabela_preco = st.file_uploader(":material/Add: Arquivo 00001produtotabela.txt", disabled=desativa_manual, type="txt")

st.subheader(":material/Toggle_On: Excessões: O que retirar da lista")
c1, c2 = st.columns(2)
with c1:
    ind_neg = st.checkbox("[:material/Stat_Minus_1:]  Estoque Negativo", value=True)
    ind_div = st.checkbox("[:material/Safety_Divider:]  Divisão", value=True)
with c2:
    ind_grupo = st.pills(":material/Group_Work: Grupo", options=GRUPO, selection_mode="multi",default=GRUPO)
    ind_qtmin = st.number_input(":material/Numbers: Estoque Mínimo", value=None, placeholder="Digite um valor", step=10, )

# --- PROCESSAMENTO

if (f_produto and f_extra and f_tabela_preco) or desativa_manual:
    with st.status ("Processando dados...", expanded=True) as status:
        #   1. Inicialização
        if desativa_manual:
            df = abrir_arquivo_txt(f_produto_auto, COLUNAS_PRODUTOS)
            df_extra = abrir_arquivo_txt(f_extra_auto, COLUNAS_PRODUTOS_EXTRA)
            df_preco = abrir_arquivo_txt(f_tabela_preco_auto, COLUNAS_PRODUTOS_PRECO)
        else:
            if f_produto.name != "00001produto.txt":
                st.error(":material/Close: 00001produto.txt erro ao carregar")
                st.stop()
            if f_extra.name != "00001produtoextra.txt":
                st.error(":material/Close: 00001produtoextra.txt erro ao carregar")
                st.stop()
            if f_tabela_preco.name != "00001produtotabela.txt":
                st.error(":material/Close: 00001produtotabela.txt erro ao carregar")
                st.stop()
            df = abrir_arquivo_txt(f_produto, COLUNAS_PRODUTOS)
            df_extra = abrir_arquivo_txt(f_extra, COLUNAS_PRODUTOS_EXTRA)
            df_extra = abrir_arquivo_txt(f_extra, COLUNAS_PRODUTOS_EXTRA)
            df_preco = abrir_arquivo_txt(f_tabela_preco, COLUNAS_PRODUTOS_PRECO)
        
        produtos_cadastrados = len(df)
        # Merge Produto + Extra
        df_merge = df.merge(df_extra[["CodProduto", "ListaCodCaract"]], on="CodProduto", how="left")
        df_merge = df_merge[['CodProduto', 'CodGrupo', 'Descricao', 'Estoq', 'Fam', 'ListaCodCaract']]
       
        #df_preco = df_preco[df_preco["Tabela"] == "PRATI"]

        df_preco = df_preco.pivot(index='CodProduto', columns='Tabela', values='Preco')
        df_preco = df_preco.reset_index()

        df_completo = df_merge.merge(df_preco, on="CodProduto", how="left")
        df_completo = df_completo.rename(columns={"SUGER":"Lojas","PRATI":"Atacado"})

        #Cria coluna de fornecedores
        padrao = "|".join(FORNECEDORES)
        df_completo["Fornecedor"] = df_completo["Descricao"].str.extract(f"({padrao})", flags=re.IGNORECASE, expand=False)
        df_completo["Fornecedor"] = df_completo["Fornecedor"].fillna("Outros")
        
        df_completo["TIPO"] = "SECO"
        df_completo.loc[df_completo["CodGrupo"].isin([9]), "TIPO"] = "CONG"
        df_completo.loc[df_completo["CodGrupo"].isin([14]), "TIPO"] = "REFR"
        df_completo.loc[df_completo["ListaCodCaract"].astype(str).str.contains("000002"), "TIPO"] = "PESO"

        #   2. FILTRO DATAFRAME
        #filtro negativo
        if ind_neg:
            df_completo = df_completo[df_completo["Estoq"] > 0].copy()
        #filtro divisão
        if ind_div:
            df_completo = df_completo[df_completo["Fam"] != 900000008].copy()
        #filtro grupo
        df_completo = df_completo[df_completo["TIPO"].isin(ind_grupo)].copy()
        #filtro qt mínima estoque
        if ind_qtmin:
            df_completo = df_completo[df_completo["Estoq"] > ind_qtmin]

        #   --- MOSTRAR INFORMAÇÕES
        if df_completo.empty:
            st.error(":material/Cancel: Nenhum item selecionado")
            status.update(label="Processamento concluído!", state="complete")
            st.stop()
        
        st.write(f":material/Delete: Selecione os produtos que deseja remover da lista original: :red[{len(df_completo)} itens]")
        
        remover_linhas = st.dataframe(
            df_completo[['CodProduto', 'Descricao', 'Fornecedor', 'TIPO', 'Estoq']],
            hide_index=True,
            selection_mode="multi-row",
            on_select="rerun"
        )

        #Pega o dict e remove as linhas selecionadas
        ind_remover_linhas = remover_linhas["selection"]["rows"]
        df_removido = df_completo.drop(df_completo.index[ind_remover_linhas]).copy()


        df_removido = df_removido[['CodProduto', 'Descricao', 'Fornecedor', 'TIPO', 'Estoq', 'Lojas',"Atacado"]]
        df_removido = df_removido.sort_values(by=["Fornecedor"])

        if habilita_preco_cx:
            ultimo = df_removido["Descricao"].astype(str).str.split().str[-1]
            df_removido["CONV"] = np.where(ultimo.str.isdigit(), ultimo, 1).astype(float)

            df_removido["Venda"] = df_removido["CONV"] * df_removido["Lojas"]
        
        df_removido["Lojas"] = df_removido["Lojas"].map(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_removido["Atacado"] = df_removido["Atacado"].map(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        if habilita_preco_cx:
            df_removido["R$ Venda"] = df_removido["Venda"].map(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        if not df_removido.empty and len(df_removido) == len(df_completo):
            st.write(f":material/List: Total Itens na lista: :red[{len(df_removido)} itens]")
        elif df_removido.empty:
            st.write(f":material/List: :red[Nenhum item na lista]")
            st.stop()
        else:
            st.write(f":material/List: Total Itens na lista: :blue[{len(df_removido)} itens]")
 
        status.update(label="Processamento concluído!", state="complete")
    
    st.divider()
    st.markdown("## :material/Sell: Lista Atacado:")
    if habilita_preco_cx:
        st.dataframe(
            df_removido[["CodProduto", "Descricao", "R$/Un", "R$ Venda", "Fornecedor","Estoq"]].sort_values("Fornecedor"),
            hide_index=True,        
        )
    else:
        st.dataframe(
            df_removido[["CodProduto", "Descricao", "Lojas","Atacado", "Fornecedor","Estoq"]].sort_values("Fornecedor"),
            hide_index=True,        
        )

    st.divider()
    if st.toggle("Mostrar Preços com Atenção"):
        st.markdown("# Validar preço dos produtos abaixo")

        df_atencao = df_completo[["CodProduto", "Descricao", "Estoq", "Lojas", "Atacado","Fornecedor","TIPO"]].sort_values(by="CodProduto")
        df_atencao["Dif_Preco"] = df_atencao["Lojas"]-df_atencao["Atacado"]

        st.markdown("### Mesmo Preço - Lojas e Atacado")
        df_atencao_view = df_atencao[df_atencao["Dif_Preco"]==0].sort_values(by="Estoq",ascending=False)
        df_atencao_view


        st.markdown("### Preço Maior nas Lojas")
        df_atencao["Dif_Perc"] = (df_atencao["Dif_Preco"]/df_atencao["Lojas"])*100
        df_atencao_view = df_atencao[df_atencao["Dif_Preco"]>0].sort_values(by="Dif_Perc",ascending=False)
        df_atencao_view

        st.markdown("### Mais que 50% para Atacado")
        df_atencao_view = df_atencao[df_atencao["Dif_Perc"]<=-20].sort_values(by="Dif_Perc")
        df_atencao_view




else:
    st.info("Insira _'00001produto.txt'_ e _'00001produtoextra.txt'_ e _'00001produtotabela.txt'_ para começar a edição")

#   --- SIDEBAR
with st.sidebar:
    with st.expander("Link para arquivo .txt"):
        st.subheader("Link para produto.txt:")
        st.link_button("Clique aqui", link_produto)

        st.subheader("Link para produtoextra.txt:")
        st.link_button("Clique aqui", link_produto_extra)
    st.write(f"Produtos cadastrados: :blue[{produtos_cadastrados}]")
