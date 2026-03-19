import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração visual
st.set_page_config(page_title="CRM Dash - Ecossistema HSM/Singularity", layout="wide")

st.title("📊 Dashboard de Performance CRM")
st.markdown("---")

# 1. SIDEBAR - Configurações
st.sidebar.header("⚙️ Configurações")
arquivo = st.sidebar.file_uploader("Suba sua base semanal", type=["csv", "xlsx"])

if arquivo:
    try:
        # Carregamento dos dados
        df = pd.read_excel(arquivo) if arquivo.name.endswith('.xlsx') else pd.read_csv(arquivo)
        
        # Mapeamento de Colunas
        st.sidebar.subheader("Mapeamento de Colunas")
        col_bu = st.sidebar.selectbox("Produto/BU:", df.columns, index=0)
        col_data_bruta = st.sidebar.selectbox("Coluna de Data/Hora:", df.columns, index=3)
        col_abertura = st.sidebar.selectbox("Taxa de Abertura:", df.columns, index=4)
        col_clique = st.sidebar.selectbox("Taxa de Clique:", df.columns, index=5)

        # --- TRATAMENTO DE DATAS (O SEGREDO DO FILTRO) ---
        # Converte a coluna para data e cria uma coluna de "Mês/Ano" amigável
        df[col_data_bruta] = pd.to_datetime(df[col_data_bruta], errors='coerce')
        df['Mês_Ref'] = df[col_data_bruta].dt.strftime('%m - %B %Y') 
        # Ordenação para os meses aparecerem na ordem correta (Jan, Fev, Mar)
        df = df.sort_values(by=col_data_bruta)
        meses_disponiveis = df['Mês_Ref'].unique().tolist()

        # --- FILTROS DINÂMICOS ---
        st.sidebar.markdown("---")
        st.sidebar.subheader("🎯 Filtros de Visualização")
        
        # Agora o filtro é por MÊS e não por hora/minuto
        meses_selecionados = st.sidebar.multiselect("Selecionar Mês:", options=meses_disponiveis, default=meses_disponiveis)
        
        todas_unidades = df[col_bu].unique().tolist()
        unidades_selecionadas = st.sidebar.multiselect("Selecionar Unidade:", options=todas_unidades, default=todas_unidades)

        # Aplicando filtros
        df_filtrado = df[
            (df[col_bu].isin(unidades_selecionadas)) & 
            (df['Mês_Ref'].isin(meses_selecionados))
        ].copy()

        # --- CORREÇÃO MATEMÁTICA ---
        def ajustar_porcentagem(valor):
            if pd.isna(valor): return 0
            if valor <= 1.0: return valor * 100
            return valor

        df_filtrado[col_abertura] = df_filtrado[col_abertura].apply(ajustar_porcentagem)
        df_filtrado[col_clique] = df_filtrado[col_clique].apply(ajustar_porcentagem)

        # --- EXIBIÇÃO DOS KPIs ---
        st.subheader(f"📌 Resultados: {', '.join(meses_selecionados) if len(meses_selecionados) < 4 else 'Todo o Período'}")
        
        kpi1, kpi2, kpi3 = st.columns(3)
        media_ab = df_filtrado[col_abertura].mean()
        media_cl = df_filtrado[col_clique].mean()
        
        # Agora o 20.25% aparecerá de forma legível
        kpi1.metric("Abertura Média", f"{media_ab:.2f}%", delta=f"{media_ab - 22:.1f}% vs Meta")
        kpi2.metric("Clique Médio (CTR)", f"{media_cl:.2f}%", delta=f"{media_cl - 2.5:.1f}% vs Meta")
        kpi3.metric("Eficiência (CTO)", f"{(media_cl/media_ab)*100:.1f}%" if media_ab > 0 else "0%")

        # --- GRÁFICO DE EVOLUÇÃO ---
        st.markdown("---")
        st.subheader("Evolução Mensal da Abertura")
        df_mensal = df_filtrado.groupby('Mês_Ref')[col_abertura].mean().reset_index()
        fig_evol = px.line(df_mensal, x='Mês_Ref', y=col_abertura, markers=True, 
                          text=df_mensal[col_abertura].map('{:.1f}%'.format))
        st.plotly_chart(fig_evol, use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao processar datas: {e}. Certifique-se de que a coluna de data está no formato correto.")
else:
    st.info("👋 Suba sua planilha para começar!")
