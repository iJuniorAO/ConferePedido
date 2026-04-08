import streamlit as st
import xmltodict
import re
import pandas as pd
from datetime import datetime,timedelta

#   Input do número do XML e buscar no site da fazenda para calculo
#   Testar Calculo de Bonificação se está OK, somente testado com guia

def processa_XML(xml_file):
    data = xmltodict.parse(xml_file)

    info_nfe = data['nfeProc']['NFe']['infNFe']
    detalhes = info_nfe['det']
    total = info_nfe['total']
    emitente=info_nfe["emit"]

    if not isinstance(detalhes, list):
        detalhes = [detalhes]

    emitente_nome = emitente["xNome"]
    emitente_uf = emitente["enderEmit"]["UF"]

    if "xFant" in emitente:
        emitente_fantasia = emitente["xFant"]
    else:
        emitente_fantasia=""

    nr_Nfe = info_nfe["ide"]["nNF"]
      
    total_nf_xml = float(total['ICMSTot']['vNF'])
    outras_despesas = float(total['ICMSTot']['vOutro'])


    if "cobr" in info_nfe:
        Boletos = info_nfe["cobr"].get("dup",0)
    else:
        Boletos=0
    
    meio_pgto = info_nfe["pag"]["detPag"]["tPag"]
    valor_pgto = float(info_nfe["pag"]["detPag"]["vPag"])


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
            
        cod_CEST = item["prod"].get("CEST","")
        
        if "IPI" in item["imposto"]:
            if "IPITrib" in item["imposto"]["IPI"]:
                valor_IPI = float(item["imposto"]["IPI"]["IPITrib"]["vIPI"])
            else:
                valor_IPI = 0
        else:
            valor_IPI=0

        v_desc = float(item["prod"].get("vDesc",0))

        soma_produtos += valor_produto
                
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
            "ICMS_CST": cst,
            "CEST": cod_CEST,
            "V_ST": v_st,
            "V_IPI": valor_IPI,
            "V_FCPST": v_FCPST,
            "Valor Desconto": v_desc
        })
    soma_produtos = round(soma_produtos,2)
    #return pd.DataFrame(lista_produtos), total_nf_xml, soma_produtos, emitente_nome, emitente_fantasia, nr_Nfe, Boletos, pgto, outras_despesas
    pgto = {
        "meio_pgto":meio_pgto,
        "valor_pgto":valor_pgto,
    }
    return {
        "df": pd.DataFrame(lista_produtos),
        "total_nf": total_nf_xml,
        "soma_produtos": soma_produtos,
        "emitente": {
            "emitente_nome": emitente_nome,
            "emitente_fantasia": emitente_fantasia,
            "emitente_uf":emitente_uf,

        },
        "nr_Nfe": nr_Nfe,
        "Boletos": Boletos,
        "pgto": pgto,
        "outras_despesas": outras_despesas
    }
def extrair_inteiro_unidade(texto_unidade):
    numeros = re.findall(r'\d+', str(texto_unidade))
    if numeros:
        return int("".join(numeros))
    return 1 # Retorna 1 se for apenas 'un' ou 'cx' sem número
def define_fator_conversao(df):
    st.markdown("### Informe o :blue[Fator de Conversão]")    
    if df["Ucom"].isin(["cx"]).all():
        escolha_conversao = "CX/FD"
    elif df["Ucom"].isin(["un"]).all():
        escolha_conversao = "UN"    
    else:
        if "kg" in df["Ucom"].values:
            st.warning("Fator de Conversão tem KG")
        escolha_conversao = st.segmented_control(
            "Informar Unidade de Compra",
            ["CX/FD", "UN"],
            width="stretch",
        )
    if escolha_conversao==None:
        st.error("Selecione um fator de conversão")
        return 0,0

    fator_conversao = df[["Descrição", "ICMS_CST", "CEST"]].copy()
    fator_conversao["Fator de Conversão"] = 0
    st.caption("Digitar :red[**SOMENTE**] números")
    fator_conversao = st.data_editor(
        fator_conversao,
        disabled=["Descrição", "ICMS_CST", "CEST"],
        width="stretch",
        hide_index=True,
        height="content",
    )
    if 0 in fator_conversao["Fator de Conversão"].values:
        st.error("Não pode haver fator de conversão: 0 - 'Zero'")
        return 0,0
    fator_conversao = fator_conversao["Fator de Conversão"]
    return fator_conversao, escolha_conversao
def calculos(df, vl_total_nf, outras_despesas,emitente, fator_conversao, unidade_compra, ignora_impostos, df_bon=""):
    def define_cx_un():
        if unidade_compra=="UN":
            df["Qt un"] = df["qt_Com"]
            df["Qt Cx"] = df["Qt un"] / fator_conversao
            if uploaded_file_2:
                df_bon["Qt un"] = df_bon["qt_Com"]
                df_bon["Qt Cx"] = df_bon["Qt un"] / fator_conversao
            return df
        elif unidade_compra=="CX/FD":
            df["Qt Cx"] = df["qt_Com"]
            df["Qt un"] = df["Qt Cx"] * fator_conversao
            if uploaded_file_2:
                df_bon["Qt Cx"] = df_bon["qt_Com"]
                df_bon["Qt un"] = df_bon["Qt Cx"] * fator_conversao
        return df
    def solicita_guia(df):
        guia_ST = df[["Descrição"]].copy()
        guia_ST["Valor Guia"] = 0.0
        guia_ST = st.data_editor(
            guia_ST,
            width="stretch",
            hide_index=True,
            disabled=["Descrição"]
        )
        if 0 in guia_ST.values:
            st.error("Guia ST tem valores zerados!")
            st.stop()
        return guia_ST

    df["Valor Outras Despesas"] = (df["Valor Original"]/df["Valor Original"].sum())*outras_despesas

    df = define_cx_un()

    if uploaded_file_2:
        df_bon["Qt Cx Bon"] = df_bon["Qt Cx"]*desconsidera_bonificacao
        df_bon["Qt un Bon"] = df_bon["Qt un"]*desconsidera_bonificacao

        df=df.merge(df_bon[["Descrição", "Qt Cx Bon", "Qt un Bon"]],how="left")
        df["Qt Cx"] = df["Qt Cx Bon"].fillna(0) + df["Qt Cx"]
        df["Qt un"] = df["Qt un Bon"].fillna(0) + df["Qt un"]

    linhas_com_guia = df[df["ICMS_CST"].isin(["00", "20"]) & (df["CEST"] != "")]


    if (not linhas_com_guia.empty):
        st.markdown("### Informe Calculo GUIA ST :blue[Contabilidade]")
        if st.toggle("Já possuo retorno da contabilidade"):
            st.markdown("### Informe Calculo GUIA ST :blue[Contabilidade]")

            guia_st = solicita_guia(linhas_com_guia)
            df = df.merge(guia_st,how="left")
        else:
            st.error(f"Contactar Contabilidade - Possui itens com CEST")
            st.stop()        

    if emitente["emitente_uf"]!="MG":
        if st.toggle("Já possuo retorno da contabilidade"):
            st.markdown("### Informe Calculo ST :blue[Contabilidade]")

            guia_st = solicita_guia(df)
            df = df.merge(guia_st,how="left")
        else:
            st.error(f"Contactar Contabilidade - Fornecedor fora de MG")
            st.stop()        

    else:
        df["Valor Guia"]=0.0
    
    if ignora_impostos:
        df["Valor Total"] = df["Valor Original"]
        total_impostos=0
    else:
        df["Valor Total"] = df["Valor Original"] + df["V_ST"] + df["V_IPI"] + df["Valor Guia"] + df["Valor Outras Despesas"] + df["V_FCPST"] - df["Valor Desconto"]
        total_impostos = df["V_ST"].sum()+df["V_IPI"].sum()+df["Valor Guia"].sum()-df["Valor Desconto"].sum()
    
    df["Valor Cx"] = df["Valor Total"] / df["Qt Cx"]
    df["Valor un"] = df["Valor Total"] / df["Qt un"]

    valor_total_calculado = round(df["Valor Total"].sum(),2)
    return {
        "df_calc":df,
        "df_calc_bon":df_bon,   # dataframe calculado da bonificação
        "total_impostos":total_impostos,
        "valor_total_calculado":valor_total_calculado,
    }
    #return df, df_bon, total_impostos, total_Valor_Total
def valida_calculo():
    if df_calc["Valor Guia"].sum():
        return st.error(":material/Check: Possui GUIA a ser paga")
    elif resposta_xml["total_nf"]==resposta_xml["soma_produtos"]:
        return st.success(":material/Check: Sem ST")
    elif resposta_xml["total_nf"]==calc_vl_total_calculado:
        return st.success(":material/Check: Encontrado Calculo de ST")
    elif diferenca_nf_total_calculado==0:
        st.error("Não foi considerado os impostos")
    else:
        return st.error(":material/Close: Não foi possível calcular impostos")

# --- Interface Streamlit ---
st.set_page_config(page_title="Calcula NFe", layout="wide")
HOJE = datetime.now().date()
st.markdown("# :material/Docs: Calculo NF-e de Compras")
st.markdown("## :material/Upload: Importação de Arquivo xml")
desconto_boleto_padrao =  ["LATICINIOS BELINHO"] #somente nome fantasia completo
meio_pagamento = {
    '01':'Dinheiro',
    '02':'Cheque',
    '03':'Cartão de Crédito',
    '04':'Cartão de Débito',
    '05':'Crédito Loja',
    '10':'Vale Alimentação',
    '11':'Vale Refeição',
    '12':'Vale Presente',
    '13':'Vale Combustível',
    '15':'Boleto Bancário',
    '16':'Depósito Bancário',
    '17':'Pagamento Instantâneo (PIX)',
    '18':'Transferência bancária, Carteira Digital',
    '19':'Programa de fidelidade, Cashback, Crédito Virtual',
    '90':'Sem pagamento',
    '99':'Outros',    
    }

with st.sidebar:
    st.markdown("# :material/Filter_Alt: Filtros")
    desconsidera_bonificacao = st.number_input("% Para desconsiderar na Bonificação",min_value=0.00,max_value=100.00,value=10.00)
    desconsidera_bonificacao = 1-(desconsidera_bonificacao/100)

    st.divider()
    st.markdown("# Legenda")
    st.markdown("### Valor Total Boletos")
    st.markdown(":green[R$###.###,##] - Boleto = Calculo")
    st.markdown(":orange[R$###.###,##] - Boleto = Total Nfe")
    st.markdown(":blue[R$###.###,##] - Boleto = Total Produtos")
    st.markdown(":red[R$###.###,##] - Valor Divergente")
    st.space()
    st.markdown("### Vencimento Boletos")
    st.markdown(f"{HOJE} - Vencimento OK")
    st.markdown(f":red[:material/Close: {HOJE-timedelta(days=1)}] - Vencido")

    st.divider()
    st.markdown("# Melhorias")
    st.markdown("|- Opção de imbutir valor de frete no calculo")

c1,c2 = st.columns(2)
with c1:
    uploaded_file = st.file_uploader("COMPRA - Arraste o XML da nota fiscal aqui", type="xml")
with c2:
    uploaded_file_2 = st.file_uploader("BONIFICAÇÃO - Arraste o XML da nota fiscal aqui", type="xml", disabled=True)
st.divider()
if uploaded_file:
    resposta_xml = processa_XML(uploaded_file)
    fator_conversao, unidade_compra = define_fator_conversao(resposta_xml["df"])

    if uploaded_file_2:
        if uploaded_file_2:
            
            resposta_xml_bon  = processa_XML(uploaded_file_2)
            if resposta_xml["emitente_nome"] != resposta_xml_bon["emitente_nome"]:
                st.error("NFs possuem emitente divergente")
                st.stop()
            if resposta_xml["Nr_Nfe"]==resposta_xml_bon["Nr_Nfe"]:
                st.error("Nº NF BONIFICAÇÃO não pode ser o mesmo da NF COMPRA")
                st.stop()
            if desconsidera_bonificacao==100:
                st.error(":material/Close: Não é possível calcular bonificação ignorando 100% da bonificação")
                st.markdown("Valor padrão 10%")
                st.stop()

        else:
            st.error(":material/Close: Insira o XML da bonificação")
            st.stop()
    st.divider()

    if resposta_xml["emitente"]["emitente_fantasia"] in desconto_boleto_padrao:
        ignora_impostos=True
    else:
        ignora_impostos=False
    ignora_impostos = st.toggle("Não considerar imposto ST (desconto em boleto)", value=ignora_impostos)

    if not isinstance(fator_conversao,int):
        if not uploaded_file_2:
            resposta_calc = calculos(resposta_xml["df"], resposta_xml["total_nf"], resposta_xml["outras_despesas"], resposta_xml["emitente"], fator_conversao, unidade_compra, ignora_impostos, None)
        # else:
        #     df_calculado, df_calculado_bon, imposto_somado, Valor_Total_Somado = calculos(resposta_xml["df"], resposta_xml["total_nf"], fator_conversao, ignora_impostos,df_bon)
        calc_vl_total_calculado = resposta_calc["valor_total_calculado"]
        df_calc = resposta_calc["df_calc"]
        st.divider()
        
        st.markdown("## :material/Functions: Informações Gerais")
        with st.expander("Mostrar detalhes do calculo",icon=":material/function:"):
            st.dataframe(
                resposta_xml["df"].drop(columns=["Codigo Fornecedor","Qt un","Qt Cx"])
            )


        diferenca_nf_total_calculado = calc_vl_total_calculado-resposta_xml["soma_produtos"]
        valida_calculo()

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Valor Total da Nota (campo total)",
                f"R$ {resposta_xml["total_nf"]:,.2f}".replace(",","x").replace(".",",").replace("x",".")
            )
            st.space()
            st.metric(
                "Valor Total dos Produtos",
                f"R$ {resposta_xml["soma_produtos"]:,.2f}".replace(",","x").replace(".",",").replace("x","."),
            )
        with col2:
            st.metric(
                "Valor Total Calculado",
                f"R$ {calc_vl_total_calculado:,.2f}".replace(",","x").replace(".",",").replace("x","."),
            )
            st.space()
            if diferenca_nf_total_calculado>0:
                st.metric(":red[**Imposto Somado**]", f"R$ {abs(diferenca_nf_total_calculado):,.2f}")
            elif calc_vl_total_calculado == resposta_xml["total_nf"]:
                st.metric(":green[**Sem Guia**]", f"R$ {abs(diferenca_nf_total_calculado):,.2f}")
            else:
                st.metric(
                    ":green[**Desconto em Boleto**]",
                    f"R$ {abs(calc_vl_total_calculado-resposta_xml["total_nf"]):,.2f}".replace(",","x").replace(".",",").replace("x",".")
                )

        st.divider()
        meio_pgto = resposta_xml["pgto"]["meio_pgto"]
        valor_pgto = resposta_xml["pgto"]["valor_pgto"]
        st.markdown(f"## :material/Payments: {meio_pagamento.get(meio_pgto,f"Cod.: {meio_pgto} - Não Encontrado")}")
        if not resposta_xml["Boletos"]:
            st.markdown(f"## :red[:material/Money_Off: Sem Detalhes de Vencimento do Boleto]")        

            if calc_vl_total_calculado==valor_pgto:
                st.markdown(f"### Valor Total :green[R$ {valor_pgto:,.2f}]".replace(".","x").replace(",",".").replace("x",","))
            else:
                st.markdown(f"### Valor Total :red[R$ {valor_pgto:,.2f}]".replace(".","x").replace(",",".").replace("x",","))
                st.error("Boleto com valor divergente do Calculo")
        else:            
            if isinstance(resposta_xml["Boletos"], dict):
                resposta_xml["Boletos"] = [(resposta_xml["Boletos"])]
                
            qt_Boleto = len(resposta_xml["Boletos"])
            vl_total_boleto = sum(float(boleto["vDup"]) for boleto in resposta_xml["Boletos"])
            st.markdown(f"### Boletos Emitidos: {qt_Boleto}")
            
            if (calc_vl_total_calculado==vl_total_boleto) & (vl_total_boleto==resposta_xml["total_nf"]):
                st.markdown(f"### Valor Total :green[R$ {vl_total_boleto:,.2f}]".replace(".","x").replace(",",".").replace("x",","))
                st.caption("Boleto :green[**IGUAL**] ao valor total da NFe e o valor calculado")
            elif (calc_vl_total_calculado > vl_total_boleto) & (vl_total_boleto==resposta_xml["total_nf"]):
                st.markdown(f"### Valor Total :green[R$ {vl_total_boleto:,.2f}]".replace(".","x").replace(",",".").replace("x",","))
                st.caption("Valor a pagar :red[**MAIOR**] que valor total da NFe e IGUAL ao valor calculado")
            elif vl_total_boleto==resposta_xml["soma_produtos"]:
                st.markdown(f"### Valor Total :blue[R$ {vl_total_boleto:,.2f}]".replace(".","x").replace(",",".").replace("x",","))
            else:
                st.error("Boleto com valor divergente do Calculo")
                st.markdown(f"### Valor Total :red[R$ {vl_total_boleto}]")
            cols = st.columns(qt_Boleto)

            for i, boleto in enumerate(resposta_xml["Boletos"]):
                Vencimento_Boleto = datetime.strptime(boleto["dVenc"],"%Y-%m-%d")
                with cols[i]:
                    with st.container(border=True):
                        st.markdown(f"Boleto: {boleto["nDup"]}")
                        st.markdown(f"Valor: {float(boleto["vDup"]):,.2f}".replace(".","x").replace(",",".").replace("x",","))
                        if Vencimento_Boleto>(datetime.now()+timedelta(5)):
                            st.markdown(f":green[Vencimento: {boleto["dVenc"]}]")
                            st.caption("PRAZO :green[**ACIMA**] DE 5 DIAS")
                        elif Vencimento_Boleto>(datetime.now()):
                            st.markdown(f":green[Vencimento: {boleto["dVenc"]}]")
                            st.caption("PRAZO :orange[**ABAIXO**] DE 5 DIAS")
                        else:
                            st.markdown(f":red[Vencimento: {boleto["dVenc"]}]")
                            st.caption("PRAZO :red[**VENCIDO**]")

            st.divider()

        st.markdown(f"### Emitente: :blue[{resposta_xml["emitente"]['emitente_fantasia']}] - {resposta_xml["emitente"]["emitente_nome"]}")
        st.markdown(f"#### Nº NFe: :blue[{resposta_xml["nr_Nfe"]}]")
        st.markdown("## :material/Post: Relatório para Compras")

        df_calc["Qt por Cx"] = df_calc["Qt un"]/df_calc["Qt Cx"]

        if df_calc["Valor Guia"].sum()>0:            
            df_dir = df_calc[['Item', 'Descrição', 'Qt Cx', "Qt por Cx", 'Valor Total',"Valor Guia", 'Valor un']]
        else:
            df_dir = df_calc[['Item', 'Descrição', 'Qt Cx', "Qt por Cx", 'Valor Total', 'Valor un']]
        
        st.dataframe(
            df_dir.style.format({
                "Qt por Cx": lambda x: f"{x:,.2f}".replace(".","x").replace(",",".").replace("x",","),
                "Qt Cx": lambda x: f"{x:,.2f}".replace(".","x").replace(",",".").replace("x",","),
                "Valor Total": lambda x: f"R$ {x:,.2f}".replace(".","x").replace(",",".").replace("x",","),
                "Valor Guia": lambda x: f"R$ {x:,.2f}".replace(".","x").replace(",",".").replace("x",","),
                "Valor un": lambda x: f"R$ {x:,.2f}".replace(".","x").replace(",",".").replace("x",","),
            }),
            hide_index=True,
            width="stretch",
            height="content"
        )
    st.divider()
    selecao_conf_cega = st.toggle("Ocultar bordas")
    st.markdown("# :material/Package: Logística: Conferência Cega")
    st.markdown(f"#### Emitente: :blue[{resposta_xml["emitente"]["emitente_fantasia"]}] - {resposta_xml["emitente"]["emitente_nome"]}")
    colun1, colun2, colun3, colun4, colun5 = st.columns(5)
    with colun1:
        st.write(r"______ / ______")
    with colun2:
        st.markdown(":________ Ordem Liberação")
    with colun3:
        st.markdown(":material/Check_Box_Outline_Blank: Descarga Normal")
    with colun4:
        st.markdown(":material/Check_Box_Outline_Blank: Descarga Isenta")
    with colun5:
        st.markdown("R$:_________________")

    df_log = resposta_xml["df"][["Codigo Fornecedor",'Descrição']].copy()
    df_log = df_log.rename(columns={"Codigo Fornecedor": "Cod Forn."})
    df_log.index=resposta_xml["df"]["Item"]
    st.space()
    df_log["Qt por Cx"]=""
    df_log['Qtd Contada'] = ""
    df_log['Data Validade'] = ""
    if selecao_conf_cega: # tabela
        st.table(
            df_log,
            border="horizontal",
            width="stretch",
        )
    else:
        st.dataframe(
            df_log,
            column_config={
                "Descrição": st.column_config.TextColumn(
                    "Descrição",
                    width="large",
                )
            },
            width="stretch",
            height="content",
        )
    st.divider()