import streamlit as st
import pandas as pd

st.title("🚀 Meu App de CRM está ONLINE!")

st.write("Se você está lendo isso, o erro de instalação foi resolvido.")

arquivo = st.file_uploader("Teste subir sua planilha aqui", type=["csv", "xlsx"])

if arquivo:
    st.success("Consegui ler o arquivo! O próximo passo é gerar os gráficos.")
    df = pd.read_excel(arquivo) if arquivo.name.endswith('.xlsx') else pd.read_csv(arquivo)
    st.write(df.head())
