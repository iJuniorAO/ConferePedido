import streamlit as st
import pandas as pd
import numpy as np
import io
import re
from rapidfuzz import process, fuzz

#   MELHORIAS
#       Mudar index e corrigir para ser igual arquivo txt
#       # Status de carregamento - mostrar carregando e concluído quando importar txt base dados
#       Lista > Importar produto.txt e criar criar lista no aplicativo
#       Importação de Pedidos > Importação automática do arquivo txt
#       Importação de Pedidos > Processamento concluído somente mostrar após botão do download aparecer
#       Importação de Pedidos > Mostrar qt de linhas que foi puxado
#       Importação de Pedidos > Mostrar qt de linhas com erro na qtde
#       Importação de Pedidos > Botão > Usar IA para tentar corrigir descrição com valores mostraods
#       Informar qt linhas no pedido q qt linhas finais
#       st.sucess caso não ocorra nenhum erro


if not st.session_state["roles"] in ["administrador", "usuario"]:
    st.markdown("# :material/block: Acesso Negado")
    st.stop()


# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Conversor de Pedidos",
    layout="wide")

# --- FUNÇÕES DE PROCESSAMENTO (Adaptadas do seu arquivo original) ---
def abrir_txt_st(uploaded_file, colunas):
    """Lê o arquivo carregado no Streamlit."""
    try:
        return pd.read_csv(uploaded_file, sep="|", header=None, names=colunas, encoding="latin1")
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
        return None
def procuranumero(linha):
    linha = linha.strip()
    partes = linha.split()
    if not partes:
        return None
    codigo_cru = partes.pop(0)

    if re.search(r"\d", codigo_cru):
        match = re.match(r"(\d+)(.*)", codigo_cru)
        if match:
            numero = match.group(1)
            resto_texto = match.group(2)
            if resto_texto:
                partes.insert(0, resto_texto)
            partes.insert(0, numero)
            return " ".join(partes)
    return None
def limpa_df(uploaded_file):
    # Lê as linhas do arquivo
    conteudo = uploaded_file.read().decode("utf-8")
    linhas = conteudo.splitlines()
    
    linhas_novas = []
    alteracoes_feitas = 0
    erros_nao_corrigidos = []
    linhas_removidas = 0


    # Processamento
    for i, linha in enumerate(linhas):
        num_l = i + 1

        if linha.strip() == "":
            linhas_removidas += 1
            continue
        
        #Retira linhas em branco extra
        if linha.strip() != linha:
            linha = linha.strip()
       
        # Tenta corrigir se o código (1ª coluna) não for número
        colunas = linha.split()
        if len(colunas) >= 1 and not colunas[0].isdigit():
            sugestao = procuranumero(linha)
            if sugestao:
                linhas_novas.append(sugestao)
                alteracoes_feitas += 1
            else:
                linhas_novas.append(linha)
                erros_nao_corrigidos.append(f"Linha {num_l}: Sem correção automática:  \n{linha}.")
        else:
            linhas_novas.append(linha)
        texto_corrigido = "\n".join(linhas_novas)
    return io.StringIO(texto_corrigido)
def importa_pedido_loja_st(uploaded_file, colunas_Pedidos):
    """Prepara o pedido da loja a partir do arquivo enviado[cite: 2, 10]."""
    df_Import_loja = pd.read_csv(uploaded_file, sep="|", header=None, encoding="latin1")
    Linhas_Pedidos = len(df_Import_loja)
    
    # Prepara o df separando a primeira coluna [cite: 2]
    df_Import_loja[colunas_Pedidos] = (
        df_Import_loja[0]
        .astype(str)
        .str.split(" ", n=2, expand=True)
    )
    df_Import_loja = df_Import_loja.drop(columns=[0]) # Removido 'Sigla' do drop pois ela é criada no split

    # Separa erros de quantidade [cite: 10]
    num = pd.to_numeric(df_Import_loja["QtCx"], errors="coerce")
    df_ok = df_Import_loja[num.notna()].copy()
    df_erro = df_Import_loja[num.isna()].copy()
    df_ok["QtCx"] = df_ok["QtCx"].astype(float)
    
    return df_ok, df_erro, Linhas_Pedidos
# 1. Função para encontrar o melhor match
def encontra_melhor_match(descricao_erro, escolhas_base, threshold=60):

    # extractOne retorna (string_encontrada, score, index)
    match = process.extractOne(descricao_erro, escolhas_base, scorer=fuzz.token_set_ratio)

    if match and match[1] >= threshold:
        return pd.Series([match[0], match[1]], index=['Descricao_Sugerida', 'Score_Similaridade'])
    return pd.Series([None, 0], index=['Descricao_Sugerida', 'Score_Similaridade'])

# Definição de colunas conforme o código original [cite: 4]
colunas_produto = ["CodProduto", "CodGrupo", "Descricao", "SiglaUn", "MinVenda", "PrecoUnPd", "CodPrincProd", "Estoq", "Obs", "Grade", "Falta", "Novo", "Prom", "DescMax", "Fam"]
colunas_produto_extra = ["CodProduto", "Fam", "ListaCodCaract", "DescComplementar"]
colunas_Pedidos = ["QtCx", "Sigla", "Descricao"]
Linhas_Pedidos = 0
# --- INTERFACE STREAMLIT ---
st.title("💾 Conversor de Pedidos para Importação")

#Tabs para base de dados e importação pedidos
tab1,tab2 = st.tabs(["📦 Base de Dados","📝 Importação de Pedidos"])
# 1. UPLOAD DE ARQUIVOS (Substitui os caminhos C:\...) [cite: 5]
with tab1:
    st.header("Upload de Bases de Dados")
    #Btm com link para baixar produto.txt e produtoextra.txt
    st.subheader("Link para txt atualizado:")
    st.link_button("Clique aqui",
                   r"https://mumulaticinios-my.sharepoint.com/my?id=%2Fpersonal%2Fanalista%5Fadm%5Fmumix%5Fcom%5Fbr%2FDocuments%2FBaseDados%2FNOVO&ga=1"
                   )
    #col1, col2, col3 = st.columns(3)
    col1, col2 = st.columns(2)
    with col1:
        f_produto = st.file_uploader("📦 Arquivo 00001produto.txt", type="txt")
    with col2:
        f_extra = st.file_uploader("➕ Arquivo 00001produtoextra.txt", type="txt")
#2. UPLOAD DE ARQUIVOS PEDIDO
with tab2:
    tabela1 = st.columns([0.2, 0.6, 0.2])
    with tabela1[1]:
        st.header("Upload de Pedidos da Loja")
        f_pedido = st.file_uploader("📝 Pedido da Loja (.txt)", type="txt")

if f_produto and f_extra and f_pedido:
    # --- PROCESSAMENTO ---
    with st.status("Processando dados...", expanded=True) as status:
        # Carregamento
        df = abrir_txt_st(f_produto, colunas_produto)
        df_extra = abrir_txt_st(f_extra, colunas_produto_extra)

        # Filtros iniciais
        df = df[["CodProduto", "CodGrupo", "Descricao", "Estoq", "Fam"]]
        df = df[(df["Fam"] != 900000008) & (df["Estoq"] > 0)]

        # Merge Produto + Extra
        df = df.merge(df_extra[["CodProduto", "ListaCodCaract"]], on="CodProduto", how="left")

        # Regra de TIPO
        df["TIPO"] = "SECO"
        df.loc[df["CodGrupo"].isin([9, 14]), "TIPO"] = "CONG"
        df.loc[df["ListaCodCaract"].astype(str).str.contains("000002"), "TIPO"] = "PESO"

        # Fator de conversão
        ultimo = df["Descricao"].astype(str).str.split().str[-1]
        df["CONV"] = np.where(ultimo.str.isdigit(), ultimo, 1).astype(float)

        # Padroniza código
        df_Produto_Base = df.copy()
        df_Produto_Base.insert(0, "Codigo", df_Produto_Base["CodProduto"].astype(str).str.rjust(13))
        df_Produto_Base = df_Produto_Base[["Codigo", "Descricao", "TIPO", "CONV"]]
        # Importa Pedido da Loja
        f_pedido = limpa_df(f_pedido)
        df_Pedido_Loja, df_Erro_Qt, Linhas_Pedidos = importa_pedido_loja_st(f_pedido, colunas_Pedidos)
        
        # Procv Pedido_loja com 0001produto
        df_Pedido_Final = df_Produto_Base.merge(
            df_Pedido_Loja[["QtCx", "Descricao"]],
            on="Descricao",
            how="outer",
            indicator=True
        )

        df_Erro_Desc = df_Pedido_Final[df_Pedido_Final["_merge"] == "right_only"]
        
        # Cálculo final 
        df_Pedido_Final = df_Pedido_Final[df_Pedido_Final["QtCx"].notna()].copy()
        df_Pedido_Final["TOTAL"] = df_Pedido_Final["QtCx"] * df_Pedido_Final["CONV"]

        # Formatação numérica (00000,000) 
        df_Pedido_Final["VALOR_STR"] = df_Pedido_Final["TOTAL"].map(
            lambda x: f"{x:09.3f}".replace(".", ",") if isinstance(x, (int, float)) else "00000,000"
        )

        st.write(f"Foram importados: {Linhas_Pedidos} linhas")

        # --- EXIBIÇÃO DE ERROS ---
        if not df_Erro_Qt.empty or not df_Erro_Desc.empty:
            if not df_Erro_Desc.empty:
                st.toast("Houve erro de importação",icon="❌")
            with st.expander("⚠️ Ver Erros de Importação"):
                if not df_Erro_Qt.empty:
                    st.warning(f"[{len(df_Erro_Qt)}] Linhas com erro na quantidade:")
                    st.dataframe(df_Erro_Qt)
                if not df_Erro_Desc.empty:
                    st.error(f"[{len(df_Erro_Desc)}] Itens não encontrados na base de produtos:")
                    #st.dataframe(df_Erro_Desc[['Codigo', "QtCx",'Descricao']])
        

        
                # Lista de descrições únicas da base para comparar
                lista_base = df_Produto_Base['Descricao'].tolist()
                # Aplicamos a função no df_Erro_Desc
                matches = df_Erro_Desc['Descricao'].apply(lambda x: encontra_melhor_match(x, lista_base))
                # 3. Concatenando os resultados para validação

                df_validacao = pd.concat([df_Erro_Desc, matches], axis=1)
                # 4. Trazer as outras colunas do df_Produto_Base baseada na sugestão
                df_final = df_validacao.merge(
                    df_Produto_Base[['Descricao', 'Codigo', 'TIPO', 'CONV']], 
                    left_on='Descricao_Sugerida', 
                    right_on='Descricao', 
                    how='left',
                    suffixes=('_Erro', '_Base')
                )

                st.write(f"Encontrados Automaticamente: {df_validacao["Descricao_Sugerida"].notna().sum()}/{df_validacao["Descricao"].notna().sum()} itens")
                st.write("Selecione as alterações corretas:")

                # Ordenar pelos scores mais baixos primeiro para o usuário focar no que é duvidoso
                #df_final = df_final.sort_values(by='Score_Similaridade', ascending=False)

                df_validacao = df_validacao.sort_values(by="Score_Similaridade", ascending=False)

                validacao_dic = st.dataframe(df_validacao[['QtCx', 'Descricao', 'Descricao_Sugerida', 'Score_Similaridade']],
                            selection_mode="multi-row",
                            on_select="rerun",
                            #hide_index=True
                            )

                aplicar_correcao = st.toggle("Usar correções automáticas")

                if aplicar_correcao:
                    ind_aprovados = validacao_dic["selection"]["rows"]

                    df_corrigido = df_validacao.iloc[ind_aprovados].copy()

                    #pegar o df_corrigido e realizar merge junto ao df_pedido para criar um novo df_pedido
                    #importado 20 sem a correção esperado 22
                    #O que é VALOR_STR em df_Pedido_Final??
                    #!!!!

                    #Troca valores de df_corrigido para df_Pedido_Final
                    # 1. Criar um dicionário de mapeamento: { 'Valor Antigo': 'Valor Novo' }
                    mapeamento = dict(zip(df_corrigido['Descricao'], df_corrigido['Descricao_Sugerida']))
                    # 2. Aplicar a substituição na coluna original
                    df_Pedido_Rev = df_Pedido_Loja.copy()
                    df_Pedido_Rev['Descricao'] = df_Pedido_Rev['Descricao'].replace(mapeamento)

                    # Procv Pedido_loja_Final_Rev com 0001produto
                    df_Pedido_Final_Rev = df_Produto_Base.merge(
                        df_Pedido_Rev[["QtCx", "Descricao"]],
                        on="Descricao",
                        how="outer",
                        indicator=True
                    )

                    df_Erro_Desc = df_Pedido_Final[df_Pedido_Final["_merge"] == "right_only"]
                    
                    # Cálculo final 
                    df_Pedido_Final_Rev = df_Pedido_Final_Rev[df_Pedido_Final_Rev["QtCx"].notna()].copy()
                    df_Pedido_Final_Rev["TOTAL"] = df_Pedido_Final_Rev["QtCx"] * df_Pedido_Final_Rev["CONV"]

                    # Formatação numérica (00000,000) 
                    df_Pedido_Final_Rev["VALOR_STR"] = df_Pedido_Final_Rev["TOTAL"].map(
                        lambda x: f"{x:09.3f}".replace(".", ",") if isinstance(x, (int, float)) else "00000,000"
                    )        
        else:
            st.success("Sem erro de exportação")
            st.toast("Todos itens importados",icon="✅")
    
    status.update(label="Processamento concluído!", state="complete")
    
    # --- DOWNLOADS ---
    #Dict com todos os valores prontos para importar para ERP
    Linhas_Pedidos_por_Tipo = df_Pedido_Final["TIPO"].value_counts().to_dict()

    #Se todas as linhas não foram importados gera erro
    if not Linhas_Pedidos_por_Tipo:
        st.error("ERRO NA IMPORTAÇÃO - Arquivo fora do padrão")
    #Não tem correções automáticas
    elif not aplicar_correcao:
        st.header("Baixar Pedidos Gerados")
        c1, c2, c3 = st.columns(3)
        tipos = [("SECO", c1), ("CONG", c2), ("PESO", c3)]
        
        for tipo, col in tipos:
            df_sub = df_Pedido_Final[df_Pedido_Final["TIPO"] == tipo][["Codigo", "VALOR_STR"]]
            with col:
                if not df_sub.empty:
                    st.success(f"[{len(df_sub)}] Pedido {tipo} pronto!")
                    # Gera o CSV em memória para download 
                    output = io.StringIO()
                    df_sub.to_csv(output, sep="\t", index=False, header=False)
                    
                    st.download_button(
                        label=f"📥 Baixar Pedido {tipo}",
                        data=output.getvalue(),
                        file_name=f"Pedido_{tipo}.txt",
                        mime="text/plain"
                    )
                else:
                    st.info(f"Sem itens para {tipo}")
    #Possui correções automáticas
    else:
        st.header("Baixar Pedidos Gerados - Correção Automática")
        c1, c2, c3 = st.columns(3)
        tipos = [("SECO", c1), ("CONG", c2), ("PESO", c3)]
        
        for tipo, col in tipos:
            df_sub = df_Pedido_Final_Rev[df_Pedido_Final_Rev["TIPO"] == tipo][["Codigo", "VALOR_STR"]]
            with col:
                if not df_sub.empty:
                    st.success(f"[{len(df_sub)}] Pedido {tipo} pronto!")
                    # Gera o CSV em memória para download 
                    output = io.StringIO()
                    df_sub.to_csv(output, sep="\t", index=False, header=False)
                    
                    st.download_button(
                        label=f"📥 Baixar Pedido {tipo}",
                        data=output.getvalue(),
                        file_name=f"Pedido_{tipo}.txt",
                        mime="text/plain"
                    )
                else:
                    st.info(f"Sem itens para {tipo}")

elif f_produto and f_extra and not f_pedido:
    erro = 0
    df = abrir_txt_st(f_produto,colunas_produto)
    df_extra = abrir_txt_st(f_extra,colunas_produto_extra)

    #Validação produto.txt
    if df["Estoq"].sum() == 0:
        st.error("❌ Erro ao carregar 00001produto.txt")
        erro = 1
    #Validação produtoextra.txt
    if df_extra["CodProduto"].notna().sum() == df_extra["Fam"].notna().sum():
        st.error("❌ Erro ao carregar 00001produtoextra.txt")
        erro = 1
    if erro == 0:
        st.warning("✅ Arquivos de Base carregados com sucesso.\n Aguardando o upload do pedido da loja para iniciar.")
else:
    st.info("⚠️ Aguardando o upload do arquivos iniciais para iniciar.")

st.sidebar.markdown("""
## Portal Pedidos
### Correções implementadas:

### Preparação:
1. Insere o arquivo produto.txt                    
2. Insere o arquivo produtoextra.txt

### Processo de Conversão:
1. Importa o pedido da loja
2. Verifica ERROS - Qt de cx
3. Verifica ERROS - Descrição e Fator Conversão
""")