import streamlit as st
import xmltodict
import re
import pandas as pd
from datetime import datetime,timedelta

#   Input do número do XML e buscar no site da fazenda para calculo
#   Testar Calculo de Bonificação se está OK, somente testado com guia

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

    if "cobr" in data["nfeProc"]["NFe"]["infNFe"]:
        Boletos = data["nfeProc"]["NFe"]["infNFe"]["cobr"].get("dup",0)
    else:
        Boletos=0
    pgto = data["nfeProc"]["NFe"]["infNFe"].get("pag",0)

    if False:
        if "cobr" in data["nfeProc"]["NFe"]["infNFe"]:
            Boletos = data["nfeProc"]["NFe"]["infNFe"]["cobr"].get("dup","")
        else:
            Boletos=0

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
    return pd.DataFrame(lista_produtos), total_nf_xml, soma_produtos, emitente_nome, emitente_fantasia, nr_Nfe, Boletos, pgto
def extrair_inteiro_unidade(texto_unidade):
    numeros = re.findall(r'\d+', str(texto_unidade))
    if numeros:
        return int("".join(numeros))
    return 1 # Retorna 1 se for apenas 'un' ou 'cx' sem número
def solicita_input(df, tipo):
    if tipo=="fator_conversão":
        fator_conversao = df[["Descrição", "ICMS_CST", "CEST"]].copy()
        fator_conversao["Fator de Conversão"] = 0
        fator_conversao = st.data_editor(
            fator_conversao,
            width="stretch",
            hide_index=True,
        )
        if 0 in fator_conversao.values:
            st.error("Não pode haver fator de conversão 'Zero', caso não tenha mude para '1'")
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
        )
        if 0 in guia_ST.values:
            st.error("Guia ST está zerada!")
            st.stop()
        return guia_ST
def calculos(df, vl_total_nf,ignora_impostos,df_bon=""):
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
    
    st.caption("Informar :red[*Fator de Conversão*] (somente números)")

    if "un" in df["Ucom"].values or escolha_conversão_user=="UN":
        fator_conversao = solicita_input(df, "fator_conversão")
        df["Qt un"] = df["qt_Com"]
        df["Qt Cx"] = df["Qt un"] / fator_conversao
        if calc_bonificacao:
            df_bon["Qt un"] = df_bon["qt_Com"]
            df_bon["Qt Cx"] = df_bon["Qt un"] / fator_conversao

    elif "cx" in df["Ucom"].values or escolha_conversão_user=="CX/FD":
        fator_conversao = solicita_input(df, "fator_conversão")
        df["Qt Cx"] = df["qt_Com"]
        df["Qt un"] = df["Qt Cx"] * fator_conversao
        if calc_bonificacao:
            df_bon["Qt Cx"] = df_bon["qt_Com"]
            df_bon["Qt un"] = df_bon["Qt Cx"] * fator_conversao

    else:
        st.error("Erro4")
        st.stop()

    if calc_bonificacao:
        df_bon["Qt Cx Bon"] = df_bon["Qt Cx"]*desconsidera_bonificacao
        df_bon["Qt un Bon"] = df_bon["Qt un"]*desconsidera_bonificacao

    linhas_com_guia = df[df["ICMS_CST"].isin(["00", "20"]) & (df["CEST"] != "")]
    if not linhas_com_guia.empty and not ignora_impostos:
        st.divider()
    
        if st.toggle("Já possuo retorno da contabilidade"):
            st.markdown("### Informe Calculo ST :blue[Contabilidade]")
            guia_st = solicita_input(linhas_com_guia, "guia_ST")

            df = df.merge(guia_st,how="left")
            
            if calc_bonificacao:
                df=df.merge(df_bon[["Descrição", "Qt Cx Bon", "Qt un Bon"]],how="left")
                df["Qt Cx"] = df["Qt Cx Bon"].fillna(0) + df["Qt Cx"]
                df["Qt un"] = df["Qt un Bon"].fillna(0) + df["Qt un"]
                            
            df["Valor Guia ST"] = df["Valor Guia ST"].fillna(0)
            df["Valor Total"] = df["Valor Original"] + df["V_ST"] + df["V_IPI"] + df["Valor Guia ST"] + df["V_FCPST"] - df["Valor Desconto"]
            df["Valor Cx"] = df["Valor Total"] / df["Qt Cx"]
            df["Valor un"] = df["Valor Total"] / df["Qt un"]


            total_impostos = df["V_ST"].sum()+df["V_IPI"].sum()+df["Valor Guia ST"].sum()-df["Valor Desconto"].sum()
            total_Valor_Total = round(df["Valor Total"].sum(),2)
            return df, df_bon, total_impostos, total_Valor_Total
        else:
            st.error(f"Contactar Contabilidade Nfe possui itens com CEST")
            st.stop()


    if calc_bonificacao:
        df=df.merge(df_bon[["Descrição", "Qt Cx Bon", "Qt un Bon"]],how="left")
        df["Qt Cx"] = df["Qt Cx Bon"].fillna(0) + df["Qt Cx"]
        df["Qt un"] = df["Qt un Bon"].fillna(0) + df["Qt un"]

    if not vl_total_nf == df["Valor Original"].sum() and not ignora_impostos:
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

    return df, df_bon, total_impostos, total_Valor_Total

# --- Interface Streamlit ---
st.set_page_config(page_title="Calculo NFe", layout="wide")
HOJE = datetime.now().date()
st.markdown("# :material/Docs: Calculo NF-e de Compras")
st.divider()
st.markdown("## :material/Upload: Importação de Arquivo xml")
calc_bonificacao = st.toggle("Calcular Bonificação")

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
    uploaded_file_2 = st.file_uploader("BONIFICAÇÃO - Arraste o XML da nota fiscal aqui", type="xml")

if uploaded_file:
    df, total_nf, soma_itens, emitente_nome, emitente_fantasia, Nr_Nfe, Boletos, pgto = processa_XML(uploaded_file)

    if calc_bonificacao:
        if uploaded_file_2:
            df_bon, _, _, emitente_nome_bon, emitente_fantasia_bon, Nr_Nfe_bon, _, _  = processa_XML(uploaded_file_2)
            if emitente_nome != emitente_nome_bon:
                st.error("NFs possuem emitente divergente")
                st.stop()
            if Nr_Nfe==Nr_Nfe_bon:
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

    ignora_impostos = st.toggle("Não considerar impostos")
    
    if calc_bonificacao:
        df_calculado, df_calculado_bon, imposto_somado, Valor_Total_Somado = calculos(df, total_nf, ignora_impostos,df_bon)
    else:
        df_calculado, _, imposto_somado, Valor_Total_Somado = calculos(df, total_nf, ignora_impostos, None)

    st.divider()
    st.markdown("## :material/Desktop_Mac: Informações Gerais")
    
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

    if Boletos:
        st.markdown(f"## :material/Payments: Boletos")
        if isinstance(Boletos, dict):
            qt_Boleto=1
            vl_total_boleto=float(Boletos["vDup"])
            Vencimento_Boleto = datetime.strptime(Boletos["dVenc"],"%Y-%m-%d")
        else:
            qt_Boleto = len(Boletos)
            vl_total_boleto = sum(float(boleto["vDup"]) for boleto in Boletos)
        st.markdown(f"### Boletos Emitidos: {qt_Boleto}")
        
        if vl_total_boleto==Valor_Total_Somado:
            st.markdown(f"### Valor Total :green[R$ {vl_total_boleto:,.2f}]".replace(".","x").replace(",",".").replace("x",","))
        elif vl_total_boleto==total_nf:
            st.markdown(f"### Valor Total :orange[R$ {vl_total_boleto:,.2f}]".replace(".","x").replace(",",".").replace("x",","))
        elif vl_total_boleto==soma_itens:
            st.markdown(f"### Valor Total :blue[R$ {vl_total_boleto:,.2f}]".replace(".","x").replace(",",".").replace("x",","))
        else:
            st.error("Boleto com valor divergente do Calculo")
            st.markdown(f"### Valor Total :red[R$ {vl_total_boleto}]")
        cols = st.columns(qt_Boleto)

        if qt_Boleto==1:
            with st.container(border=True):
                    st.markdown(f"Boleto: {Boletos["nDup"]}")
                    st.markdown(f"Valor: {vl_total_boleto:,.2f}".replace(".","x").replace(",",".").replace("x",","))
                    if Vencimento_Boleto>datetime.now():
                        st.markdown(f"Vencimento: {Vencimento_Boleto.date()}")
                    else:                            
                        st.markdown(f":red[:material/Close: Vencimento: {Vencimento_Boleto.date()}]")
        else:
            for i, boleto in enumerate(Boletos):
                Vencimento_Boleto = datetime.strptime(boleto["dVenc"],"%Y-%m-%d")
                with cols[i]:
                    with st.container(border=True):
                        st.markdown(f"Boleto: {boleto["nDup"]}")
                        st.markdown(f"Valor: {float(boleto["vDup"]):,.2f}".replace(".","x").replace(",",".").replace("x",","))
                        if Vencimento_Boleto>datetime.now():
                            st.markdown(f"Vencimento: {boleto["dVenc"]}")
                        else:                            
                            st.markdown(f":red[:material/Close: Vencimento: {boleto["dVenc"]}]")

        st.divider()
    elif pgto:
        forma_pgto = pgto["detPag"]["tPag"]
        valor_pgto = float(pgto["detPag"]["vPag"])
        if forma_pgto =="16":
            st.markdown(f"## :material/Payments: Depósito Bancário")
            if Valor_Total_Somado==valor_pgto:
                st.markdown(f"### Valor Total :green[R$ {valor_pgto:,.2f}]".replace(".","x").replace(",",".").replace("x",","))
            else:
                st.error("Boleto com valor divergente do Calculo")
                st.markdown(f"### Valor Total :red[R$ {valor_pgto}]")
        if forma_pgto =="15":
            st.markdown(f"## :material/Payments: Boleto Bancário")
            st.markdown(f"### Valor Total R$ {valor_pgto}")
        if forma_pgto =="90":
            st.markdown(f"## :material/Payments: Sem Pagamento")

        st.divider()
    else:
        st.error("Não foi possível encontrar Boleto na NFe")
        st.markdown(":material/Close: Não recebemos NF sem Boleto - Solicitar ao Motorista")
        st.markdown("Após receber Boleto verificar vencimento")
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
    coluna1, coluna2 = st.columns([3,1])
    with coluna1:
        colun1, colun2, colun3, colun4 = st.columns(4)
        with colun1:
            st.markdown(":material/Check_Box_Outline_Blank: Descarga Normal")
        with colun2:
            st.markdown(":material/Check_Box_Outline_Blank: Descarga Isenta")
        with colun3:
            st.markdown(":____________________________")
        with colun4:
            st.markdown(":________________Volumes")
    with coluna2:
        st.markdown(":material/Check_Box_Outline_Blank: Lista/Divisão: ________________")
        st.markdown(":material/Check_Box_Outline_Blank: Precificação: ________________")


    df_log = df_calculado[["Codigo Fornecedor",'Descrição']].copy()
    st.markdown(f"#### Produtos:")
    df_log.index=df_calculado["Item"]
    df_log['Qtd Contada'] = ""
    df_log['Data Validade'] = ""
    st.table(
        df_log,
        border="horizontal",
    )
    st.divider()