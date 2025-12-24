import pandas as pd
#   MELHORIA
#       Subir para Streamlit
#       Usuário alterar a distribuição por loja


# --- DEFINIÇÕES E CONSTANTES ---
def divide_produto(produto, qt_cx):
    df["QtCx"] = (df["Distribuição"] * qt_cx / 100).round(0).astype(int)
    df["Produto"] = produto
    return df

LOJAS = { "Lojas": [ "Abilio Machado", "Cabana", "Silva Lobo", "Jardim Alterosa",
                    "Brigadeiro", "Nova Contagem", "Novo Progresso", "Palmital", "Pindorama",
                    "Neves", "Santa Cruz", "São Luiz", "Venda Nova", "Cabral", "Laguna",
                    "Goiania", "Caete", "Lagoa Santa", "Laranjeiras", "Santa Helena",
                    "Eldorado", "Centro Betim", "Para de Minas", "Serrano"],
        "Distribuição" : [5,5,6,5,2,7,4,5,4,5,6,4,5,4,4,3,2,4,4,4,3,3,3,3]
        }

df = pd.DataFrame(LOJAS)

if df["Distribuição"].sum() != 100:
    print("❌ A distribuição não soma 100%\n Ajustar tabela de Lojas.")
else:
    produto = input("Digite o nome do produto: ").strip().upper()
    qt_cx = int(input("Digite a quantidade de caixas: ").strip())



    df = divide_produto(produto, qt_cx)

    if df["QtCx"].sum() != qt_cx:
        print(f"""
        ❌ A quantidade total de caixas não confere com a entrada.
            ⚠️  Necessário correção manual.)
                Esperado: {qt_cx}
                Divisão: {df["QtCx"].sum()} \n{df}""")
    else:
        print(f"""
            🟢 A quantidade total de caixas confere com a entrada.
            {df}""")
