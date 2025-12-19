import pandas as pd
import io

# --- DEFINIÇÕES DE FUNÇÕES E VARIÁVEIS ---
def abrir_txt(caminho_arquivo):
    try:
        dfLocal = pd.read_csv(caminho_arquivo, sep="|", header=None, names=colunas, encoding="latin1")
        return dfLocal
    except FileNotFoundError:
        print("❗Erro: O arquivo .txt não foi encontrado.")
def LimpaDataFrame(dfLocal):
    # Remove linhas onde "Codigo" está em branco
    dfLocal = dfLocal[dfLocal["Codigo"].notna()].copy()

    # Remove colunas desnecessárias
    colunas_para_remover = ["Sigla", "Peso"]
    # Usamos errors='ignore' para evitar erro caso a coluna não exista
    dfLocal = dfLocal.drop(columns=colunas_para_remover, errors='ignore')

    # ---- 1. Corrigir coluna A (13 caracteres com preenchimento à esquerda)
    dfLocal["Codigo"] = dfLocal["Codigo"].astype(str).str.strip().str.rjust(13, '0')
    return dfLocal  
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
    df = LimpaDataFrame(df)

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

colunas = [
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


# --- INÍCIO DO FLUXO PRINCIPAL ---

print("\n PROGRAMA PARA CONVERTER PEDIDO.TXT PARA IMPORTAÇÃO 💾 \n\n")

# 1. Abrir o arquivo de produtostxt atualizado (diário)
caminho_arquivo = r"C:\Users\Ismael\OneDrive - Mumu\BaseDados\NOVO\00001produto.txt"
df = abrir_txt(caminho_arquivo)

try:
    df = df[["CodProduto", "CodGrupo", "Descricao", "Estoq", "Fam"]]
    print("df ok")
except:
    pass


caminho_arquivo = r"C:\Users\Ismael\OneDrive - Mumu\BaseDados\NOVO\00001produtoextra.txt"
df_extra = abrir_txt(caminho_arquivo)
print(df_extra.head())



#pd.df.append(procv_produtoextra)
#tipo_peso_cong_seco
#ultimo_caract_arquivo
#proc_txt_loja



#(codigo/grupo/descrição/sigla/peso/tipo/conv/LOJA)

# 2.a o df que passa pelo filtro de limpeza possui as seguintes colunas (codigo/grupo/descrição/sigla/peso/tipo/conv/LOJA)
    #codigo/grupo/descrição/sigla sao retirados direto de produto.txt
    #peso é feito procv do produtoextra
    #tipo é classificado como peso/cong/seco
        #SE PESO: TIPO=PESO
        #SENÃOSE: NÃO(PESO) && ((GRUPO==CONG)OU(GRUPO=R=EFR)) TIPO=PESO
        #SENÃO: TIPO=SECO 
    #conv ultimo texto da descrição seder erro=1

# 2. passa o filtro para limpar o df
# 3. df vira 3 versões a.dfseco b.dfcong c.dfpeso