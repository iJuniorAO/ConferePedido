import pandas as pd

Colunas_Pedidos = [
    "QtCx",
    "Sigla",
    "Desc"
]

caminho_arquivo = r"C:\Users\Ismael\OneDrive - Mumu\BaseDados\PedidoAtual.txt"
df_Pedido_Loja = pd.read_csv(caminho_arquivo, sep="|", header=None, encoding="latin1")

df_Pedido_Loja[Colunas_Pedidos] = (
    df_Pedido_Loja[0]
    .astype(str)
    .str.split(" ", n=2, expand=True)
)

df_Pedido_Loja = df_Pedido_Loja.drop(columns=[0,"Sigla"])

print(f"\n🟢 Pedido Lojas:\n{df_Pedido_Loja}\n\n")



if False:

    df_Pedido_Loja2 = pd.read_csv(caminho_arquivo, sep =" ",header=None, names=None, encoding="latin1")

    df_Pedido_Loja = pd.read_csv(caminho_arquivo, sep=" ", header=None, encoding="latin1")
    print(f"🟠Pedido Errado: \n{df_Pedido_Loja}\n\n")

