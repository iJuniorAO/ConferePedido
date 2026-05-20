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
    emitente = info_nfe["emit"]
    det_pag = info_nfe["pag"]["detPag"]

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

    if isinstance(det_pag,dict):
        meio_pgto = det_pag["tPag"]
        valor_pgto = float(det_pag["vPag"])
    else:   # Senão == lista 
        meio_pgto = det_pag[0]["tPag"]
        valor_pgto = sum([float(x["vPag"]) for x in det_pag])        
        

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

def encontra_un_compra(df):
    if df["Ucom"].isin(["cx","fd","frd"]).all():
        return "CX/FD"
    elif df["Ucom"].isin(["un"]).all():
        return "UN"
    elif df["Ucom"].isin(["kg"]).all():
        return "KG"
    
    return ""    

def define_un_compra(df):
    if "kg" in df["Ucom"].values:
        st.warning("Fator de Conversão tem KG")
    escolha_conversao = st.segmented_control(
            "Informar Unidade de Compra",
            ["CX/FD", "UN", "KG"],
            default=None,
            width="stretch",
    )
    return escolha_conversao

def define_fator_conversao(df):
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
    fator_conversao = fator_conversao["Fator de Conversão"]
    return fator_conversao

def calculos(df, vl_total_nf, outras_despesas,emitente, fator_conversao, unidade_compra, ignora_impostos, df_bon=""):
    def define_cx_un():
        if (unidade_compra=="UN") or (unidade_compra=="KG"):
            df["Qt un"] = df["qt_Com"]
            df["Qt de Cx"] = df["Qt un"] / fator_conversao
            if uploaded_file_2:
                df_bon["Qt un"] = df_bon["qt_Com"]
                df_bon["Qt de Cx"] = df_bon["Qt un"] / fator_conversao
            return df
        elif unidade_compra=="CX/FD":
            df["Qt de Cx"] = df["qt_Com"]
            df["Qt un"] = df["Qt de Cx"] * fator_conversao
            if uploaded_file_2:
                df_bon["Qt de Cx"] = df_bon["qt_Com"]
                df_bon["Qt un"] = df_bon["Qt de Cx"] * fator_conversao
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
        return guia_ST

    df["Valor Outras Despesas"] = (df["Valor Original"]/df["Valor Original"].sum())*outras_despesas
    df["Valor Guia"] = 0

    df = define_cx_un()

    if uploaded_file_2:
        df_bon["Qt de Cx Bon"] = df_bon["Qt de Cx"]*desconsidera_bonificacao
        df_bon["Qt un Bon"] = df_bon["Qt un"]*desconsidera_bonificacao

        df=df.merge(df_bon[["Descrição", "Qt de Cx Bon", "Qt un Bon"]],how="left")
        df["Qt de Cx"] = df["Qt de Cx Bon"].fillna(0) + df["Qt de Cx"]
        df["Qt un"] = df["Qt un Bon"].fillna(0) + df["Qt un"]

    # Regra de negocio
    # Guia se ICMS-ST for 00 ou 20
    linhas_com_guia = df[df["ICMS_CST"].isin(["00", "20"])]

    if (not linhas_com_guia.empty):
        st.markdown("#### Solicitar Calculo GUIA ST :blue[Contabilidade]")
        st.text("Foi verificado que na NFe possui item com ICMS ST 00 ou 20")
        if emitente["emitente_uf"]!="MG":
            st.error("Fornecedor fora de Minas")
        if st.toggle("Já possuo retorno da contabilidade"):
            st.markdown("#### Informe Valor da :blue[GUIA ST]")
            guia_st = solicita_guia(linhas_com_guia)
            st.caption("Para seguir sem calcular a guia, insira Valor da Guia qualquer número abaixo de 0,01 | :blue[Ex.: R$ 0,00000001]")
            if 0 in guia_st.values:
                st.error("Guia ST tem valores zerados!")
                st.stop()
            df = df.merge(guia_st,how="left")
        else:
            st.info(f"Contactar Contabilidade")
            st.stop()        

    
    if ignora_impostos:
        df["Valor Total"] = df["Valor Original"]
        total_impostos=0
    else:
        df["Valor Total"] = df["Valor Original"] + df["V_ST"] + df["V_IPI"] + df["Valor Guia"] + df["Valor Outras Despesas"] + df["V_FCPST"] - df["Valor Desconto"]
        total_impostos = df["V_ST"].sum()+df["V_IPI"].sum()+df["Valor Guia"].sum()-df["Valor Desconto"].sum()
    
    df["Valor Cx"] = df["Valor Total"] / df["Qt de Cx"]
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
st.markdown("# :material/Adf_Scanner: Impressão Guia Cega")
st.markdown("## :material/Upload: Importação de Arquivo xml")
desconto_boleto_padrao =  ["LATICINIOS BELINHO"] #somente nome fantasia completo
# caso tenha uma pendência irá pausar o calculo porém não irá parar o programa
pendencia_calculo = False
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
if (not uploaded_file):
    st.info("Insira o XML para iniciar o calculo")
    st.divider()
    st.stop()
resposta_xml = processa_XML(uploaded_file)

st.markdown("## :material/Input: Informações")

st.markdown("#### 1. Selecionar :blue[Unidade de Compra]")
unidade_compra = encontra_un_compra(resposta_xml["df"])
if (not unidade_compra):
    unidade_compra = define_un_compra(resposta_xml["df"])
else:
    st.success("Unidade de Compra [cx ou un] encontrado automaticamente")
if (not unidade_compra):
    st.error("Necessário escolher fator de conversão")
    pendencia_calculo = True
    # st.stop()
else:
    pendencia_calculo = False


if not pendencia_calculo:
    st.space()
    st.markdown("#### 2. Informe se irá :blue[Ignorar Imposto] - Desconto em Boleto")
    if resposta_xml["emitente"]["emitente_fantasia"] in desconto_boleto_padrao:
        st.caption(f"Fornecedor: :blue[{resposta_xml["emitente"]["emitente_fantasia"]}] | Desconto em boleto padrão - Ignora imposto ativado")
        ignora_impostos=True
    else:
        ignora_impostos=False
    ignora_impostos = st.toggle("Não considerar imposto ST (desconto em boleto)", value=ignora_impostos)

if not pendencia_calculo:
    st.space()
    st.markdown("#### 3. Informe o :blue[Fator de Conversão]")
    fator_conversao = define_fator_conversao(resposta_xml["df"])
    if (0 in fator_conversao.values):
        st.error("Não pode haver fator de conversão: 'Zero'")
        pendencia_calculo = True
        # st.stop()
    else:
        pendencia_calculo = False

if not pendencia_calculo:
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
    else:
        resposta_calc = calculos(resposta_xml["df"], resposta_xml["total_nf"], resposta_xml["outras_despesas"], resposta_xml["emitente"], fator_conversao, unidade_compra, ignora_impostos, None)

    calc_vl_total_calculado = resposta_calc["valor_total_calculado"]
    df_calc = resposta_calc["df_calc"]


    st.divider()
    st.markdown("## :material/Functions: Informações Gerais")
    with st.expander("Mostrar detalhes do calculo",icon=":material/function:"):
        st.dataframe(
            resposta_xml["df"],
            column_order= ['Item', 'Descrição', 'ICMS_CST', 'CEST',
                'Valor Original', 'V_ST', 'V_IPI', 'V_FCPST', 'Valor Guia', 'Valor Outras Despesas',
                'Valor Desconto', 'Valor Total',
                'Ucom', 'qt_Com', 'Qt de Cx', 'Qt un',
                'Valor Cx', 'Valor un']                        
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
    valor_pgto = round(resposta_xml["pgto"]["valor_pgto"],2)
    st.markdown(f"## :material/Payments: {meio_pagamento.get(meio_pgto,f"Cod.: {meio_pgto} - :red[Não Encontrado]")}")
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
        vl_total_boleto = round(sum(float(boleto["vDup"]) for boleto in resposta_xml["Boletos"]),2)
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

    st.markdown("## :material/Post: Relatório para Compras")
    st.markdown(f"#### Emitente: :blue[{resposta_xml["emitente"]['emitente_fantasia']}] - {resposta_xml["emitente"]["emitente_nome"]}")
    st.markdown(f" Nº NFe: :blue[{resposta_xml["nr_Nfe"]}]")

    df_calc["Un por Cx"] = df_calc["Qt un"]/df_calc["Qt de Cx"]

    if df_calc["Valor Guia"].sum()>0:            
        df_dir = df_calc[['Item', 'Descrição', 'Qt de Cx', "Un por Cx", 'Valor Total',"Valor Guia", 'Valor un']]
    else:
        df_dir = df_calc[['Item', 'Descrição', 'Qt de Cx', "Un por Cx", 'Valor Total', 'Valor un']]


    formato_br = lambda x: f"{x:,.2f}".replace(".","x").replace(",",".").replace("x",",")
    formato_moeda = lambda x: f"R$ {x:,.2f}".replace(".","x").replace(",",".").replace("x",",")

    st.dataframe(
        df_dir
        .style.format({
            "Un por Cx": formato_br,
            "Qt de Cx": formato_br,
            "Valor Total": formato_moeda,
            "Valor Guia": formato_moeda,
            "Valor un": formato_moeda,
        }),
        hide_index=True,
        width="stretch",
        height="content"
    )
    if df_calc["Ucom"].isin(["kg"]).all():
        st.info("NF veio em KG")

st.divider()
selecao_conf_cega = st.toggle("Layout Secundário")
coluna1, coluna2 = st.columns(2, vertical_alignment="bottom")
with coluna1:
    st.markdown("## :material/Package: Logística: Conferência Cega")
with coluna2:
    st.write("Conferido por: _________________")

st.markdown(f"#### Emitente: :blue[{resposta_xml["emitente"]["emitente_fantasia"]}] - {resposta_xml["emitente"]["emitente_nome"]}")
st.markdown(f"Nº NFe: :blue[{resposta_xml["nr_Nfe"]}]")

colun1, colun2, colun3, colun4 = st.columns(4, vertical_alignment="center")
with colun1:
    st.write(r"______ / ______")
    st.markdown(":_____________ Ordem")
with colun2:
    st.checkbox('Descarga Normal')
    st.checkbox('Descarga Isenta')
with colun3:
    st.checkbox('Descarga Fixa')
    st.markdown("R$:_________________")
with colun4:
    st.checkbox('Lista')
    st.checkbox('Divisão')

df_log = resposta_xml["df"][["Codigo Fornecedor",'Descrição']].copy()
df_log = df_log.rename(columns={"Codigo Fornecedor": "Cod Forn."})
df_log.index=resposta_xml["df"]["Item"]
st.space()
df_log["Un por Cx"]=""
df_log['Qtd Cx Contada'] = ""
df_log['Data Validade'] = ""
df_log['Qtd Palete'] = ''
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
