import streamlit as st
import xmltodict
import re
import pandas as pd

#       pegar nr nf
#       pegar fornecedor

def processa_XML(xml_file):
    # Transforma o XML em um dicionário Python
    data = xmltodict.parse(xml_file)

    detalhes = data['nfeProc']['NFe']['infNFe']['det']
    if not isinstance(detalhes, list):
        detalhes = [detalhes]
    
    emitente_nome = data['nfeProc']['NFe']['infNFe']["emit"]["xNome"]


    if "xFant" in data['nfeProc']['NFe']['infNFe']["emit"]:
        emitente_fantasia = data['nfeProc']['NFe']['infNFe']["emit"]["xFant"]
    else:
        emitente_fantasia=""

    nr_Nfe = data['nfeProc']['NFe']['infNFe']["ide"]["nNF"]
      
        
    total_nf_xml = float(data['nfeProc']['NFe']['infNFe']['total']['ICMSTot']['vNF'])
    
    lista_produtos = []
    soma_produtos = 0

    for id, item in enumerate(detalhes):

        cod_produto = item["prod"]["cProd"]
        imposto = item['imposto']
        Item = detalhes[id]["@nItem"]
        descricao = item['prod']['xProd']
        qt_Com = float(item['prod']['qCom'])
        Ucom = item['prod']['uCom'].lower()
        valor_produto = float(item['prod']['vProd'])
        if "CEST" in item["prod"]:
            cod_CEST = item["prod"]["CEST"]
        else:
            cod_CEST=""
        if "IPI" in item["imposto"]:
            if "IPITrib" in item["imposto"]["IPI"]:
                valor_IPI = float(item["imposto"]["IPI"]["IPITrib"]["vIPI"])
            else:
                valor_IPI = 0
        else:
            valor_IPI=0

        soma_produtos += valor_produto
        
        #   OTIMIZAR
        icms_info = imposto['ICMS']
        tipo_icms = list(icms_info.keys())[0] # Ex: 'ICMS60'
        cst = icms_info[tipo_icms].get('CST', icms_info[tipo_icms].get('orig', ''))
        v_st = float(icms_info[tipo_icms].get('vICMSST', 0))
        
        lista_produtos.append({
            "Item": Item,
            "Codigo Fornecedor": cod_produto,
            "Descrição": descricao,
            "Ucom": Ucom,
            "qt_Com": qt_Com,
            "Valor Original": valor_produto,
            "CST": cst,
            "CEST": cod_CEST,
            "V_ST": v_st,
            "V_IPI": valor_IPI
        })

    return pd.DataFrame(lista_produtos), total_nf_xml, soma_produtos, emitente_nome, emitente_fantasia, nr_Nfe
def extrair_inteiro_unidade(texto_unidade):
    numeros = re.findall(r'\d+', str(texto_unidade))
    if numeros:
        return int("".join(numeros))
    return 1 # Retorna 1 se for apenas 'un' ou 'cx' sem número
def input_fator_conversao(df):
    fator_conversao = df[["Descrição"]].copy()
    fator_conversao["Fator de Conversão"] = 0
    fator_conversao = st.data_editor(
        fator_conversao,
        width="stretch",
        hide_index=True,
        num_rows="dynamic"
    )
    if 0 in fator_conversao.values:
        st.error("Não pode haver fator de conversão 'Zero', caso não tenha mude para '1'")
        st.stop()
    if len(df) != len(fator_conversao):
        st.error("Qt de conversões precisa ser igual a quantidade de itens na NF")
        st.stop()
    fator_conversao = fator_conversao["Fator de Conversão"]
    return fator_conversao

def calcula_df(df, vl_total_nf):
    st.info("No campo :red[*Fator de Conversão*] Informar quantas unidades vem na caixa (somente números)")
    if "un" in df["Ucom"].values:
        
        fator_conversao = input_fator_conversao(df)
        df["Qt un"] = df["qt_Com"]
        df["Qt Cx"] = df["Qt un"] / fator_conversao
    elif "cx" in df["Ucom"].values:
        fator_conversao = input_fator_conversao(df)
        df["Qt Cx"] = df["qt_Com"]
        df["Qt un"] = df["Qt Cx"] * fator_conversao
    elif "kg" in df["Ucom"].values:
        #Faz o mesmo que o anterior, melhoria para utilizaro extrair_inteiro_unidade antes de retornar o fator_conversao
        st.warning("Fator de Conversão é KG")
        fator_conversao = input_fator_conversao(df)
        df["Qt Cx"] = df["qt_Com"]
        df["Qt un"] = df["Qt Cx"] * fator_conversao
    else:
        #Faz o mesmo que o anterior, melhoria para utilizaro extrair_inteiro_unidade antes de retornar o fator_conversao
        st.error("erro não foi possível identificar Unidade de Compra")
        fator_conversao = input_fator_conversao(df)
        df["Qt Cx"] = df["qt_Com"]
        df["Qt un"] = df["Qt Cx"] * fator_conversao

    if df["CST"].isin(["0","20"]).any():
        if df["CEST"].values != "":
            st.error(f"Contactar Contabilidade Nfe possui itens com CEST {df["CEST"].values}")
            if st.toggle("Já possuo retorno da contabilidade"):
                "erro2"
                st.stop()
            else:
                "erro3"
                st.stop()

    if not vl_total_nf == df["Valor Original"].sum():
        df["Valor Total"] = df["Valor Original"] + df["V_ST"] + df["V_IPI"]
        df["Valor Cx"] = df["Valor Total"] / df["Qt Cx"]
        df["Valor un"] = df["Valor Total"] / df["Qt un"]

        total_impostos = df["V_ST"].sum()+df["V_IPI"].sum()

    else:
        df["Valor Total"] = df["Valor Original"]
        df["Valor Cx"] = df["Valor Total"] / df["Qt Cx"]
        df["Valor un"] = df["Valor Total"] / df["Qt un"]
        total_impostos=0

    return df, total_impostos

# --- Interface Streamlit ---
st.set_page_config(page_title="Calculo NFe", layout="wide")
st.markdown("# :material/Docs: Calculo NF-e de Compras")
st.divider()
st.markdown("## :material/Upload: Importação de Arquivo xml")

uploaded_file = st.file_uploader("Arraste o XML da nota fiscal aqui", type="xml")

if uploaded_file:
    df, total_nf, soma_itens, emitente_nome, emitente_fantasia, Nr_Nfe = processa_XML(uploaded_file)

    df_calculado, imposto_somado = calcula_df(df, total_nf)

    st.divider()
    st.markdown("## Informações Gerais")

    if total_nf==soma_itens:
        st.success(":material/Check: Sem Calculo de ST")
    elif total_nf==df["Valor Total"].sum():
        st.success(":material/Check: Possui Calculo de ST")
    else:
        st.error(":material/Close: Nâo foi possível calcular impostos")

    st.markdown(f"### Emitente: :blue[{emitente_fantasia}] - {emitente_nome}")
    st.markdown(f"#### Nº NFe: :blue[{Nr_Nfe}]")

    if not df["CST"].isin(["20", "60", "70"]).any():
        st.error(":material/Close: Encontrado Registro com CST diferente de 20, 60 ou 70!")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total da Nota (XML)", f"R$ {total_nf:,.2f}")
    col2.metric("Soma dos Produtos", f"R$ {soma_itens:,.2f}",delta=f"{soma_itens-total_nf:.2f}")
    col3.metric("Imposto Somado", f"R$ {imposto_somado:,.2f}")

    st.divider()
    st.markdown("## :material/Post: Relatório para Compras")

    df_dir = df_calculado[['Item', 'Descrição', 'Qt Cx', 'Valor Total', 'Valor un']]
    st.dataframe(
        df_dir.style.format({
            "Qt Cx": lambda x: f"{x:,.2f}".replace(".","x").replace(",",".").replace("x",","),
            "Valor Total": lambda x: f"R$ {x:,.2f}".replace(".","x").replace(",",".").replace("x",","),
            "Valor un": lambda x: f"R$ {x:,.2f}".replace(".","x").replace(",",".").replace("x",","),
        }),
        hide_index=True,
        width="stretch",
        height="content"
    )

    st.divider()
    st.markdown("## :material/Package: Logística: Conferência Cega")
    st.markdown(f"#### Emitente: :blue[{emitente_fantasia}] - {emitente_nome}")
    df_log = df_calculado[["Codigo Fornecedor",'Descrição']].copy()
    df_log.index=df_calculado["Item"]
    df_log['Qtd Contada'] = ""
    df_log['Data Validade'] = ""
    st.table(
        df_log,
        border="horizontal",
    )