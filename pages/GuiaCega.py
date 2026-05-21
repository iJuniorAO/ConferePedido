import streamlit as st
import xmltodict
import pandas as pd
from utils import layout_guia_cega

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

    # Inicializa o PDF em modo Retrato (P), milímetros (mm) e formato A4
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_margins(5, 5, 5)
    pdf.add_page()
    
    # --- 1. CABEÇALHO ---
    pdf.set_font("Arial", "B", 14)
    # Título da Logística (alinhado à esquerda)
    pdf.cell(110, 10, "Logistica: Conferencia Cega", ln=0, align="L")
    
    pdf.set_font("Arial", "", 11)
    # Linha para assinatura do conferente (alinhado à direita)
    pdf.cell(80, 10, "Conferido por: _________________", ln=1, align="R")
    pdf.ln(3)
    
    # --- 2. DADOS DO EMITENTE E NF-E ---
    emitente_fantasia = resposta_xml["emitente"]["emitente_fantasia"]
    emitente_nome = resposta_xml["emitente"]["emitente_nome"]
    nr_nfe = resposta_xml["nr_Nfe"]
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(20, 6, "Emitente: ", ln=0)
    pdf.set_font("Arial", "", 10)
    pdf.cell(170, 6, f"{emitente_fantasia} - {emitente_nome}", ln=1)
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(20, 6, "Nº NFe: ", ln=0)
    pdf.set_font("Arial", "", 10)
    pdf.cell(170, 6, f"{nr_nfe}", ln=1)
    pdf.ln(5)
    
    # --- 3. GRID DE CHECKBOXES E CAMPOS OPERACIONAIS ---
    # Largura total útil da página A4 com margens de 10mm é 190mm (190 / 4 colunas = 47.5mm)
    y_atual = pdf.get_y()
    
    # Coluna 1
    pdf.set_xy(10, y_atual)
    pdf.cell(47.5, 5, "______ / ______", ln=0)
    pdf.set_xy(10, y_atual + 6)
    pdf.cell(47.5, 5, ":_____________ Ordem", ln=0)
    
    # Coluna 2
    pdf.set_xy(10 + 47.5, y_atual)
    pdf.cell(47.5, 5, "[ ] Descarga Normal", ln=0)
    pdf.set_xy(10 + 47.5, y_atual + 6)
    pdf.cell(47.5, 5, "[ ] Descarga Isenta", ln=0)
    
    # Coluna 3
    pdf.set_xy(10 + (47.5 * 2), y_atual)
    pdf.cell(47.5, 5, "[ ] Descarga Fixa", ln=0)
    pdf.set_xy(10 + (47.5 * 2), y_atual + 6)
    pdf.cell(47.5, 5, "R$:_________________", ln=0)
    
    # Coluna 4
    pdf.set_xy(10 + (47.5 * 3), y_atual)
    pdf.cell(47.5, 5, "[ ] Lista", ln=0)
    pdf.set_xy(10 + (47.5 * 3), y_atual + 6)
    pdf.cell(47.5, 5, "[ ] Divisao", ln=1)
    
    pdf.ln(8) # Espaçamento antes da tabela
    
    # --- 4. CRIAÇÃO DA TABELA DE PRODUTOS ---
    # Definição exata das larguras das colunas para fechar em 190mm
    # Item(12) + Cod Forn(23) + Descrição(65) + Un por Cx(20) + Qtd Cx(25) + Validade(25) + Palete(20) = 190mm
    colunas = ["Item", "Cod Forn.", "Descricao", "Un por Cx", "Qtd Cx Cont.", "Data Valid.", "Qtd Palete"]
    larguras = [12, 23, 65, 20, 25, 25, 20]
    
    # Cabeçalho da Tabela (Cinza claro estilizado)
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(230, 230, 230)
    for col, larg in zip(colunas, larguras):
        pdf.cell(larg, 7, col, border=1, align="C", fill=True)
    pdf.ln()
    
    # Processando os dados do XML idêntico ao seu DataFrame original
    df_log = resposta_xml["df"][["Codigo Fornecedor", "Descrição"]].copy()
    df_log = df_log.rename(columns={"Codigo Fornecedor": "Cod Forn."})
    df_log.index = resposta_xml["df"]["Item"]
    
    # Linhas da Tabela
    pdf.set_font("Arial", "", 9)
    for item, row in df_log.iterrows():
        # Item (Index) e Código
        pdf.cell(larguras[0], 9, str(item), border=1, align="C")
        pdf.cell(larguras[1], 9, str(row["Cod Forn."]), border=1, align="C")
        
        # Tratamento de tamanho para a descrição não estourar a célula
        desc = str(row["Descrição"])
        if len(desc) > 34:
            desc = desc[:31] + "..."
        pdf.cell(larguras[2], 9, desc, border=1, align="L")
        
        # Células vazias com borda estruturada (altura de 9mm ideal para escrita manual)
        pdf.cell(larguras[3], 9, "", border=1)
        pdf.cell(larguras[4], 9, "", border=1)
        pdf.cell(larguras[5], 9, "", border=1)
        pdf.cell(larguras[6], 9, "", border=1)
        pdf.ln()
        
    # Retorna o arquivo gerado em formato de bytes brutos (In-memory)
    return pdf.output()

# --- Interface Streamlit ---
st.set_page_config(page_title="Calcula NFe", layout="wide")
st.markdown("# :material/Adf_scanner: Calculo NF-e de Compras")
st.markdown("## :material/Upload: Importação de Arquivo xml")

uploaded_file = st.file_uploader("NFe - Arraste o XML da nota fiscal aqui", type="xml")
if (not uploaded_file):
    st.info("Insira o XML para iniciar imprimir a Guia Cega")
    st.divider()
    st.stop()

resposta_xml = processa_XML(uploaded_file)

st.divider()
selecao_conf_cega = st.toggle("Layout Secundário")

df_log = layout_guia_cega(resposta_xml)

if selecao_conf_cega:
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
