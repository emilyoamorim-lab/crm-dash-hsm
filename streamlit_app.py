import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da Página
st.set_page_config(page_title="CRM Dash - Ecossistema HSM/Singularity", layout="wide")

st.title("📊 CRM Analytics - Visão Ecossistema")
st.markdown("Monitoramento de Performance: **Singularity Brazil, HSM Management, Executive Program, Learning Village, HSM Academy e HSM Cobranded.**")

# --- SIDEBAR: CONTROLE TOTAL ---
st.sidebar.header("Painel de Controle")
arquivo = st.sidebar.file_uploader("Suba sua base semanal (Excel ou CSV)", type=["csv", "xlsx"])

if arquivo:
    # Carregamento Inteligente
    df = pd.read_excel(arquivo) if arquivo.name.endswith('.xlsx') else pd.read_csv(arquivo)
    
    # Padronização de nomes (Ajuste para garantir que todas as BUs apareçam)
    # Supondo que a coluna na sua planilha se chame 'BU'
    todas_bus = df['BU'].unique().tolist()

    # Filtros Dinâmicos
    st.sidebar.subheader("Filtros")
    selecao_bus = st.sidebar.multiselect("Unidades de Negócio:", options=todas_bus, default=todas_bus)
    
    df_filtrado = df[df['BU'].isin(selecao_bus)]

    # --- ABA 1: INDICADORES DE PERFORMANCE ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Envios", f"{df_filtrado['Envios Totais'].sum():,}")
    with col2:
        abertura_media = df_filtrado['Taxa de Abertura'].mean()
        st.metric("Abertura Média", f"{abertura_media:.2f}%")
    with col3:
        st.metric("CTR Médio (Clique)", f"{df_filtrado['Taxa de Clique'].mean():.2f}%")
    with col4:
        # Cálculo de eficiência: Cliques por Abertura (CTO)
        cto = (df_filtrado['Taxa de Clique'].mean() / df_filtrado['Taxa de Abertura'].mean()) * 100 if abertura_media > 0 else 0
        st.metric("Eficiência de Conteúdo (CTO)", f"{cto:.2f}%")

    # --- ABA 2: COMPARATIVO ENTRE PRODUTOS ---
    st.markdown("---")
    st.subheader("Performance Comparativa por Unidade")
    
    # Gráfico comparando Abertura vs Clique por BU
    fig = px.bar(df_filtrado, x='BU', y=['Taxa de Abertura', 'Taxa de Clique'], 
                 barmode='group', title="Abertura vs Clique por Produto",
                 color_discrete_map={'Taxa de Abertura': '#1f77b4', 'Taxa de Clique': '#ff7f0e'})
    st.plotly_chart(fig, use_container_width=True)

    # --- ABA 3: RANKING DE CAMPANHAS ---
    st.subheader("Top 5 Campanhas da Semana")
    top_5 = df_filtrado.nlargest(5, 'Taxa de Abertura')[['BU', 'Assunto', 'Taxa de Abertura']]
    st.table(top_5)

else:
    st.info("👋 Olá! Por favor, faça o upload da sua planilha para ativar o dashboard.")
    st.image("https://via.placeholder.com/800x400.png?text=Aguardando+Dados+do+CRM", use_column_width=True)
