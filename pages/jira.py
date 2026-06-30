import streamlit as st
import pandas as pd
from jira import JIRA
from datetime import datetime
from utils import validar_acesso

# Configuração da página
st.set_page_config(
    page_title="Central Mumix - Jira",
    layout="wide",
    page_icon=":material/local_post_office:",
)
HOJE = datetime.now().date()

link_portal = st.secrets["jira"]["link_portal_cliente"]
link_formulario = st.secrets["jira"]["link_formulario"]

validar_acesso(["administrador", "prevencao"])

jira_dict = {
    "loja": "customfield_10126",
    "fornecedor": "customfield_10129",
    "Motivo": "customfield_10127",
    "CodProduto": "customfield_10184",
    "QtdProduto": "customfield_10185",
    "DescricaoProduto": "customfield_10125",
}


# 1. Conexão com o Jira (Cache para evitar reconectar a cada reload)
# @st.cache_resource
def conectar_jira():
    try:
        jira_conn = JIRA(
            server=st.secrets["jira"]["url"],
            basic_auth=(st.secrets["jira"]["email"], st.secrets["jira"]["token"]),
        )
        return jira_conn
    except Exception as e:
        st.error(f"Erro ao conectar ao Jira: {e}")
        return None


jira = conectar_jira()


# Função para buscar dados e converter em DataFrame
def buscar_dados_jira(jql):
    try:
        # Busca as issues (ajuste o maxResults se necessário)
        issues = jira.search_issues(jql, maxResults=100)

        dados = []
        for issue in issues:
            # Tratamento seguro de campos nulos
            fornecedor = issue.get_field(jira_dict["fornecedor"])
            responsavel = (
                issue.fields.assignee.displayName
                if issue.fields.assignee
                else "Não atribuído"
            )

            # Monta o dicionário com os campos que você usa no código
            dados.append(
                {
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "status": issue.fields.status.name,
                    "tipo": issue.fields.issuetype.name,
                    "responsavel": responsavel,
                    "criado_em": issue.fields.created[:10],
                    "descricao": (
                        issue.fields.description
                        if issue.fields.description
                        else "Sem descrição informada."
                    ),
                    "loja": issue.get_field(jira_dict["loja"]),
                    "fornecedor": "-" if fornecedor is None else fornecedor,
                    "motivo": issue.get_field(jira_dict["Motivo"]),
                    "cod_produto": issue.get_field(jira_dict["CodProduto"]),
                    "qtd_produto": issue.get_field(jira_dict["QtdProduto"]),
                    "desc_produto": issue.get_field(jira_dict["DescricaoProduto"]),
                }
            )

        return pd.DataFrame(dados)
    except Exception as e:
        st.error(f"Erro ao buscar dados do Jira: {e}")
        return pd.DataFrame()


# --- PAINEL LATERAL: FILTROS GERAIS ---
with st.sidebar:
    st.markdown("## :material/Filter_Alt: Filtros de Busca")

    # Filtro de Projeto (Deixe vazio para buscar em todos)
    filtro_projeto = st.text_input(
        "Código do Projeto (ex: MTED)",
        help="Deixe em branco para ver todos os projetos",
    )

    # Filtro de Status
    filtro_status = st.selectbox(
        "Status da Tarefa", ["Todas", "To Do", "In Progress", "Done", "Backlog"]
    )

    # Configuração de Paginação na lateral
    st.markdown("---")
    st.markdown("# :material/Docs: Paginação")
    itens_por_pagina = st.slider(
        "Itens por página", min_value=5, max_value=50, value=20
    )
    pagina_atual = st.number_input("Página", min_value=1, value=1)
    inicio_registro = (pagina_atual - 1) * itens_por_pagina

    # --- CONSTRUÇÃO DINÂMICA DA JQL (QUERY DO JIRA) ---
    componentes_jql = []

    # 2. Filtro de Projeto
    if filtro_projeto:
        componentes_jql.append(f"project = '{filtro_projeto.upper()}'")

    # 3. Filtro de Status
    if filtro_status != "Todas":
        componentes_jql.append(f"status = '{filtro_status}'")

    # Juntar todos os filtros com 'AND'. Se não houver filtros, traz tudo.
    if componentes_jql:
        jql_final = " AND ".join(componentes_jql) + " ORDER BY created DESC"
    else:
        jql_final = "id is not EMPTY ORDER BY created DESC"  # Traz absolutamente tudo do seu espaço

    st.space()
    # Botão para disparar a busca/atualização explicitamente
    if st.button(":material/Sync: Atualizar Dados", use_container_width=True):
        st.session_state["df_jira"] = buscar_dados_jira(jql_final)


# Garante que os dados sejam carregados na primeira execução caso o botão não tenha sido clicado
if "df_jira" not in st.session_state:
    with st.spinner("Carregando dados iniciais do Jira..."):
        st.session_state["df_jira"] = buscar_dados_jira(jql_final)

# Copia o DataFrame da sessão para uso no código
df = st.session_state["df_jira"]


st.markdown("# :material/local_post_office: Central Trocas e Devoluções")
# O [Texto](Link) cria o link hipertexto direcionado
st.markdown(f"Portal: [:material/Captive_Portal: Portal do Cliente]({link_portal})")
st.markdown(
    f"Link das Lojas: [:material/Content_Paste: Formulário Trocas e Devoluções]({link_formulario})"
)
st.divider()

if not df.empty:

    # --- ABAS DA INTERFACE PRINCIPAL ---
    # aba_board = st.tabs(["📊 Quadro (Board)"])[0] if "aba_board" not in locals() else aba_board
    aba_board, aba_view, aba_coleta = st.tabs(
        ["📊 Quadro (Board)", "📋 Painel de Tarefas (detalhado)", "📦 Ordem Coleta"]
    )

    # --- ABA BOARD: VISUALIZAÇÃO EM COLUNAS ---
with aba_board:
    st.markdown("# Quadro")
    col_todo, col_nfe, col_envio, col_fornecedor, col_done = st.columns(5)

    titulos = [
        ":material/Edit: A fazer",
        ":material/Barcode: Validação NFE",
        ":material/Send: Envio Produto",
        ":material/Group: Negociação Fornecedor",
        ":material/Check: Concluído",
    ]
    lista_colunas = [col_todo, col_nfe, col_envio, col_fornecedor, col_done]

    for titulo, coluna in zip(titulos, lista_colunas):
        with coluna:
            st.markdown(f"### {titulo}")

    # Mapeamento de Status do seu código original
    status_map = {
        "Aberto": col_todo,
        "Validação NFE": col_nfe,
        "Envio Produto": col_envio,
        "NEGOCIAÇÃO FORNECEDOR": col_fornecedor,
        "Concluído (reposição)": col_done,
        "Concluído (prejuízo)": col_done,
        "Concluído (estoque)": col_done,
        "Troca Recusada": col_done,
    }

    # Se o DataFrame não estiver vazio, renderiza os cards
    if not df.empty:
        for _, row in df.iterrows():
            status_name = row["status"]
            # Determina a coluna alvo (padrão col_todo se não mapeado)
            col_alvo = status_map.get(status_name, col_todo)

            with col_alvo:
                with st.container(border=True):
                    # Forçando conversão para string para evitar erros de renderização caso venha nulo
                    motivo_str = str(row["motivo"]).upper() if row["motivo"] else ""
                    st.markdown(f"##### **{row['key']}** | {motivo_str}")
                    st.markdown(f"**LOJA:** {row['loja']}")
                    st.markdown(f"**FORNECEDOR:** {row['fornecedor']}")
                    st.markdown(
                        f"**{row['cod_produto']}** | {row['qtd_produto']}x {row['desc_produto']}"
                    )
                    st.markdown(
                        f"[🔗 Abrir no Jira]({st.secrets['jira']['url']}/browse/{row['key']})"
                    )

    # --- ABA 1: VISUALIZAR / FILTRAR TASKS ---
    with aba_view:
        # Mostra a query JQL que está sendo executada (útil para depuração)
        # st.caption(f"**Query JQL Ativa:** `{jql_final}`")

        with st.spinner("Buscando tarefas no Jira..."):
            try:
                # Realiza a busca utilizando os filtros e os parâmetros de paginação
                issues = jira.search_issues(
                    jql_final, startAt=inicio_registro, maxResults=itens_por_pagina
                )
                total_issues = (
                    issues.total
                )  # Total de tarefas que correspondem ao filtro no Jira

                st.markdown(f"## Tarefas Encontradas ({total_issues})")

                if issues:
                    # Exibe um resumo de paginação para o usuário
                    fim_registro = min(inicio_registro + itens_por_pagina, total_issues)
                    st.write(
                        f"Exibindo registros de {inicio_registro + 1} a {fim_registro}"
                    )

                    # Listagem dos cards
                    for issue in issues:
                        # Identifica o responsável de forma segura
                        responsavel = (
                            issue.fields.assignee.displayName
                            if issue.fields.assignee
                            else "Não atribuído"
                        )

                        titulo_card = f"**{issue.key}** - {issue.fields.summary} | *({issue.fields.status.name})*"
                        with st.expander(titulo_card):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Status:** {issue.fields.status.name}")
                                st.write(f"**Tipo:** {issue.fields.issuetype.name}")
                                st.write(f"**Responsável:** {responsavel}")
                            with col2:
                                st.write(f"**Criado em:** {issue.fields.created[:10]}")
                                st.markdown(
                                    f"[🔗 Abrir diretamente no Jira]({st.secrets['jira']['url']}/browse/{issue.key})"
                                )

                            st.markdown("---")
                            st.write("**Descrição:**")
                            st.write(
                                issue.fields.description
                                if issue.fields.description
                                else "*Sem descrição informada.*"
                            )
                else:
                    st.info("Nenhuma tarefa corresponde aos filtros selecionados.")

            except Exception as e:
                st.error(f"Erro ao processar a busca no Jira: {e}")

    with aba_coleta:
        # Filtra apenas as tarefas com status "Envio Produto"
        df_coleta = df[df["status"] == "Envio Produto"].copy()

        if not df_coleta.empty:
            st.markdown("# Todas Coletas")

            datas_coleta = pd.to_datetime(df_coleta["criado_em"], errors="coerce")
            coleta_mais_antiga = datas_coleta.min()
            coleta_mais_antiga_texto = (
                coleta_mais_antiga.strftime("%d/%m/%Y")
                if pd.notna(coleta_mais_antiga)
                else "-"
            )

            metrica_lojas, metrica_coletas, metrica_antiga = st.columns(3)
            metrica_lojas.metric("Lojas", df_coleta["loja"].nunique())
            metrica_coletas.metric("Coletas", len(df_coleta))
            metrica_antiga.metric("Chamado mais Antigo", coleta_mais_antiga_texto)

            # Agrupa por loja
            lojas_coleta = df_coleta["loja"].unique()

            for loja in lojas_coleta:
                st.markdown("## Ordem de Coleta")
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"### :material/store: Loja: {loja}")
                c2.markdown(f"### Motorista:______________")
                c3.markdown(f"### {HOJE.strftime("%d/%m/%Y")}")
                # Filtra os itens daquela loja específica

                df_loja_coleta = df_coleta[df_coleta["loja"] == loja].copy()
                df_loja_coleta["Coletado"] = False
                df_loja_coleta = df_loja_coleta[
                    ["cod_produto", "qtd_produto", "desc_produto", "key", "Coletado"]
                ]
                # Renomeia colunas para melhor visualização
                df_loja_coleta.columns = [
                    "Cód. Produto",
                    "Qtd",
                    "Descrição",
                    "Ticket",
                    "Coletado",
                ]

                st.dataframe(df_loja_coleta, hide_index=True, width="stretch")
                st.space("xxlarge")
                st.divider()

                # Botão para gerar um resumo de texto (opcional)
                # resumo_texto = f"Ordem de Coleta - Loja: {loja}\n"
                # for _, item in df_loja_coleta.iterrows():
                #     resumo_texto += f"- {item['Cód. Produto']} | {item['Qtd']}x {item['Descrição']}\n"

                # st.download_button(
                #     label=f"Baixar Lista de Coleta - {loja}",
                #     data=resumo_texto,
                #     file_name=f"coleta_{loja}.txt",
                #     mime="text/plain",
                #     key=f"btn_{loja}"
                # )
        else:
            st.success(
                "Nenhuma tarefa no status 'Envio Produto' para gerar ordens de coleta."
            )

    # --- ABA 2: CRIAR TASKS ---
    # with aba_create:
    #     st.markdown("## Abrir novo Ticket")

    #     with st.form("form_nova_task", clear_on_submit=True):
    #         project_key = st.text_input("Chave do Projeto (ex: PRJ)", help="A sigla do seu projeto no Jira")
    #         summary = st.text_input("Título da Task")
    #         description = st.text_area("Descrição detalhada")
    #         issue_type = st.selectbox("Tipo de Task", ["Task", "Bug", "Story"])

    #         submit_button = st.form_submit_button("Criar Task no Jira")

    #         if submit_button:
    #             if project_key and summary:
    #                 try:
    #                     new_issue_dict = {
    #                         'project': {'key': project_key.upper()},
    #                         'summary': summary,
    #                         'description': description,
    #                         'issuetype': {'name': issue_type},
    #                     }
    #                     new_issue = jira.create_issue(fields=new_issue_dict)
    #                     st.success(f"Task **{new_issue.key}** criada com sucesso!")
    #                     # Força o recarregamento para atualizar a lista na outra aba
    #                     st.rerun()
    #                 except Exception as e:
    #                     st.error(f"Erro ao criar task: {e}")
    #             else:
    #                 st.warning("Por favor, preencha a Chave do Projeto e o Título.")

st.divider()
