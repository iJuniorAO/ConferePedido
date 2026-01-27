import streamlit as st
import pandas as pd
import numpy as np
import io
import re
import requests
from supabase import create_client, Client



# --- DEFINIÇÕES E CONSTANTES ---
@st.cache_data
def carregar_dados_onedrive(input_texto):
    try:
        # 1. Limpeza: Se o usuário colou o <iframe>, extrai apenas a URL
        url_match = re.search(r'src="([^"]+)"', input_texto)
        url = url_match.group(1) if url_match else input_texto
        
        # 2. Ajuste para SharePoint Business
        # Se for link de embed do SharePoint, mudamos para o modo de download
        if "sharepoint.com" in url:

            if "embed.aspx" in url:
                # Transforma o link de embed em um link de ação de download
                url = url.replace("embed.aspx", "download.aspx")
            elif "download=1" not in url:
                # Se for link de compartilhamento normal, força o download
                url = url + ("&" if "?" in url else "?") + "download=1"
        else:
            # Caso seja OneDrive Pessoal
            url = url.replace("embed", "download")

        # 3. Faz a requisição
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        
        return response.text
    except Exception as e:
        st.error(f"Erro ao processar URL: {e}")
        return None
def abrir_arquivo_txt(arquivo, colunas=None):
    try:
        if isinstance(arquivo, str):
            arquivo = io.StringIO(arquivo)
        return pd.read_csv(arquivo, sep="|", header=None, names=colunas, encoding="latin1")
    except Exception as e:
        st.error(f"Erro ao ler arquivo {e}")
        st.stop()

COLUNAS_PRODUTOS = ["CodProduto", "CodGrupo", "Descricao", "SiglaUn", "MinVenda", "PrecoUnPd", "CodPrincProd", "Estoq", "Obs", "Grade", "Falta", "Novo", "Prom", "DescMax", "Fam"]
COLUNAS_PRODUTOS_EXTRA = ["CodProduto", "Fam", "ListaCodCaract", "DescComplementar"]

#   --- INICIALIZAÇÃO   ---
st.set_page_config(page_title="Divisão", layout="wide")
st.markdown("# :material/Split_Scene: Divisão")

url=st.secrets["connections"]["supabase"]["url"]
key=st.secrets["connections"]["supabase"]["key"]

supabase: Client = create_client(url,key)
resposta_loja = supabase.table("Lojas").select("*").execute()

df_loja = pd.DataFrame(resposta_loja.data)

porc_total = df_loja["fator_porcentagem"].sum()
#editar fator_porcentagem
if porc_total != 100 or st.toggle("Alterar Fator de Porcentagem"):
    st.error(f":material/Exclamation: Corrigir para que o total fator de conversão seja 100,00%, atualmente em {porc_total:.2f}%")
    st.markdown("### Corrigir Fator de Porcentagem:")

    col1, col2 = st.columns(2,vertical_alignment="bottom")
    with col1:
        Loja_Selecionada = st.selectbox("Lojas", df_loja["Filial"])
    with col2:
        novo_fator_correcao = st.text_input("Digite Novo valor", max_chars=6, placeholder="000.00")
    if st.button("Confirmar Alteração",width="stretch"):
        try:
            resposta = (
                supabase.table("Lojas")
                .update({"fator_porcentagem":novo_fator_correcao})
                .eq("Filial", Loja_Selecionada)
                .execute()
            )
            st.success(f":material/Check: {resposta.data[0]["Filial"]} agora é {resposta.data[0]["fator_porcentagem"]}")
        except Exception as e:
            st.error(f"Erro ao realizar alteração {e}")
    st.divider()

st.markdown("## Lojas Cadastradas")
st.bar_chart(
    df_loja,
    x="Filial",
    y="fator_porcentagem",
    color="fator_porcentagem",
    horizontal=True,
    sort="-fator_porcentagem"
)


link_produto = st.secrets["onedrive"]["links"]["produto"]
link_produto_extra = st.secrets["onedrive"]["links"]["produto_extra"]
f_produto_auto = carregar_dados_onedrive(link_produto)
f_extra_auto = carregar_dados_onedrive(link_produto_extra)

df = abrir_arquivo_txt(f_produto_auto, COLUNAS_PRODUTOS)
df_extra = abrir_arquivo_txt(f_extra_auto, COLUNAS_PRODUTOS_EXTRA)

produtos_cadastrados = len(df)

df = df[df["Fam"] == 900000008].copy()
df = df.merge(df_extra[["CodProduto", "ListaCodCaract"]], on="CodProduto", how="left")

df = df[['CodProduto', 'CodGrupo', 'Descricao', 'Estoq', 'Fam', 'ListaCodCaract']]

CONDICOES = [
        df["ListaCodCaract"].astype(str).str.contains("000002", na=False),
        df["CodGrupo"].isin([9, 14])
    ]
df["TIPO"] = np.select(CONDICOES, ["PESO", "CONG"], default="SECO")
df["Qt Cx Total"] = 0
df = df[["CodProduto", "TIPO", "Descricao", "Estoq", "Qt Cx Total"]].sort_values("Estoq",ascending=False)

st.divider()
st.markdown("## Fazer Nova Divisão")

df_divisao = st.data_editor(
    df,
    hide_index=True
)

df_divisao = df_divisao[df_divisao["Qt Cx Total"]>0]
ultimo = df_divisao["Descricao"].astype(str).str.split().str[-1]
df_divisao["CONV"] = np.where(ultimo.str.isdigit(), ultimo, 1).astype(float)
df_divisao["Codigo"] = df_divisao["CodProduto"].astype(str).str.rjust(13)


df_loja = df_loja[["Filial", "fator_porcentagem"]]
df_divisao = df_divisao[["Codigo", "Descricao", "CONV","Estoq", "Qt Cx Total"]]

df_resultado = pd.merge(df_loja, df_divisao, how='cross')
df_resultado["Qt Cx Loja"] = df_resultado["Qt Cx Total"] * (df_resultado["fator_porcentagem"]/100)
df_resultado["Qt_ERP"] = df_resultado["Qt Cx Loja"] * df_resultado["CONV"]

df_resultado = df_resultado[["Filial", "Codigo", "Descricao", "Qt Cx Total", "Qt Cx Loja", "Qt_ERP"]]

st.divider()

if df_resultado.empty:
    st.info(":material/Exclamation: Nenhum item selecionado")
    st.stop()

st.markdown("## Tabela da Divisão")

df_resultado_produto = df_resultado.pivot_table(
    index='Descricao', 
    columns='Filial', 
    values='Qt Cx Loja', 
    aggfunc='sum'
)


df_resultado_produto = np.trunc(df_resultado_produto)
if False:
    df_resultado_produto["Total Distribuído"] = df_resultado_produto.sum(axis=1)

df_referencia = df_divisao.set_index("Descricao")["Qt Cx Total"]
df_resultado_produto["Qt Cx Planejada"] = df_resultado_produto.index.map(df_referencia)

st.markdown("### Correção de Administrativo")
df_resultado_editado = st.data_editor(
    df_resultado_produto
)
df_resultado_editado["Total Distribuído2"] = df_resultado_editado.sum(axis=1) - df_resultado_produto["Qt Cx Planejada"]
st.divider()    
st.markdown("### Conferência de Distribuição (Qt Cx Loja)")
st.dataframe(df_resultado_editado)


# 1. Calcular a diferença absoluta entre o planejado e o que foi distribuído
df_resultado_editado["Diferença"] = df_resultado_editado["Total Distribuído2"] - df_resultado_editado["Qt Cx Planejada"]

# 2. Filtrar apenas as divergências (onde a diferença não é zero)
df_divergencias = df_resultado_editado[df_resultado_editado["Diferença"] != 0][["Qt Cx Planejada", "Total Distribuído2", "Diferença"]]

if not df_divergencias.empty:
    st.error(":material/warning: Itens com divergência na distribuição!")
    st.markdown("### Tabela de Divergências")
    st.dataframe(df_divergencias)


def colorir_divergencia(row):
    # Se a diferença for diferente de 0, pinta o fundo da linha de vermelho suave
    color = 'background-color: #ffcccc' if row["Diferença"] != 0 else ''
    return [color] * len(row)

# Aplicar a estilização na tabela editada
df_estilizado = df_resultado_editado.style.apply(colorir_divergencia, axis=1)

st.divider()
st.markdown("### Conferência de Distribuição (Qt Cx Loja)")
# Exibir a tabela com o estilo aplicado
st.dataframe(df_estilizado)



# 1. Calculando a diferença
df_resultado_editado["Diferença"] = df_resultado_editado["Total Distribuído2"] - df_resultado_editado["Qt Cx Planejada"]

# 2. Criando uma coluna de Status visual para facilitar a batida de olho
df_resultado_editado["Status"] = df_resultado_editado["Diferença"].apply(
    lambda x: "⚠️ Erro" if x != 0 else "✅ OK"
)

# 3. Exibindo a Tabela de Divergências (apenas se houver erro)
df_divergencias = df_resultado_editado[df_resultado_editado["Diferença"] != 0]

if not df_divergencias.empty:
    st.error("### 🚨 Itens com Diferença na Distribuição")
    st.dataframe(
        df_divergencias[["Qt Cx Planejada", "Total Distribuído2", "Diferença"]],
        use_container_width=True
    )

st.divider()

# 4. Tabela Principal com configuração de colunas (estética limpa)
st.markdown("### Conferência de Distribuição Final")
st.dataframe(
    df_resultado_editado,
    column_config={
        "Status": st.column_config.TextColumn("Status"),
        "Diferença": st.column_config.NumberColumn(
            "Diferença",
            help="Valor deve ser 0 para estar correto",
            format="%.2f" # Ajuste conforme necessário
        ),
    },
    use_container_width=True
)


def destacar_descricao(row):
    # Verifica se há diferença
    cor = 'color: red; font-weight: bold' if row["Diferença"] != 0 else ''
    # Retorna o estilo apenas para a coluna 'Descricao', as outras ficam vazias
    return [cor if col == 'Descricao' else '' for col in row.index]

# Aplicando o estilo
df_estilizado = df_resultado_editado.style.apply(destacar_descricao, axis=1)

st.markdown("### Conferência de Distribuição")
st.dataframe(df_estilizado, use_container_width=True)

# Criar uma cópia para exibição
df_visualizacao = df_resultado_editado.copy()

# Modifica a descrição se houver diferença
df_visualizacao["Descricao"] = df_visualizacao.apply(
    lambda x: f"⚠️ {x.name}" if x["Diferença"] != 0 else x.name, 
    axis=1
)

st.markdown("### Itens para Revisão")
st.dataframe(df_visualizacao, use_container_width=True)


# 1. Calculamos a diferença
df_resultado_editado["Diferença"] = df_resultado_editado["Total Distribuído2"] - df_resultado_editado["Qt Cx Planejada"]

# 2. Criamos uma lista com os novos nomes para o index
novos_nomes_index = [
    f"⚠️ {idx}" if dif != 0 else idx 
    for idx, dif in zip(df_resultado_editado.index, df_resultado_editado["Diferença"])
]

# 3. Aplicamos os novos nomes
df_resultado_editado.index = novos_nomes_index

st.markdown("### Conferência de Distribuição")
st.dataframe(df_resultado_editado, use_container_width=True)


"OPÇÃO 1"

# 1. Calculamos a diferença
df_resultado_editado["Diferença"] = df_resultado_editado["Total Distribuído2"] - df_resultado_editado["Qt Cx Planejada"]

# 2. Criamos uma lista com os novos nomes para o index
novos_nomes_index = [
    f"⚠️ {idx}" if dif != 0 else idx 
    for idx, dif in zip(df_resultado_editado.index, df_resultado_editado["Diferença"])
]

# 3. Aplicamos os novos nomes
df_resultado_editado.index = novos_nomes_index

st.markdown("### Conferência de Distribuição")
st.dataframe(df_resultado_editado, use_container_width=True)


"OPÇÃO 2"

def estilo_index(df):
    # Criamos uma série de estilos vazios
    estilos = pd.Series('', index=df.index)
    # Onde houver diferença, aplicamos o vermelho
    mask = df["Diferença"] != 0
    estilos[mask] = 'color: red; font-weight: bold;'
    return estilos

# Aplicando o estilo especificamente ao Index
df_estilizado = df_resultado_editado.style.apply(
    lambda x: ['color: red' if df_resultado_editado.loc[x.name, "Diferença"] != 0 else '' for _ in x], 
    axis=1
)

st.dataframe(df_estilizado, use_container_width=True)


"OPÇÃO 3"

# Filtrar apenas o que está errado
df_divergentes = df_resultado_editado[df_resultado_editado["Diferença"] != 0].copy()

if not df_divergentes.empty:
    st.error("### 🔍 Itens com erro de cálculo")
    # Criamos a tabela de conferência
    conferencia = df_divergentes[["Qt Cx Planejada", "Total Distribuído2", "Diferença"]]
    st.table(conferencia)

if False:
    "teste1"
    df_resultado_produto = df_resultado.pivot_table(
        index='Descricao', 
        columns='Filial', 
        values='Qt Cx Loja', 
        aggfunc='sum'
    )
    "resultado produto original"
    df_resultado_produto

    df_resultado_produto = np.trunc(df_resultado_produto)
    "resultado produto round"
    df_resultado_produto
    df_resultado_produto["Total"] = df_resultado_produto.sum(axis=1)
    "resultado produto total"
    df_resultado_produto
    df_resultado_produto["Qt Cx Total"] = df_resultado["Qt Cx Total"]

    "saida"
    df_resultado_produto 

    if st.button("Salvar divisão", width="stretch"):
        "salvo"
        "arquivo txt"




