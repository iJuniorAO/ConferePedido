import streamlit as st

st.set_page_config(page_title="Conversor Markup/Margem", page_icon="📊",layout="wide")

st.title(":material/Percent: Conversor de Markup e Margem")
st.divider()
col1,col2 = st.columns(2,vertical_alignment="top")

with col1:
    st.markdown("### Valores Iniciais")

    # Seleção do tipo de conversão
    opcao = st.radio(
        "O que você deseja encontrar?",
        ("Markup", "Margem"),
        horizontal=True
    )

    # Entrada de valor
    valor_input = st.number_input(
        f"Informe o valor do {opcao.split(' ')[0]} (%)", 
        min_value=0.0, 
        max_value=1000.0,
        value=10.0,
        step=0.1,
        format="%.2f"
    )

# Conversão decimal para o cálculo
taxa = valor_input / 100

if opcao == "Markup":
    resultado = (taxa / (1 + taxa)) * 100
    tipo_resultado = "Margem"
else:
    if taxa >= 1: # Evita divisão por zero ou markup infinito
        resultado = float('inf')
    else:
        resultado = (taxa / (1 - taxa)) * 100
    tipo_resultado = "Markup"

with col2:
    #st.markdown("---")
    if resultado == float('inf'):
        st.error("Erro: A margem não pode ser 100% ou superior para o cálculo de Markup.")
    else:
        st.markdown(f"### Resultado: {tipo_resultado}")
        st.metric("", value=f"{resultado:.2f}%")