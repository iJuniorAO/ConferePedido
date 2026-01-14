import streamlit as st
import pandas as pd
import re
from datetime import datetime, time
import io


if not st.session_state["roles"] in ["administrador"]:
    st.markdown("# :material/block: Acesso Negado")
    st.stop()

# --- MELHORIAS ---
#   2. se a sigla estiver junto à descrição separar [cxBISCOITO] = [cx] [biscoito]

#Variaveis Iniciacao
AGORA = datetime.now()
PRAZO = time(10,0)
LOJAS = pd.DataFrame(
    {
        "Lojas": ["Abilio Machado", "Brigadeiro", "Cabana", "Cabral", "Caete", "Centro Betim", "Ceu Azul", "Eldorado", "Goiania", "Jardim Alterosa", "Lagoa Santa", "Laguna", "Laranjeiras", "Neves", "Nova Contagem", "Novo Progresso", "Palmital", "Para de Minas", "Pedra Azul", "Pindorama", "Santa Cruz", "Santa Helena", "São Luiz", "Serrano", "Silva Lobo", "Venda Nova", "Retirada em Loja"],
        "SECO": [False]*27,
        "CONG": [False]*27
    }
)

# --- Funções  ---
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
def confere_hr_pedido():
    if AGORA.time() >= time(10,5):
        st.write("❌ Prazo de Pedido finalizado!")
    elif AGORA.time() >= PRAZO:
        st.write("🕛 Prazo de Pedido finalizado! - Tolerância 5 minutos")
    elif AGORA.time() >= time(9,45):
        st.write("⚠️ Faltam 15min para fazerem pedidos")
    elif AGORA.time() >= time(9,0):
        st.write("🟠 Faltam 1 hora para o prazo do pedido ")
    else:
        st.write("🟢 Dentro do prazo para Pedidos")
def barra_lojas_pedido():
    enviados = lojas_editado["Pedido"].sum()
    total = len(lojas_editado)

    if enviados == total:
        texto_lojas = f"Lojas com Pedidos Realizados: :green[{enviados}]"
    elif enviados == 0:
        texto_lojas = f"Lojas com Pedidos Realizados: {enviados}"
    else:
        texto_lojas = f"Lojas com Pedidos Realizados: :red[{enviados}]"
    barra_lojas = st.progress(0, text=texto_lojas)

    progresso = (enviados/total)
    barra_lojas.progress(progresso, text=texto_lojas)


# -------------------------------
# --- Interface do Aplicativo ---
st.set_page_config(page_title="Corretor de Pedidos", page_icon="📦")
st.title("📦 Corretor de Arquivos de Pedido")

# --- hora ---
confere_hr_pedido()

# --- SubHeader ---
st.subheader("Lojas que realizaram pedido:")

# --- Tabela ---
lojas_editado = st.data_editor(
    LOJAS,
    hide_index=True
)

# --- Barra Lojas que fizeram pedidos ---
# barra_lojas_pedido()

# --- Subir arquivo --- 
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
    st.info("Faça upload de arquivo para iniciar a verificação.")


# ---------------
# --- SideBar ---
st.sidebar.markdown("""
## Correção Automática
### Correções implementadas:

1. O sistema remove espaços vazios no início.
2. Se o código estiver grudado no texto (ex: `10CX`), ele separa (`10 CX`).
3. Remove linhas vazias
4. Você baixa o arquivo pronto para uso.
""")

