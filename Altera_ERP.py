import pandas as pd
import numpy as np
import io

#   MELHORIAS Ver. DEFINITIVA
#   1. Filtrar df Estoq>0 no inicio para melhorar tempo de processamento  

# --- DEFINIÇÕES DE FUNÇÕES, VARIÁVEIS e CONSTANTES ---
def abrir_txt(caminho_arquivo,colunas):
    try:
        dfLocal = pd.read_csv(caminho_arquivo, sep="|", header=None, names=colunas, encoding="latin1")
        return dfLocal
    except FileNotFoundError:
        print("❗Erro: O arquivo .txt não foi encontrado.")
def Preparadf(dfLocal, nome_loja):
    # Filtra apenas onde a loja tem valor > 0
    dfLocal = dfLocal[dfLocal[nome_loja] > 0].copy()
    
    # Calcula quantidade em caixa
    dfLocal["QtCx"] = dfLocal[nome_loja] * dfLocal["conv"]
    
    # Seleciona e formata as colunas
    dfLocal = dfLocal[["Codigo", "QtCx"]]
    
    # Insere a coluna da loja no início
    dfLocal.insert(0, nome_loja, dfLocal["Codigo"])
    dfLocal = dfLocal[[nome_loja, "QtCx"]]
    
    # Formatação numérica: 9 dígitos, 3 após a vírgula, trocando ponto por vírgula
    dfLocal["QtCx"] = dfLocal["QtCx"].map(
        lambda x: f"{x:09.3f}".replace(".", ",") if isinstance(x, (int, float)) else "00000,000"
    )

    return dfLocal
def salvar_txt(dfLocalTXT, nome_arquivo):
    # Salva o resultado em um arquivo físico .txt
    dfLocalTXT.to_csv(nome_arquivo, sep="\t", index=False, header=False, decimal=",")
    print(f"Arquivo {nome_arquivo} gerado com sucesso.")
def main():  
    # 2. Definir a loja manualmente (já que não temos o campo G2 do Excel)
    # Aqui você coloca o nome da coluna que representa a loja
    loja_pedido = input("Digite a loja Escolhida: ")

    # loja_pedido = "Loja_01"           == ex GEMINI

    # Limpeza inicial
    #df = LimpaDataFrame(df)

    # Separação por tipo
    dfseco = df[df["Tipo"] == "S"]
    dfcong = df[df["Tipo"] == "C"]
    dfpeso = df[df["Tipo"] == "P"]

    # Processamento e exportação
    if loja_pedido in df.columns:
        # Processa Seco
        dfsecoLoja = Preparadf(dfseco, loja_pedido)
        salvar_txt(dfsecoLoja, "resultado_seco.txt")

        # Processa Congelado
        dfcongLoja = Preparadf(dfcong, loja_pedido)
        salvar_txt(dfcongLoja, "resultado_congelado.txt")

        # Processa Peso
        dfpesoLoja = Preparadf(dfpeso, loja_pedido)
        salvar_txt(dfpesoLoja, "resultado_peso.txt")
    else:
        print(f"Erro: A coluna da loja '{loja_pedido}' não foi encontrada no arquivo.")
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
print("\n PROGRAMA PARA CONVERTER PEDIDO.TXT PARA IMPORTAÇÃO 💾 \n\n")

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
#df_Pedido = df[df["Estoq"] > 0]
df_Pedido = df
df_Pedido.insert(0,"Codigo", df_Pedido["CodProduto"].astype(str).str.rjust(13, '0'))
df_Pedido = df_Pedido[["Codigo", "Descricao", "TIPO", "CONV"]]

#   3 PEGA O PEDIDO DA LOJA E INSERE NO DF

#loja_pedido = input("\n\t🔹Digite a loja Escolhida: ")
loja_pedido = "teste"


#   a. Importa Pedido_Loja
caminho_arquivo = r"C:\Users\Ismael\OneDrive - Mumu\BaseDados\Brigadeiro2.txt"
df_Pedido_Loja, df_Erro_Loja = importa_pedido_loja(caminho_arquivo)

if not df_Pedido_Loja.empty:
    print(f"\n🟢 Pedido Lojas importado")
if not df_Erro_Loja.empty:
    print(f"❌ Linhas com Erro:\n{df_Erro_Loja}\n\n")


#   b. Procv Pedido_loja
df_Pedido = df_Pedido.merge(
    df_Pedido_Loja[["QtCx", "Descricao"]],
    on = "Descricao",
    how="left"
)
#Aqui será retirado a lista para as lojas:

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
    print("🟠 Pedido PESO sem Itens")
else:
    print("🟢 Gerado Pedido PESO")
    df_Pedido_PESO.to_csv("Pedido_PESO.txt", sep="\t", index=False)

if df_Pedido_SECO.empty:
    print("🟠 Pedido SECO sem Itens")
else:
    print("🟢 Gerado Pedido SECO")

    df_Pedido_SECO.to_csv("Pedido_SECO.txt", sep="\t", index=False)

if df_Pedido_CONG.empty:
    print("🟠 Pedido CONG/REFR sem Itens")
else:
    print("🟢 Gerado Pedido CONG/REFR")
    df_Pedido_CONG.to_csv("Pedido_CONG.txt", sep="\t", index=False)