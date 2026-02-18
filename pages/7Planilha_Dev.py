import streamlit as st
import pandas as pd
import xmltodict
import io

st.set_page_config(page_title="Conversor NFe", layout="wide")

st.title(":material/Add_Notes: Automação de XML para Controle")

arquivos_xml = st.file_uploader(
    "Selecione os arquivos XML", 
    type=['xml'], 
    accept_multiple_files=True
)

if arquivos_xml:
    dados_finais = []
    Nfs_erradas=[]
    
    for arquivo in arquivos_xml:
        conteudo = arquivo.read()
        dict_nfe = xmltodict.parse(conteudo)

              
        if 'nfeProc' in dict_nfe:
            infNFe = dict_nfe['nfeProc']['NFe']['infNFe']
        else:
            infNFe = dict_nfe['NFe']['infNFe']

        #infNFe
        finalidade_nfe = infNFe["ide"]["finNFe"]
        destinatario = infNFe['dest']['CNPJ']
        nr_NFe = infNFe["ide"]["nNF"]

        emissor = infNFe["emit"]["xNome"]
        
        if finalidade_nfe != "4":
            Nfs_erradas.append((nr_NFe,"dev",arquivo.name))
            continue
        
        if destinatario != "42500350000167":
            Nfs_erradas.append((nr_NFe,"spm"))
            continue

        detalhes = infNFe['det']
        if not isinstance(detalhes, list):
            detalhes = [detalhes]

        for item in detalhes:
            prod = item['prod']
            dados_finais.append({
                'loja': emissor,
                "Nf Compra": "",
                "NFD": nr_NFe,
                'cod produto': prod['cProd'],
                'produto': prod['xProd'],
                "Qtd un.": prod["qCom"].replace(".",","),
                'vl un': prod['vUnCom'].replace(".",","),
                "":"",
                'vl Total': prod['vProd'].replace(".",",")
            })

    if Nfs_erradas:
        st.divider()
        st.markdown(f"### :material/Close: Erro ao importar :red[{len(Nfs_erradas)}] NFs")
        with st.expander("Ver erros"):
            for nf in Nfs_erradas:
                if nf[1]=="dev":
                    st.write(f"NF {nf[0]} - Não é devolução - {nf[2]}")
                elif nf[1]=="spm":
                    st.write(f"NF {nf[0]} - Não foi emitido para SPM - {nf[2]}")
                else:
                    st.write(f"NF {nf[0]} - ERRO - {nf[2]}")
        st.divider()

    if dados_finais:
        df = pd.DataFrame(dados_finais)

        # Formatação visual para o Streamlit (opcional)
        st.subheader(":material/Download_Done: Dados Extraídos")

        st.dataframe(df,
            use_container_width=True,
            hide_index=True
            )
else:
    st.info("Arraste os XMLs aqui para começar.")