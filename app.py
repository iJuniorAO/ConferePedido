import streamlit as st
import pandas as pd
import re
import io


#Variaveis Iniciacao

LOJAS = pd.DataFrame(
    {
        "Lojas": ["Abilio Machado", "Brigadeiro", "Cabana", "Cabral", "Caete", "Centro Betim", "Ceu Azul", "Eldorado", "Goiania", "Jardim Alterosa", "Lagoa Santa", "Laguna", "Laranjeiras", "Neves", "Nova Contagem", "Novo Progresso", "Palmital", "Para de Minas", "Pedra Azul", "Pindorama", "Santa Cruz", "Santa Helena", "São Luiz", "Serrano", "Silva Lobo", "Venda Nova", "Retirada em Loja"],
        "Enviado": [False]*27   
    }
)




# --- Função de Correção ---
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


# --- Interface do Aplicativo ---
st.set_page_config(page_title="Corretor de Pedidos", page_icon="📦")
st.title("📦 Corretor de Arquivos de Pedido")


st.data_editor(
    LOJAS,
    column_config={
        "Enviado": st.column_config.CheckboxColumn(
            "Enviado",
            help="Selecione as lojas enviadas",
            default=False,
        )
    },
    hide_index=True
)

texto_lojas = "Pedido em progresso"
barra_lojas = st.progress(0, text=texto_lojas)
total = len(LOJAS)
enviados = LOJAS["Enviado"].sum()
progresso = (enviados/total)
barra_lojas.progress(progresso, text=texto_lojas)

st.write(enviados)
st.write(total)
st.write(progresso)

st.write(LOJAS)



uploaded_file = st.file_uploader("Suba seu arquivo *.txt aqui*", type="txt")

if uploaded_file:
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

    # Exibição dos resultados
    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Correções sugeridas", alteracoes_feitas)
    col2.metric("Erros manuais", len(erros_nao_corrigidos))
    col3.metric("Linhas vazias removidas", linhas_removidas)

    if alteracoes_feitas > 0 or linhas_removidas>0:
        st.success(f"Foram identificadas e corrigidas {alteracoes_feitas+linhas_removidas} linhas!")
        
        # --- O BOTÃO DE DOWNLOAD ---
        # Preparamos o texto final
        texto_corrigido = "\n".join(linhas_novas)
        
        st.download_button(
            label="📥 BAIXAR ARQUIVO CORRIGIDO",
            data=texto_corrigido,
            file_name="pedido_atualizado.txt",
            mime="text/plain",
            help="Clique aqui para baixar o arquivo com as correções aplicadas",
            use_container_width=True # Deixa o botão grande e visível
        )
        # ---------------------------
        
    if erros_nao_corrigidos:
        with st.expander("Ver linhas com erros que exigem atenção manual"):
            for erro in erros_nao_corrigidos:
                st.warning(erro)

else:
    st.info("Aguardando upload de arquivo para iniciar a verificação.")

st.sidebar.markdown("""
## Correção Automática
### Correções implementadas:

1. O sistema remove espaços vazios no início.
2. Se o código estiver grudado no texto (ex: `10CX`), ele separa (`10 CX`).
3. Remove linhas vazias
4. Você baixa o arquivo pronto para uso.
""")

# --- MELHORIAS ---
#   2. se a sigla estiver junto à descrição separar [cxBISCOITO] = [cx] [biscoito]

