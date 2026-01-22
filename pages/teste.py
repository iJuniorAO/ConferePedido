import streamlit as st
from supabase import create_client, Client

url = st.secrets["connections"]["supabase"]["url"]
key = st.secrets["connections"]["supabase"]["key"]

supabase: Client = create_client(url, key)

resposta = supabase.table("Lojas").select("*").order("Codigo").execute()

LOJAS = []
LOJAS_DICT = {}

for i in resposta.data:
    LOJAS.append(i.get("Filial"))
    LOJAS_DICT[i["Filial"]]=i["Grupo"]