import streamlit as st
import pandas as pd
import numpy as np
import re
import io
import requests
from bancoDados import inicia_conexao_bancoDados, obter_lojas
from utils import carregar_dados_onedrive, abrir_arquivo_txt, validar_acesso

if 'perfil' not in st.session_state:
    st.session_state.perfil = 'none'


validar_acesso(['administrador', 'usuario'])

def trata_df(resposta, df_produtos):    # irá mesclear a resposta da funçaõ distribuir_estoque com as demais descrições

    df_lista = []
    for filial, dados in resposta.items():
        temp_df = dados.copy()
        temp_df['filial'] = filial
        df_lista.append(temp_df)
    
    df_completo = pd.concat(df_lista, ignore_index=True)
    
    df_pivot = df_completo.pivot(index='CodProduto', columns='filial', values='Qt Cx')
    df_pivot['Total Distribuído'] = df_pivot.sum(axis=1)

    df_pivot = df_pivot.reset_index()
    df_produtos = df_produtos[['CodProduto', 'Descricao', 'TIPO','Estoq', 'Fornecedor']]
    
    df_merge = df_produtos.merge(df_pivot, on='CodProduto', how='inner')


    return df_merge
def distribuir_estoque_df(df_divisao, df_loja):

    lista_resultados = []
    
    for _, prod in df_divisao.iterrows():
        total_caixas = prod['Qt Cx']
        cod_prod = prod['CodProduto']
        erro_acumulado = 0.0
        
        for _, loja in df_loja.iterrows():
            nome_loja = loja['filial']
            cod_empresa = loja['cod_empresa']
            cod_nome_loja = nome_loja+'_'+cod_empresa

            fator = loja['fator_porcentagem'] / 100
            
            valor_ideal = (total_caixas * fator) + erro_acumulado            
            valor_inteiro = round(valor_ideal)
            erro_acumulado = valor_ideal - valor_inteiro
            
            # Armazena em formato de lista simples para criar o DataFrame
            lista_resultados.append({
                'CodProduto': cod_prod,
                'Loja': cod_nome_loja,
                'Qt Cx': valor_inteiro
            })    
    df_final = pd.DataFrame(lista_resultados)

    
    # Transforma o DataFrame: Linhas viram Produtos, Colunas viram Lojas
    df_pivoted = df_final.pivot(index='CodProduto', columns='Loja', values='Qt Cx')

    # df_pivoted = df_final.pivot(index='CodProduto', columns=['Loja','CodLoja'], values='Qt Cx')
    df_pivoted['Total Distribuído'] = df_pivoted.sum(axis=1)

    # Opcional: Remove o nome da coluna de índice para ficar mais limpo
    df_pivoted.columns.name = None
    df_pivoted = df_divisao[['CodProduto','Descricao','TIPO','Fator Conversao']].merge(df_pivoted,on='CodProduto')
    
    return df_pivoted

def extrai_qt_TXT(df):
    colunas_fixas = ['cod_empresa','CodProduto', 'Fator Conversao', 'Total Distribuído']
    df["CodProduto"] = df["CodProduto"].astype(str).str.rjust(13)

    colunas_qt = [c for c in df.columns if c not in colunas_fixas]
    saida = {}

    for col in colunas_qt:
            
            if df[col].sum()==0:
                continue
            
            nome_qt_txt = f"Qt_TXT_{col}"
            qt_convertida = df[col] * df["Fator Conversao"]

            df[nome_qt_txt] = qt_convertida.apply(lambda x: f"{x:09.3f}".replace(".", ","))

            # saida[col] = df[["CodProduto", nome_qt_txt]]
            saida[col] = df[["CodProduto", nome_qt_txt]].rename(columns={"CodProduto": "Codigo", nome_qt_txt: "Valor"})

    return saida

supabase = inicia_conexao_bancoDados()
todas_lojas = obter_lojas(supabase)

if not todas_lojas['status']:
    st.markdown('# :material/Close: Nâo é possível acessar as lojas')
    st.error('Contacte suporte técnico')
    st.stop()


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

st.title(":material/Universal_Currency_Alt: LANÇA :red[DIVISÃO]")

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
    

    st.markdown('## Lojas')
    df_lojas = pd.DataFrame(todas_lojas['resposta'])
    df_lojas = df_lojas.drop(columns='id')
    fator_porcentagem_total = df_lojas['fator_porcentagem'].sum()

    if fator_porcentagem_total!=100.00:
        st.error(f'Fator de porcentagem atual: {fator_porcentagem_total}, esperado 100%')
        if st.button('Corrigir'):
            st.switch_page('Home.py')
        st.stop()

    df_lojas = df_lojas[~df_lojas['grupo'].isin(['atacado','teste'])]
    df_lojas_fatorZero = df_lojas[df_lojas['fator_porcentagem']<=0]

    
    if not df_lojas_fatorZero.empty:
        st.info(f'Há {len(df_lojas_fatorZero)} lojas sem fator de conversão (zerado)')
        with st.expander('Mostrar lojas fator zerado'):
            df_lojas_fatorZero
    with st.expander('Mostrar lojas'):
        df_lojas

    st.divider()
    st.markdown('## Selecione os Produtos para Divisão')
    with st.expander('Todos os produtos',expanded=True):
        grid_divisao = st.dataframe(
            df[["CodProduto", "Descricao", "Fornecedor", "TIPO", 'Estoq']],
            selection_mode="multi-row",
            on_select='rerun',
        )

        itens_divisao = grid_divisao['selection']['rows']
        df_divisao = df.iloc[itens_divisao]

    if df_divisao.empty:
        st.error('Selecione ao menos 1 item para divisão')
        st.stop()

    
    df_divisao = df_divisao[['CodProduto', 'Descricao', 'Estoq', 'Fornecedor', 'TIPO', 'Qt Cx', 'Fator Conversao']]

    st.divider()
    st.markdown('## Informe Quantidade de Caixa')
    df_editado = st.data_editor(
        df_divisao[['CodProduto', 'Descricao', 'Fornecedor', 'TIPO', 'Estoq',"Fator Conversao", "Qt Cx"]],
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


    if (df_editado['Qt Cx'] == 0).any():
        st.info('Preencher a "Qt Cx" de TODOS dos produtos selecionados')
        st.stop()

    st.divider()
    with st.expander('Conferir Divisão'):
        st.markdown("# Divisão Todas Lojas (Qt Cx)")
        resposta = distribuir_estoque_df(df_editado,df_lojas)
        resposta

        df_cong = resposta[resposta['TIPO'].isin(['CONG','REFR'])].copy()
        df_peso = resposta[resposta['TIPO'] == 'PESO'].copy()
        df_seco = resposta[resposta['TIPO'] == 'SECO']
        
        st.markdown('### Separado por Grupo')
        st.write('SECO')
        df_seco
        st.write('CONGELADO/REFRIGERADO')
        df_cong
        st.write('PESO')
        if df_peso.empty:
            st.info('Nenhum item PESO selecionado')
        else:
            df_peso

    df_peso = df_peso.drop(columns=['TIPO','Descricao'])
    df_seco = df_seco.drop(columns=['TIPO','Descricao'])
    df_cong = df_cong.drop(columns=['TIPO','Descricao'])

    df_txt_seco = extrai_qt_TXT(df_seco)
    df_txt_cong = extrai_qt_TXT(df_cong)
    df_txt_peso = extrai_qt_TXT(df_peso)

    st.divider()
    st.markdown("# DIVISÃO TXT", text_alignment='center')
    col_txt_seco, col_txt_cong, col_txt_peso = st.columns(3, gap='medium')

    output = io.StringIO()
    with col_txt_seco:

        st.markdown('### :blue[SECO]', text_alignment='center')
        for loja in df_txt_seco.keys():
            df_txt_seco[loja].to_csv(output, sep="\t", index=False, header=False)
            
            secoCol1, secoCol2 = st.columns(2, vertical_alignment='center')
            secoCol1.markdown(loja.split('_')[0])
            

            secoCol2.download_button(
            label=f":material/Download: Baixar",
            data=output.getvalue(),
            file_name=f"{loja}_SECO.txt",
            mime="text/plain",
            key=f'SECO_{loja}'
            )
    output = io.StringIO()
    with col_txt_cong:
        st.markdown('### :blue[CONGELADO/REFRIGERADO]', text_alignment='center')
        for loja in df_txt_cong.keys():
            df_txt_cong[loja].to_csv(output, sep="\t", index=False, header=False)
            
            congCol1, congCol2 = st.columns(2, vertical_alignment='center')
            congCol1.markdown(loja.split('_')[0])

            congCol2.download_button(
            label=f":material/Download: Baixar",
            data=output.getvalue(),
            file_name=f"{loja}_CONG.txt",
            mime="text/plain",
            key=f'CONG_{loja}'
            )
    output = io.StringIO()
    with col_txt_peso:
        st.markdown('### :blue[PESO]', text_alignment='center')
        for loja in df_txt_peso.keys():
            df_txt_cong[loja].to_csv(output, sep="\t", index=False, header=False)

            pesoCol1, pesoCol2 = st.columns(2, vertical_alignment='center')
            pesoCol1.markdown(loja.split('_')[0])

            pesoCol2.download_button(
            label=f":material/Download: Baixar",
            data=output.getvalue(),
            file_name=f"{loja}_PESO.txt",
            mime="text/plain",
            key=f'PESO_{loja}',
            )

    st.divider()    
else:
    st.info("Insira _'00001produto.txt'_ e _'00001produtoextra.txt'_ para começar a edição")

#   --- SIDEBAR
with st.sidebar:
    st.write(f"Produtos cadastrados: :blue[{produtos_cadastrados}]")
