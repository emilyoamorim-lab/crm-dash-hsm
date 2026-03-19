import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da Página
st.set_page_config(page_title="CRM Performance - HSM/Singularity", layout="wide")

# --- DEFINA O NOME DO SEU ARQUIVO AQUI ---
NOME_ARQUIVO_PADRAO = "Dados CRM 2026 - V2.xlsx" 

st.title("📊 Dashboard de Performance CRM")
st.markdown("Monitoramento estratégico de campanhas e engajamento.")

# --- LÓGICA DE CARREGAMENTO DOS DADOS ---
df = None

# 1. Tenta carregar do GitHub automaticamente
if os.path.exists(NOME_ARQUIVO_PADRAO):
    try:
        df = pd.read_excel(NOME_ARQUIVO_PADRAO)
    except Exception as e:
        st.error(f"Erro ao ler arquivo automático: {e}")

# 2. Se não houver arquivo no GitHub, permite upload manual
if df is None:
    st.sidebar.info("Arquivo automático não encontrado no repositório.")
    arquivo_manual = st.sidebar.file_uploader("Suba uma base para análise:", type=["csv", "xlsx"])
    if arquivo_manual:
        df = pd.read_excel(arquivo_manual) if arquivo_manual.name.endswith('.xlsx') else pd.read_csv(arquivo_manual)

# --- SE OS DADOS FORAM CARREGADOS, MOSTRA O APP ---
if df is not None:
    try:
        # Configurações de Coluna (Auto-detecção para facilitar)
        st.sidebar.header("⚙️ Configurações de Coluna")
        col_bu = st.sidebar.selectbox("Produto/BU:", df.columns, index=0)
        col_data_bruta = st.sidebar.selectbox("Data do Envio:", df.columns, index=3)
        col_abertura = st.sidebar.selectbox("Taxa de Abertura:", df.columns, index=4)
        col_clique = st.sidebar.selectbox("Taxa de Clique:", df.columns, index=5)
        col_assunto = "Assunto" if "Assunto" in df.columns else df.columns[1]

        # Tratamento de Datas e Meses
        df[col_data_bruta] = pd.to_datetime(df[col_data_bruta], errors='coerce')
        df['Mês_Ref'] = df[col_data_bruta].dt.strftime('%m - %B %Y')
        df = df.sort_values(by=col_data_bruta)

        # Filtros na Lateral
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎯 Filtros")
        
        meses_disponiveis = df['Mês_Ref'].unique().tolist()
        meses_selecionados = st.sidebar.multiselect("Selecionar Mês:", options=meses_disponiveis, default=meses_disponiveis)
        
        unidades_disponiveis = df[col_bu].unique().tolist()
        unidades_selecionadas = st.sidebar.multiselect("Selecionar Unidade:", options=unidades_disponiveis, default=unidades_disponiveis)

        # Aplicando filtros
        df_filtrado = df[(df[col_bu].isin(unidades_selecionadas)) & (df['Mês_Ref'].isin(meses_selecionados))].copy()

        # Ajuste e Arredondamento
        def ajustar_e_arredondar(valor):
            if pd.isna(valor): return 0
            num = valor * 100 if valor <= 1.0 else valor
            return round(num, 1)

        df_filtrado[col_abertura] = df_filtrado[col_abertura].apply(ajustar_e_arredondar)
        df_filtrado[col_clique] = df_filtrado[col_clique].apply(ajustar_e_arredondar)

        # --- EXIBIÇÃO KPIs ---
        m1, m2, m3 = st.columns(3)
        media_ab = df_filtrado[col_abertura].mean()
        m1.metric("Abertura Média", f"{media_ab:.1f}%", delta=f"{media_ab - 22:.1f}% vs Meta")
        m2.metric("Clique Médio", f"{df_filtrado[col_clique].mean():.1f}%")
        m3.metric("Eficiência (CTO)", f"{(df_filtrado[col_clique].mean()/media_ab)*100:.1f}%" if media_ab > 0 else "0%")

        # --- GRÁFICO DE EVOLUÇÃO ---
        st.markdown("---")
        st.subheader("📈 Evolução Detalhada por Disparo")
        fig_evol = px.line(df_filtrado, x=col_data_bruta, y=col_abertura, color=col_bu, markers=True)
        fig_evol.update_traces(
            hovertemplate="<b>Assunto:</b> %{customdata[0]}<br><b>Data:</b> %{x|%d/%m}<br><b>Abertura:</b> %{y:.1f}%<extra></extra>",
            customdata=df_filtrado[[col_assunto]]
        )
        st.plotly_chart(fig_evol, use_container_width=True)

        # Tabela
        with st.expander("Ver lista de e-mails detalhada"):
            st.dataframe(df_filtrado[[col_data_bruta, col_bu, col_assunto, col_abertura]].sort_values(by=col_data_bruta, ascending=False))

    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")
else:
    st.info("👋 Bem-vindo! Suba uma planilha ou verifique se o arquivo padrão está no GitHub.")
