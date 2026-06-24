import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
from utils import carregar_dados_onedrive, abrir_arquivo_txt, validar_acesso
from bancoDados import inicia_conexao_bancoDados, tratar_erros_supabase
import streamlit as st
from thefuzz import process

# Inicializa conexão
supabase = inicia_conexao_bancoDados()
link_txt = st.secrets["onedrive"]["links"]["produto"]
COLUNAS_PRODUTOS = [
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
    "Fam",
]
COLUNAS_VALIDADE = [
    "CodProduto",
    "Descricao",
    "Tipo",
    "Estoq",
    "qtContada",
    "avaria",
    "validade",
    "Prazo",
    "Status",
    "obs",
]
COLUNAS_PENDENTE = [
    "CodProduto",
    "Descricao",
    "Tipo",
    "Estoq",
    "qtContada",
    "SaldoPendencia",
]
COLUNAS_ORDEM_TOTAL = [
    "CodProduto",
    "Descricao",
    "Tipo",
    "Estoq",
    "qtContada",
    "avaria",
    "validade",
    "Prazo",
    "Status",
    "obs",
    "SaldoPendencia",
]

# --- FUNÇÕES STREAMLIT ---


# 1. Definimos a função do diálogo de sucesso
@st.dialog("Alerta!", dismissible=False)
def confirmar_e_atualizar(mensagem: str, tipo: bool):
    """
    Exibe uma mensagem de sucesso em um modal e força o rerun
    apenas quando o usuário clicar em fechar ou no botão.
    """
    if tipo:
        st.success("SUCESSO")
    else:
        st.error("ERRO")
    st.write(mensagem)
    st.write("Clique no botão abaixo para atualizar a página e aplicar as mudanças.")

    # Botão para o usuário avançar manualmente
    if st.button("Atualizar Página"):
        st.rerun()


# --- FUNÇÕES DE BANCO DE DADOS ---


def inserir_validade(
    codigo: str,
    validade: datetime.date,
    qt_contada: float,
    avaria: bool = False,
    obs: str = "",
):
    """Insere ou atualiza um registro de validade no Supabase."""
    try:
        dados = {
            "CodProduto": codigo,  # Ajustado para bater com a coluna padrão
            "validade": str(validade),
            "qtContada": qt_contada,
            "avaria": avaria,
            "obs": obs if obs else None,
        }

        response = supabase.table("validades").insert(dados).execute()
        if response.data:
            # st.success(f"Validade do código {codigo} inserida com sucesso!")
            st.cache_data.clear()
            confirmar_e_atualizar(
                f"Validade do código {codigo} inserida com sucesso!", True
            )
        else:
            st.error("Erro ao inserir dados no banco.")
    except Exception as e:
        st.error(f"Erro ao conectar ou atualizar o Banco de Dados: {e}")


def atualizar_qt(
    codigo: str, validade: datetime.date, nova_qtd: int, avaria: bool = False
):
    """Atualiza a quantidade contada de um registro específico no Supabase."""
    try:
        query = (
            supabase.table("validades")
            .update({"qtContada": nova_qtd})
            .eq("CodProduto", codigo)
            .eq("validade", str(validade))
            .eq("avaria", avaria)
        )

        response = query.execute()
        if response.data:
            # st.success(f"Quantidade do produto {codigo} atualizada para {nova_qtd}!")
            st.cache_data.clear()
            confirmar_e_atualizar(
                f"Quantidade do produto {codigo} atualizada para {nova_qtd}!", True
            )
        else:
            st.error("Não foi possível localizar o registro para atualização.")

    except Exception as e:
        st.error(f"Erro ao atualizar quantidade no Banco de Dados: {e}")


def puxar_tabela_validade() -> pd.DataFrame:
    """Puxa todas as linhas cadastradas na tabela 'validades'."""
    try:
        response = supabase.table("validades").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            colunas_desejadas = ["CodProduto", "validade", "qtContada", "avaria", "obs"]
            colunas_existentes = [col for col in colunas_desejadas if col in df.columns]
            return df[colunas_existentes]
        else:
            st.error(":material/Close: Erro ao pegar datas planilhadas")
            st.stop()
    except Exception as e:
        st.error(f"Erro ao puxar dados do Supabase: {e}")
        if not tratar_erros_supabase(e):
            st.stop()
        return pd.DataFrame(
            columns=["CodProduto", "validade", "qtContada", "avaria", "obs"]
        )


def trata_df(df):
    """Trata o dataframe vindo do OneDrive (AlterData)."""
    colunas_filtro = ["CodProduto", "Tipo", "Descricao", "Estoq"]
    df["Tipo"] = "SECO"
    df.loc[df["CodGrupo"].isin([9]), "Tipo"] = "CONG"
    df.loc[df["CodGrupo"].isin([14]), "Tipo"] = "REFR"

    # Mantemos o DataFrame completo para processar zerados/negativos na reconciliação
    return df[colunas_filtro]


# --- LIMPEZA BANCO DE DADOS ---
def limpeza_inicial_banco_dados():
    try:
        # Deleto todas as linhas em que qtContada <= 0 ou nulo
        supabase.table("validades").delete().lte("qtContada", 0).execute()
        supabase.table("validades").delete().is_("qtContada", "null").execute()
    except Exception as e:
        st.error(f"ERRO ao realizar limpeza inicial (qtContada): {e}")

    try:
        # Deleto todas as linhas em que validade está vazia ou nula
        supabase.table("validades").delete().is_("validade", "null").execute()
    except Exception as e:
        st.error(f"ERRO ao realizar limpeza inicial (validade): {e}")


# --- BUSCA CODIGO ---
def buscar_produtos(
    termo_busca: str, df_original: pd.DataFrame, usar_fuzzy: bool = True
) -> pd.DataFrame:
    """
    Filtra o dataframe de produtos com base no termo e no método escolhido.

    Inputs:
        termo_busca (str): O texto vindo da NFe do fornecedor.
        usar_fuzzy (bool): Se True, usa Fuzzy (Top 5). Se False, usa Regex (Curingas).
        df_original (pd.DataFrame): O cadastro completo de produtos.

    Retorno:
        pd.DataFrame: Dataframe filtrado ou vazio se nada for encontrado.
    """
    # Se o campo estiver vazio, retorna o dataframe original (ou vazio, dependendo da sua preferência)
    if not termo_busca.strip():
        return pd.DataFrame()
        # return df_original

    if usar_fuzzy:
        # Pega a lista de descrições internas para o algoritmo comparar
        lista_opcoes = df_original["Descricao"].tolist()

        # Extrai os top 5 mais parecidos. Retorna uma lista de tuplas: [('Texto', score), ...]
        melhores_matches = process.extract(termo_busca, lista_opcoes, limit=15)

        # Filtra apenas os que tiveram um score mínimo aceitável (ex: maior que 30) para evitar lixo
        textos_filtrados = [match[0] for match in melhores_matches if match[1] > 30]

        if not textos_filtrados:
            return pd.DataFrame(columns=df_original.columns)

        # Filtra o DataFrame original trazendo apenas as linhas dos textos encontrados
        df_resultado = df_original[
            df_original["Descricao"].isin(textos_filtrados)
        ].copy()

        # Opcional: Adiciona a coluna de score para você ver o nível de certeza na tela
        mapeamento_scores = {match[0]: match[1] for match in melhores_matches}
        df_resultado["similaridade_%"] = df_resultado["Descricao"].map(
            mapeamento_scores
        )
        df_resultado = df_resultado[COLUNAS_VALIDADE + ["similaridade_%"]]

        # Ordena do mais parecido para o menos parecido
        return df_resultado.sort_values(by="similaridade_%", ascending=False)

    else:
        # Busca por Regex / Contém (Aceita curingas como '.*')
        try:
            df_resultado = df_original[
                df_original["Descricao"].str.contains(
                    termo_busca, case=False, na=False, regex=True
                )
            ]
            return df_resultado[COLUNAS_VALIDADE]
        except Exception:
            # Caso o usuário digite um caractere de regex inválido enquanto digita, evita quebrar o app
            return pd.DataFrame(columns=df_original.columns)


# --- ENGINE DE RECONCILIAÇÃO AUTOMÁTICA ---
def reconciliar_estoque_e_validades(df_db, df_txt):
    """
    Roda no início do programa. Compara o BD com o estoque atual do OneDrive
    e ajusta o Supabase de acordo com as regras de negócio.
    """
    with st.spinner("Validando estoque atual...", show_time=True):
        # Agrupa o estoque do OneDrive por produto (garantindo unicidade)
        estoque_atual = (
            df_txt[df_txt["Estoq"] > 0].set_index("CodProduto")["Estoq"].to_dict()
        )

        df_db["avaria"] = df_db["avaria"].fillna(False)

        produtos_no_bd = df_db["CodProduto"].unique()
        Mudou_algo = False

        for cod_prod in produtos_no_bd:
            cod_prod_str = str(cod_prod)
            qt_estoque = estoque_atual.get(cod_prod, 0)

            # Filtra os lançamentos desse produto no banco
            df_prod_all = df_db[df_db["CodProduto"] == cod_prod].copy()
            df_prod = df_prod_all[df_prod_all["avaria"] == False].copy()

            # Se o estoque no sistema for zerado ou negativo, removemos APENAS o estoque normal.
            # As avarias continuam no banco para tratamento manual.
            if qt_estoque <= 0:
                if not df_prod.empty:
                    supabase.table("validades").delete().eq(
                        "CodProduto", cod_prod_str
                    ).eq("avaria", False).execute()
                    Mudou_algo = True
                continue

            soma_contada = df_prod["qtContada"].sum()

            # REGRA 3 e 4: Se a quantidade contada for maior que o estoque atual do sistema
            if soma_contada > qt_estoque:
                Mudou_algo = True

                # Criamos e ordenamos a tabela do produto por data antes de qualquer validação.
                # Convertemos para datetime para garantir a ordenação correta (NaT/None ficam por último)
                df_prod["validade_dt"] = pd.to_datetime(df_prod["validade"])
                df_prod_ord = df_prod.sort_values(by="validade_dt", ascending=True)

                # Se for apenas 1 linha cadastrada
                if len(df_prod) == 1:
                    "Cod: ", cod_prod, " | QtdContada: ", soma_contada, " | qt_estoque: ", qt_estoque, "Atualizando..."

                    # Atualiza a linha diretamente para o valor do estoque
                    validade_alvo = (
                        str(df_prod_ord.iloc[0]["validade"])
                        if pd.notna(df_prod_ord.iloc[0]["validade"])
                        else "null"
                    )

                    query = (
                        supabase.table("validades")
                        .update({"qtContada": qt_estoque})
                        .eq("CodProduto", cod_prod_str)
                        .eq("avaria", False)
                    )
                    if validade_alvo == "null" or validade_alvo == "None":
                        query.is_("validade", "null").execute()
                    else:
                        query.eq("validade", validade_alvo).execute()

                # Se houver linhas múltiplas/duplicadas
                else:
                    excesso = soma_contada - qt_estoque
                    "Cod: ", cod_prod, " | QtdContada: ", soma_contada, " | qt_estoque: ", qt_estoque, "Deletando..."

                    for _, linha in df_prod_ord.iterrows():
                        if excesso <= 0:
                            break

                        qtd_linha = linha["qtContada"]
                        validade_alvo = str(linha["validade"])

                        if qtd_linha <= excesso:
                            # Excesso derruba a linha inteira. Deleta ela.
                            "Cod: ", cod_prod, " | QtdContada: ", soma_contada, " | qt_estoque: ", qt_estoque, "Deletando..."
                            excesso -= qtd_linha
                            query = (
                                supabase.table("validades")
                                .delete()
                                .eq("CodProduto", cod_prod_str)
                                .eq("qtContada", qtd_linha)
                                .eq("avaria", False)
                            )
                            query = (
                                query.is_("validade", "null")
                                if pd.isna(linha["validade"])
                                else query.eq("validade", validade_alvo)
                            )
                            query.execute()
                        else:
                            # Excesso diminui apenas uma parte da linha e encerra
                            nova_qtd = qtd_linha - excesso
                            excesso = 0
                            query = (
                                supabase.table("validades")
                                .update({"qtContada": nova_qtd})
                                .eq("CodProduto", cod_prod_str)
                                .eq("qtContada", qtd_linha)
                                .eq("avaria", False)
                            )
                            query = (
                                query.is_("validade", "null")
                                if pd.isna(linha["validade"])
                                else query.eq("validade", validade_alvo)
                            )
                            query.execute()

        if Mudou_algo:
            st.cache_data.clear()
            st.info("mudou algo")
            st.rerun()


# --- FLUXO PRINCIPAL DO APP ---

st.markdown("# Controle de Validades - Sistema MUMIX")
validar_acesso(["administrador", "prevencao"])

# 1. Puxa dados brutos
df_db = puxar_tabela_validade()
dados_txt = carregar_dados_onedrive(link_txt)
df_txt_bruto = abrir_arquivo_txt(dados_txt, colunas=COLUNAS_PRODUTOS)
df_txt = trata_df(df_txt_bruto)

limpeza_inicial_banco_dados()
# 2. Executa a validação e reconciliação automática no banco
reconciliar_estoque_e_validades(df_db, df_txt)

# Re-puxa os dados atualizados pós-reconciliação para exibição em tela
df_db = puxar_tabela_validade()

# 3. Cruzamento de Dados para o Painel (Merge)
# Usamos 'right' ou 'outer' baseado no df_txt para garantir que itens sem lançamento apareçam
df_validade = df_db.merge(df_txt, on="CodProduto", how="right")

# Preenche os campos nulos gerados pelo merge de produtos sem validade bipeada
df_validade["qtContada"] = df_validade["qtContada"].fillna(0).astype(int)

# Cálculo de prazos e status
df_validade["validade"] = pd.to_datetime(df_validade["validade"])
df_validade["Prazo"] = (df_validade["validade"] - pd.Timestamp.now()).dt.days

condicoes_prazo = [
    df_validade["validade"].isna(),
    df_validade["Prazo"] <= 20,
    df_validade["Prazo"] <= 30,
    df_validade["Prazo"] <= 60,
    df_validade["Prazo"] > 60,
]
resultado_prazo = [
    "2.Em Branco",
    "1.Critico",
    "3.Atenção",
    "4.Acompanhar",
    "5.Dentro do Prazo",
]
df_validade["Status"] = np.select(condicoes_prazo, resultado_prazo, default="Outros")

# Força regra visual: se a soma das validades é menor que o estoque,
# precisamos sinalizar que há saldo "Em Branco" pendente de input
# Criamos um status virtual de visualização para o usuário saber que precisa preencher o resto
df_validade["SaldoPendencia"] = df_validade["Estoq"] - df_validade.groupby(
    "CodProduto"
)["qtContada"].transform("sum")

# --- SEÇÃO DE INDICADORES NA TELA ---
df_avaria = df_validade[df_validade["avaria"] == True]
df_negativo = df_validade[df_validade["Estoq"] < 0]
df_critico = df_validade[df_validade["Status"] == "1.Critico"]
df_emBranco = df_validade[
    (df_validade["Status"] == "2.Em Branco") | (df_validade["SaldoPendencia"] > 0)
]
df_emBranco = df_emBranco[df_emBranco["Estoq"] > 0]

st.markdown("## :material/Editor_Choice: Indicadores")
col_ind1, col_ind2 = st.columns(2)
with col_ind1:
    if not df_avaria.empty:
        st.error(f":material/Close: Há {len(df_avaria)} itens Avariados")
    else:
        st.success(":material/Check: Nenhum item avariado")

with col_ind2:
    if not df_negativo.empty:
        st.error(f":material/Close: Há {len(df_negativo)} itens com Estoque Negativo")
    else:
        st.success(":material/Check: Nenhum item negativo")

# Criando as abas na interface do Streamlit
aba_criticos, aba_pendentes, aba_avaria, aba_geral = st.tabs(
    [
        ":material/Event_Busy: Críticos",
        ":material/Calendar_Add_on: Produtos Pendentes (Em Branco com Saldo)",
        ":material/Destruction: Avaria",
        ":material/Bar_Chart: Relatório Total",
    ]
)

with aba_criticos:
    st.markdown(f"### :blue[{len(df_critico)}] Itens com Prazo Crítico")
    aba_critico_geral, aba_critico_seco, aba_critico_cong = st.tabs(
        [
            ":material/Docs: Geral",
            ":material/Cookie: Seco",
            ":material/ac_unit: Congelado/Refrigerado",
        ]
    )
    df_critico_seco = df_critico[df_critico["Tipo"] == "SECO"]
    df_critico_cong = df_critico[df_critico["Tipo"] != "SECO"]

    with aba_critico_geral:
        if not df_critico.empty:
            st.dataframe(
                df_critico[COLUNAS_VALIDADE].sort_values(by=["Status", "Prazo"]),
                width="stretch",
            )
        else:
            st.info("Nenhuma item crítico no momento.")

    with aba_critico_seco:
        if not df_critico_seco.empty:
            st.markdown(f"##### :blue[{len(df_critico_seco)}] Itens SECO")
            st.dataframe(
                df_critico_seco[COLUNAS_VALIDADE].sort_values(by=["Status", "Prazo"]),
                width="stretch",
            )
        else:
            st.info("Nenhuma item crítico no momento.")
    with aba_critico_cong:
        if not df_critico_cong.empty:
            st.markdown(f"##### :blue[{len(df_critico_cong)}] Itens CONG/REFR")
            st.dataframe(
                df_critico_cong[COLUNAS_VALIDADE].sort_values(by=["Status", "Prazo"]),
                width="stretch",
            )
        else:
            st.info("Nenhuma item crítico no momento.")


with aba_pendentes:
    st.markdown(
        f"### :blue[{len(df_emBranco)}] Produtos Aguardando Bipagem / Lançamento"
    )

    aba_pendente_geral, aba_pendente_seco, aba_pendente_cong = st.tabs(
        [
            ":material/Docs: Geral",
            ":material/Cookie: Seco",
            ":material/ac_unit: Congelado/Refrigerado",
        ]
    )
    df_pendente_seco = df_emBranco[df_emBranco["Tipo"] == "SECO"]
    df_pendente_cong = df_emBranco[df_emBranco["Tipo"] != "SECO"]

    with aba_pendente_geral:
        if not df_emBranco.empty:
            # colunas_pendencia = ["CodProduto", "Descricao", "Tipo", "Estoq", "qtContada", "SaldoPendencia", "Status"]
            st.dataframe(
                df_emBranco[COLUNAS_PENDENTE].sort_values(
                    by="SaldoPendencia", ascending=False
                ),
                width="stretch",
            )
        else:
            st.success(
                ":material/Person_Celebrate: Excelente! Todos os produtos do estoque possuem suas validades correspondentes."
            )
    with aba_pendente_seco:
        if not df_pendente_seco.empty:
            st.markdown(f"##### :blue[{len(df_pendente_seco)}] Itens SECO")
            st.dataframe(
                df_pendente_seco[COLUNAS_PENDENTE].sort_values(
                    by="SaldoPendencia", ascending=False
                ),
                width="stretch",
            )
        else:
            st.success(
                ":material/Person_Celebrate: Excelente! Todos os produtos do estoque possuem suas validades correspondentes."
            )
    with aba_pendente_cong:
        if not df_pendente_cong.empty:
            st.markdown(f"##### :blue[{len(df_pendente_cong)}] Itens CONG/REFR")
            st.dataframe(
                df_pendente_cong[COLUNAS_PENDENTE].sort_values(
                    by="SaldoPendencia", ascending=False
                ),
                width="stretch",
            )
        else:
            st.success(
                ":material/Person_Celebrate: Excelente! Todos os produtos do estoque possuem suas validades correspondentes."
            )

with aba_avaria:
    st.markdown(f"### :blue[{len(df_avaria)}] Produtos Avariados")
    st.dataframe(df_avaria[COLUNAS_VALIDADE].sort_values(by="Prazo"), width="stretch")


# Conteúdo da terceira aba: O cruzamento bruto (Geral) para auditoria rápida
with aba_geral:
    st.markdown(f"### :blue[{len(df_validade)}] Lançamentos Totais")
    st.dataframe(
        df_validade[COLUNAS_ORDEM_TOTAL].sort_values(by="Status"), width="stretch"
    )


st.divider()
st.markdown("## :material/edit: Modificar Valores")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### :material/New_Label: Inserir / Bipar Nova Validade")

    with st.form(key="form_nova_validade", clear_on_submit=True):
        col1_form, col2_form, col3_form = st.columns(3)
        with col1_form:
            codigo_input = st.text_input(
                "Código do Produto", placeholder="Bipe ou digite o código"
            )
        with col2_form:
            validate_input = st.date_input(
                "Data de Validade", value=datetime.today(), format="DD/MM/YYYY"
            )
        with col3_form:
            qt_input = st.number_input(
                "Quantidade Contada", min_value=0, step=1, value=0
            )

        col4_form, col5_form = st.columns([1, 3])
        with col4_form:
            avaria_input = st.checkbox("Produto com Avaria?")
        with col5_form:
            obs_input = st.text_input(
                "Observações",
                placeholder="Ex: Lote promocional / Avaria / Aguardando Fornecedor...",
            )

        botao_enviar = st.form_submit_button(label="Salvar Validade")


with col2:
    st.markdown("### :material/Edit: Atualizar Quantidade Contada")

    with st.form(key="form_atualizar_qt", clear_on_submit=True):
        col_atualiza1, col_atualiza2, col_atualiza3 = st.columns(3)
        with col_atualiza1:
            codigo_atualiza_input = st.text_input(
                "Codigo", placeholder="Bipe ou digite o codigo"
            )
        with col_atualiza2:
            validade_atualiza_input = st.date_input(
                "Validade", value=datetime.today(), format="DD/MM/YYYY"
            )
        with col_atualiza3:
            nova_qtd_input = st.number_input(
                "Nova quantidade", min_value=0, step=1, value=0
            )

        avaria_atualiza_input = st.checkbox(
            "Produto com Avaria?", key="avaria_atualiza_qt"
        )
        st.space("medium")
        botao_atualizar_qt = st.form_submit_button(label="Atualizar Quantidade")


with col3:
    st.markdown("### :material/Delete: Deletar Registro de Validade")

    with st.form(key="form_deletar_validade", clear_on_submit=True):
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            codigo_del_input = st.text_input(
                "Código para Deletar", placeholder="Bipe ou digite o código"
            )
        with col_del2:
            validade_del_input = st.date_input(
                "Data do Registro",
                value=datetime.today(),
                format="DD/MM/YYYY",
                key="del_date",
            )

        avaria_del_input = st.checkbox("Registro de Avaria?", key="del_avaria")

        botao_deletar = st.form_submit_button(label="Excluir Registro")


st.divider()
st.markdown("## :material/Search: Encontrar código")

col1_encontra, col2_encontra = st.columns(2)
with col1_encontra:
    descricao_produto = st.text_input(
        "Digite a descrição do produto:",
        help="""
    **Como pesquisar? Você tem duas opções:**

    1️⃣ **Por aproximação (Fuzzy Match):** 
    Digite o nome do produto normalmente. O sistema vai encontrar palavras parecidas ou com pequenos erros de digitação. 
    *Ex: "Iogurte"* encontra *"Iogurt"*, *"Iogurte"* ou *"Iogurti"*.

    ---

    2️⃣ **Por padrão exato (Regex com Curinga `.*`):**
    Use `.*` para indicar que pode existir *qualquer texto* naquele meio.
    *Exemplo:* `IOG GAR.*150G`

    ✅ **Encontra:**
    * IOG GAR MORANGO ACTIVIA 150G 20
    * IOG GAR AMEIXA ACTIVIA 150G 20
    * IOG GAR VITAMINA COM CEREAL BATAVO 1150G 8

    ❌ **Não encontra:**
    * IOG LIQ GAR MORANGO BATAVO 1150G 8 *(porque 'LIQ' quebrou a ordem do início)*
    """,
    )

with col2_encontra:
    metodo_selecionado = st.selectbox(
        "Selecione o método de busca:",
        options=["Busca por palavra exata (Regex)", "Busca Inteligente (Fuzzy Match)"],
    )
metodo_selecionado = metodo_selecionado == "Busca Inteligente (Fuzzy Match)"

df_produtos_encontrados = pd.DataFrame()
if descricao_produto:
    df_produtos_encontrados = buscar_produtos(
        termo_busca=descricao_produto,
        df_original=df_validade,
        usar_fuzzy=metodo_selecionado,
    )

# Exibição do resultado
if df_produtos_encontrados.empty:
    st.info("Nenhum produto correspondente encontrado no cadastro interno.")
else:
    st.markdown("## Resultados Encontrados:")
    st.write(f"Exibindo :blue[{len(df_produtos_encontrados)}] registro(s):")
    st.dataframe(df_produtos_encontrados, width="stretch", hide_index=True)


def deletar_validade(codigo: str, validade: datetime.date, avaria: bool = False):
    """Deleta um registro específico de validade no Supabase."""
    try:
        query = (
            supabase.table("validades")
            .delete()
            .eq("CodProduto", codigo)
            .eq("validade", str(validade))
            .eq("avaria", avaria)
        )

        response = query.execute()
        if response.data:
            # st.success(f"Registro do produto {codigo} deletado com sucesso!")
            st.cache_data.clear()
            confirmar_e_atualizar(
                f"Registro do produto {codigo} deletado com sucesso!", True
            )
            # st.rerun()
        else:
            st.error("Nenhum registro encontrado com esses critérios para exclusão.")
    except Exception as e:
        st.error(f"Erro ao deletar registro no Banco de Dados: {e}")


st.divider()


if botao_enviar:
    if not codigo_input.strip():
        st.warning("Por favor, informe um código de produto válido.")
    elif qt_input <= 0:
        st.warning("A quantidade contada deve ser maior que zero.")
    else:
        # Puxa o estoque atual deste produto específico para validação antes de inserir
        estoque_prod = df_txt[df_txt["CodProduto"] == codigo_input]

        if estoque_prod.empty:
            st.error("Código de produto não encontrado.")
        else:
            total_estoque_sistema = int(estoque_prod.iloc[0]["Estoq"])
            ja_contado = df_db[df_db["CodProduto"] == codigo_input]["qtContada"].sum()

            if (ja_contado + qt_input) > total_estoque_sistema:
                st.error(
                    f"Erro: A quantidade inserida ({qt_input}) somada ao que já foi contado ({ja_contado}) ultrapassa o estoque do sistema ({total_estoque_sistema})."
                )
            else:
                inserir_validade(
                    codigo=codigo_input,
                    validade=validate_input,
                    qt_contada=qt_input,
                    avaria=avaria_input,
                    obs=obs_input,
                )


if botao_atualizar_qt:
    codigo_atualiza = codigo_atualiza_input.strip()

    if not codigo_atualiza:
        st.error("Por favor, informe um codigo de produto valido.")
    elif nova_qtd_input <= 0:
        st.error("A nova quantidade deve ser maior que zero.")
    else:
        atualizar_qt(
            codigo=codigo_atualiza,
            validade=validade_atualiza_input,
            nova_qtd=nova_qtd_input,
            avaria=avaria_atualiza_input,
        )


if botao_deletar:
    if not codigo_del_input.strip():
        st.error("Informe o código do produto.")
    else:
        deletar_validade(
            codigo=codigo_del_input.strip(),
            validade=validade_del_input,
            avaria=avaria_del_input,
        )
