import streamlit as st
import xmltodict
import re
import pandas as pd

#   Input do número do XML e buscar no site da fazenda para calculo

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
        if "vDesc" in item["prod"]:
            v_desc = float(item["prod"]["vDesc"])
        else:
            v_desc=0

        soma_produtos += valor_produto
            
        
        
        #   OTIMIZAR
        icms_info = imposto['ICMS']
        tipo_icms = list(icms_info.keys())[0] # Ex: 'ICMS60'
        cst = icms_info[tipo_icms].get('CST', icms_info[tipo_icms].get('orig', ''))
        v_st = float(icms_info[tipo_icms].get('vICMSST', 0))        
        v_FCPST = float(icms_info[tipo_icms].get("vFCPST",0))

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
            "V_IPI": valor_IPI,
            "V_FCPST": v_FCPST,
            "Valor Desconto": v_desc
        })
    soma_produtos = round(soma_produtos,2)
    return pd.DataFrame(lista_produtos), total_nf_xml, soma_produtos, emitente_nome, emitente_fantasia, nr_Nfe
def extrair_inteiro_unidade(texto_unidade):
    numeros = re.findall(r'\d+', str(texto_unidade))
    if numeros:
        return int("".join(numeros))
    return 1 # Retorna 1 se for apenas 'un' ou 'cx' sem número
def solicita_input(df, tipo):
    if tipo=="fator_conversão":
        fator_conversao = df[["Descrição", "CST", "CEST"]].copy()
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
    elif tipo=="guia_ST":
        guia_ST = df[["Descrição"]].copy()
        guia_ST["Valor Guia ST"] = 0.0
        guia_ST = st.data_editor(
            guia_ST,
            width="stretch",
            hide_index=True,
            num_rows="dynamic"
        )

        if 0 in guia_ST.values:
            st.error("Guia ST está zerada!")
            st.stop()
        if len(df) != len(guia_ST):
            st.error("Qt de conversões precisa ser igual a quantidade de itens na NF")
            st.stop()
        return guia_ST

def calcula_df(df, vl_total_nf):
    escolha_conversão_user = None
    if not df["Ucom"].isin(["cx", "un"]).all():
        st.error("Não foi encontrado fator de conversão")
        if "kg" in df["Ucom"].values:
            st.warning("Fator de Conversão é KG")
        escolha_conversão_user = st.segmented_control(
            "Informar Unidade de Compra",
            ["CX/FD", "UN"],
            default="UN",
            width="stretch"
        )
    st.divider()
    st.caption("Informar :red[*Fator de Conversão*] (somente números)")
    if "un" in df["Ucom"].values or escolha_conversão_user=="UN":
        fator_conversao = solicita_input(df, "fator_conversão")
        df["Qt un"] = df["qt_Com"]
        df["Qt Cx"] = df["Qt un"] / fator_conversao
    elif "cx" in df["Ucom"].values or escolha_conversão_user=="CX/FD":
        fator_conversao = solicita_input(df, "fator_conversão")
        df["Qt Cx"] = df["qt_Com"]
        df["Qt un"] = df["Qt Cx"] * fator_conversao
    else:
        st.error("Erro4")
        st.stop()
    if df["CST"].isin(["00","20"]).any():
        if not df["CEST"].isin([""]).any():
        #if df["CEST"].values != "":
            st.divider()
            df[["Descrição","CEST"]]

            if st.toggle("Já possuo retorno da contabilidade"):
                st.markdown("### Informe Calculo ST :blue[Contabilidade]")
                guia_st = solicita_input(df, "guia_ST")
                df = df.merge(guia_st)
                df["Valor Total"] = df["Valor Original"] + df["V_ST"] + df["V_IPI"] + df["Valor Guia ST"] + df["V_FCPST"] - df["Valor Desconto"]
                df["Valor Cx"] = df["Valor Total"] / df["Qt Cx"]
                df["Valor un"] = df["Valor Total"] / df["Qt un"]

                total_impostos = df["V_ST"].sum()+df["V_IPI"].sum()+df["Valor Guia ST"].sum()-df["Valor Desconto"].sum()
                total_Valor_Total = round(df["Valor Total"].sum(),2)
                return df, total_impostos, total_Valor_Total
            else:
                st.error(f"Contactar Contabilidade Nfe possui itens com CEST")

                st.stop()

    if not vl_total_nf == df["Valor Original"].sum():
        df["Valor Total"] = df["Valor Original"] + df["V_ST"] + df["V_IPI"] + df["V_FCPST"] - df["Valor Desconto"]
        df["Valor Cx"] = df["Valor Total"] / df["Qt Cx"]
        df["Valor un"] = df["Valor Total"] / df["Qt un"]

        total_impostos = df["V_ST"].sum()+df["V_IPI"].sum()-df["Valor Desconto"].sum()
    else:
        df["Valor Total"] = df["Valor Original"]
        df["Valor Cx"] = df["Valor Total"] / df["Qt Cx"]
        df["Valor un"] = df["Valor Total"] / df["Qt un"]
        total_impostos=0

    total_Valor_Total = round(df["Valor Total"].sum(),2)

    return df, total_impostos, total_Valor_Total

# --- Interface Streamlit ---
st.set_page_config(page_title="Calculo NFe", layout="wide")
st.markdown("# :material/Docs: Calculo NF-e de Compras")
st.divider()
st.markdown("## :material/Upload: Importação de Arquivo xml")

uploaded_file = st.file_uploader("Arraste o XML da nota fiscal aqui", type="xml")

if uploaded_file:
    df, total_nf, soma_itens, emitente_nome, emitente_fantasia, Nr_Nfe = processa_XML(uploaded_file)

    df_calculado, imposto_somado, Valor_Total_Somado = calcula_df(df, total_nf)

    st.divider()
    st.markdown("## Informações Gerais")

    
    if "Valor Guia ST" in df_calculado.columns:
        st.warning(":material/Check: Calculo com base no ST (Contabilidade)")
    elif total_nf==soma_itens:
        st.success(":material/Check: Sem Calculo de ST")
    elif total_nf==Valor_Total_Somado:
        st.success(":material/Check: Possui Calculo de ST")
    else:
        st.error(":material/Close: Não foi possível calcular impostos")

    st.markdown(f"### Emitente: :blue[{emitente_fantasia}] - {emitente_nome}")
    st.markdown(f"#### Nº NFe: :blue[{Nr_Nfe}]")

    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Valor Total da Nota",
            f"R$ {total_nf:,.2f}".replace(",","x").replace(".",",").replace("x",".")
        )
        st.space()
        st.metric(
            "Valor Total dos Produtos",
            f"R$ {soma_itens:,.2f}".replace(",","x").replace(".",",").replace("x","."),
            delta=f"{soma_itens-total_nf:,.2f}".replace(",","x").replace(".",",").replace("x","."),
        )
    with col2:
        st.metric(
            "Valor Total Calculado",
            f"R$ {Valor_Total_Somado:,.2f}".replace(",","x").replace(".",",").replace("x","."),
            delta=Valor_Total_Somado-total_nf
        )
        st.space()
        if imposto_somado>0:
            st.metric("Imposto Somado", f"R$ {imposto_somado:,.2f}")
        else:
            st.metric(
                "Desconto Concedido",
                f"R$ {abs(imposto_somado):,.2f}".replace(",","x").replace(".",",").replace("x",".")
            )

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