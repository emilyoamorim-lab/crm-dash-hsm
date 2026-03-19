import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração visual
st.set_page_config(page_title="CRM Dash - Ecossistema HSM/Singularity", layout="wide")

st.title("📊 Dashboard de Performance CRM")
st.markdown("---")

# 1. SIDEBAR - Upload e Filtros
st.sidebar.header("Configurações")
arquivo = st.sidebar.file_uploader("Suba sua base semanal (Excel ou CSV)", type=["csv", "xlsx"])

if arquivo:
    try:
        # Lendo o arquivo (suporta Excel e CSV)
        if arquivo.name.endswith('.xlsx'):
            df = pd.read_excel(arquivo)
        else:
            df = pd.read_csv(arquivo)
        
        # --- Limpeza e Padronização (Ajuste os nomes das colunas se necessário) ---
        # Aqui o app tenta identificar as colunas automaticamente
        col_bu = st.sidebar.selectbox("Coluna de Produto (BU):", df.columns)
        col_abertura = st.sidebar.selectbox("Coluna de Taxa de Abertura:", df.columns)
        col_clique = st.sidebar.selectbox("Coluna de Taxa de Clique:", df.columns)
        
        # Filtros dinâmicos
        unidades = st.sidebar.multiselect("Filtrar por Unidade:", options=df[col_bu].unique(), default=df[col_bu].unique())
        df_filtrado = df[df[col_bu].isin(unidades)]

        # --- ABA 1: KPIs GERAIS ---
        st.subheader("📌 Visão Geral de Performance")
        m1, m2, m3 = st.columns(3)
        
        media_ab = df_filtrado[col_abertura].mean()
        media_cl = df_filtrado[col_clique].mean()
        
        # Benchmark de mercado (Educação Corporativa: ~22%)
        m1.metric("Abertura Média", f"{media_ab:.2f}%", delta=f"{media_ab - 22:.1f}% vs Mercado")
        m2.metric("Clique Médio (CTR)", f"{media_cl:.2f}%", delta=f"{media_cl - 2.5:.1f}% vs Mercado")
        m3.metric("Eficiência (CTO)", f"{(media_cl/media_ab)*100:.1f}%")

        # --- ABA 2: GRÁFICOS ---
        st.markdown("---")
        col_esq, col_dir = st.columns(2)

        with col_esq:
            st.subheader("Comparativo por Produto")
            fig_prod = px.bar(df_filtrado, x=col_bu, y=col_abertura, color=col_bu, 
                             title="Taxa de Abertura por BU", text_auto='.2s')
            st.plotly_chart(fig_prod, use_container_width=True)

        with col_dir:
            st.subheader("Relação Abertura x Clique")
            fig_scatter = px.scatter(df_filtrado, x=col_abertura, y=col_clique, color=col_bu,
                                    hover_name=col_bu, size_max=60, title="Eficiência do Disparo")
            st.plotly_chart(fig_scatter, use_container_width=True)

        # --- ABA 3: LABORATÓRIO DE HIPÓTESES ---
        st.markdown("---")
        st.subheader("🧪 Laboratório de Inteligência")
        
        # Lógica Automática de Insights
        if media_ab < 20:
            st.warning("**Insight:** Suas taxas de abertura estão abaixo da média de Educação B2B. **Hipótese:** Teste assuntos com o nome do remetente sendo uma pessoa real (Ex: 'Ana da HSM').")
        else:
            st.success("**Insight:** Sua estratégia de 'Bases Refinadas' de Março está funcionando! **Próximo passo:** Foque agora em melhorar o CTA para aumentar o clique.")

        # Exibir a base para conferência
        with st.expander("Ver base completa filtrada"):
            st.write(df_filtrado)

    except Exception as e:
        st.error(f"Erro ao processar: {e}. Verifique se as colunas estão corretas.")
else:
    st.info("👋 Tudo pronto! Agora é só subir sua planilha ali na esquerda para ver a mágica.")
    # Exemplo de como deve ser a planilha
    st.image("https://via.placeholder.com/800x200.png?text=Dica:+Sua+planilha+deve+ter+colunas+como+BU,+Abertura+e+Clique")
