import pandas as pd
import numpy as np
import io

# --- DEFINIÇÕES DE FUNÇÕES, VARIÁVEIS e CONSTANTES ---
def abrir_txt(caminho_arquivo,colunas):
    try:
        dfLocal = pd.read_csv(caminho_arquivo, sep="|", header=None, names=colunas, encoding="latin1")
        return dfLocal
    except FileNotFoundError:
        print("❗Erro: O arquivo .txt não foi encontrado.")
def importa_pedido_loja(caminho_arquivo):
    caminho_arquivo = r"C:\Users\Ismael\OneDrive - Mumu\BaseDados\Brigadeiro2.txt"
    df_Import_loja = pd.read_csv(caminho_arquivo, sep="|", header=None, encoding="latin1")

    #Importa e prepara o df
    df_Import_loja[colunas_Pedidos] = (
        df_Import_loja[0]
        .astype(str)
        .str.split(" ", n=2, expand=True)
    )

    df_Import_loja = df_Import_loja.drop(columns=[0,"Sigla"])

    #Separa os pedidos em 2 df um com erros e outro sem erros
    num = pd.to_numeric(df_Import_loja["QtCx"], errors="coerce")
    df_ok = df_Import_loja[num.notna()]
    df_erro = df_Import_loja[num.isna()]
    df_ok.loc[:,"QtCx"] = df_ok["QtCx"].astype(float)
    
    return df_ok, df_erro  
def trata_erros(dfLocal):
    if len(dfLocal.columns) == 2:
        dfLocal["Linha"] = dfLocal["QtCx"].fillna("").astype(str) + " " + dfLocal["Descricao"].fillna("").astype(str)
        dfLocal = dfLocal["Linha"]
        for i, texto in dfLocal.items():
            print(f"[Linha {i}] - {texto} ")

    elif len(dfLocal.columns) == 6:
        dfLocal["Linha"] = dfLocal["QtCx"].astype(str) + " " + dfLocal["Descricao"].astype(str)
        dfLocal =  dfLocal["Linha"]
        print(dfLocal)

colunas_produto = [
    "CodProduto",
    "CodGrupo",
    "Descricao",
    "SiglaUn",
    "MinVenda",
    "PrecoUnPd",
    "CodPrincProd",
    "Estoq",
    "Obs",
    "Grade",
    "Falta",
    "Novo",
    "Prom",
    "DescMax",
    "Fam"
]
colunas_produto_extra =[
    "CodProduto",
    "Fam",
    "ListaCodCaract",
    "DescComplementar"    
]
colunas_Pedidos = [
    "QtCx",
    "Sigla",
    "Descricao"
]

# --- INÍCIO DO FLUXO PRINCIPAL ---
print("\n PROGRAMA PARA CONVERTER PEDIDO.TXT PARA IMPORTAÇÃO 💾 \n")

#   1. Abrir o arquivo de produtos.txt e produtosextra.txt atualizado (diário)
try:
    caminho_arquivo = r"C:\Users\Ismael\OneDrive - Mumu\BaseDados\NOVO\00001produto.txt"
    df = abrir_txt(caminho_arquivo,colunas_produto)
except:
    print("❌ Erro ao abrir produto.txt")
    pass

try:
    caminho_arquivo = r"C:\Users\Ismael\OneDrive - Mumu\BaseDados\NOVO\00001produtoextra.txt"
    df_extra = abrir_txt(caminho_arquivo,colunas_produto_extra)
except:
    print("❌ Erro ao abrir produtoextra.txt")
    pass

#   --- Filtros do DF (melhora processamento) ---
df = df[["CodProduto", "CodGrupo", "Descricao", "Estoq", "Fam"]]
df = df[df["Fam"] != 900000008]
df = df[df["Estoq"] > 0]


#   2. INSERE INFORMAÇÕES DO PRODUTO_EXTRA NO PRODUTO E TRATA AS INFORMAÇÕ0ES
#       a. Procv Produto_extra.txt > Produto.txt
df = df.merge(
    df_extra[["CodProduto", "ListaCodCaract"]],
    on = "CodProduto",
    how="left"
)

#       b. Coluna de Grupos seguindo a regra
            #   1º Se for balança coluna                TIPO = PESO
            #   2º Se fordo grupo CONG ou REFR coluna   TIPO = CONG
            #   3º Os demais                            TIPO = SECO
df["TIPO"] = "SECO"
df.loc[df["CodGrupo"].isin([9,14]), "TIPO"] = "CONG"
df.loc[df["ListaCodCaract"].astype(str).str.contains("000002"), "TIPO"] = "PESO"

#       c. Fator de conversão que é o ultimo caracter
ultimo = (df["Descricao"].astype(str).str.split().str[-1])
df["CONV"] = np.where(
    ultimo.str.isdigit(),
    ultimo,
    1
).astype(float)

#   FILTRA df e insere no df_Pedido
df_Pedido = df
#Padroniza 13 digitos no código
df_Pedido.insert(0,"Codigo", df_Pedido["CodProduto"].astype(str).str.rjust(13, '0'))
df_Pedido = df_Pedido[["Codigo", "Descricao", "TIPO", "CONV"]]


#   3 PEGA O PEDIDO DA LOJA E INSERE NO DF
#loja_pedido = input("\n\t🔹Digite a loja Escolhida: ")
loja_pedido = "teste"


try:
    #   a. Importa Pedido_Loja
    caminho_arquivo = r"C:\Users\Ismael\OneDrive - Mumu\BaseDados\Brigadeiro2.txt"
    df_Pedido_Loja, df_Erro_Qt = importa_pedido_loja(caminho_arquivo)

    if not df_Pedido_Loja.empty and df_Erro_Qt.empty:
        print(f"\n🟢 Todos itens da Loja: {loja_pedido} importado com sucesso\n")
    elif not df_Pedido_Loja.empty:
        print(f"\n🟠 Pedido da Loja: '{loja_pedido}' importado com ressalva\n")

    #   b. Procv Pedido_loja
    df_Pedido = df_Pedido.merge(
        df_Pedido_Loja[["QtCx", "Descricao"]],
        on = "Descricao",
        how="outer",
        indicator=True,
    )

    df_Erro_Desc = df_Pedido[df_Pedido["_merge"] == "right_only"]


    #   c. Insere fator de conversão
    df_Pedido = df_Pedido[df_Pedido["QtCx"].notna()]
    df_Pedido[loja_pedido] = df_Pedido["QtCx"] * df_Pedido["CONV"]


    #   4. PEGA OS TXT CONFORME AS 3 CLASSIFICAÇÕES (PESO/CONG/SECO)
    # Formatação numérica: 9 dígitos, 3 após a vírgula, trocando ponto por vírgula
    df_Pedido[loja_pedido] = df_Pedido[loja_pedido].map(
        lambda x: f"{x:09.3f}".replace(".", ",") if isinstance(x, (int, float)) else "00000,000"
    )

    df_Pedido_SECO = df_Pedido[df_Pedido["TIPO"] == "SECO"]
    df_Pedido_SECO = df_Pedido_SECO[["Codigo", loja_pedido]]

    df_Pedido_CONG = df_Pedido[df_Pedido["TIPO"] == "CONG"]
    df_Pedido_CONG = df_Pedido_CONG[["Codigo", loja_pedido]]

    df_Pedido_PESO = df_Pedido[df_Pedido["TIPO"] == "PESO"]
    df_Pedido_PESO = df_Pedido_PESO[["Codigo", loja_pedido]]

    if df_Pedido_PESO.empty:
        print("🟠 [Pedido PESO]\t Não Gerado - sem Itens PESO")
    else:
        print("🟢 [Pedido PESO]\t Gerado com sucesso")
        df_Pedido_PESO.to_csv("Pedido_PESO.txt", sep="\t", index=False)

    if df_Pedido_SECO.empty:
        print("🟠 [Pedido SECO]\t Não Gerado - sem Itens SECO")
    else:
        print("🟢 [Pedido SECO]\t Gerado com sucesso")

        df_Pedido_SECO.to_csv("Pedido_SECO.txt", sep="\t", index=False)

    if df_Pedido_CONG.empty:
        print("🟠 [Pedido CONG/REFR]\t Não Gerado - sem Itens CONG/REFR")
    else:
        print("🟢 [Pedido CONG/REFR]\t Gerado com sucesso")
        df_Pedido_CONG.to_csv("Pedido_CONG.txt", sep="\t", index=False)


    if not df_Erro_Qt.empty:
        print(f"\n❌ Não foi possível identificar Qt em {len(df_Erro_Qt)} linhas")
        trata_erros(df_Erro_Qt)
    if not df_Erro_Desc.empty:
        print(f"\n❌ Não foi possível verificar descrição em {len(df_Erro_Desc)} linhas")
        trata_erros(df_Erro_Desc)
except:
    print("❌ [ERRO]Não foi possível importar pedido")