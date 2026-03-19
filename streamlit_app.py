import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da Página
st.set_page_config(page_title="CRM Performance - Ecossistema HSM", layout="wide")

# --- CONFIGURAÇÕES FIXAS DAS COLUNAS ---
NOME_ARQUIVO_PADRAO = "Dados CRM 2026 - V2.xlsx"
COL_BU = "BU"                    # Unidade (Ex: HSM Management, Singularity)
COL_PRODUTO = "Produto"          # Produto específico (Ex: Executive Program T16)
COL_DATA = "Hora de Início do Envio"
COL_ABERTURA = "Taxa de Abertura"
COL_CLIQUE = "Taxa de Click Through Total"
COL_ASSUNTO = "Assunto"

st.title("📊 Dashboard de Performance CRM")
st.markdown("Análise estratégica segmentada por Unidade e Produto.")

# --- CARREGAMENTO AUTOMÁTICO ---
df = None
if os.path.exists(NOME_ARQUIVO_PADRAO):
    try:
        df = pd.read_excel(NOME_ARQUIVO_PADRAO)
    except Exception as e:
        st.error(f"Erro ao carregar a base: {e}")

if df is not None:
    try:
        # Tratamento de Datas
        df[COL_DATA] = pd.to_datetime(df[COL_DATA], errors='coerce')
        df['Mês_Ref'] = df[COL_DATA].dt.strftime('%m - %B %Y')
        df = df.sort_values(by=COL_DATA)

        # --- FILTROS EM CASCATA (SIDEBAR) ---
        st.sidebar.header("🎯 Filtros de Busca")

        # 1. Filtro de Período
        meses_disponiveis = sorted(df['Mês_Ref'].unique().tolist())
        meses_sel = st.sidebar.multiselect("1. Selecionar Período:", options=meses_disponiveis, default=meses_disponiveis)

        # 2. Filtro de BU (Unidade de Negócio)
        bus_disponiveis = sorted(df[COL_BU].unique().tolist())
        bus_sel = st.sidebar.multiselect("2. Selecionar BU:", options=bus_disponiveis, default=bus_disponiveis)

        # --- LÓGICA DA CASCATA ---
        # Filtramos o DF temporariamente para saber quais produtos existem nas BUs selecionadas
        df_temp = df[df[COL_BU].isin(bus_sel)]
        produtos_disponiveis = sorted(df_temp[COL_PRODUTO].unique().tolist())

        # 3. Filtro de Produto (Só mostra o que pertence às BUs selecionadas)
        produtos_sel = st.sidebar.multiselect("3. Selecionar Produto:", options=produtos_disponiveis, default=produtos_disponiveis)

        # --- APLICAÇÃO FINAL DOS FILTROS ---
        df_filtrado = df[
            (df['Mês_Ref'].isin(meses_sel)) & 
            (df[COL_BU].isin(bus_sel)) & 
            (df[COL_PRODUTO].isin(produtos_sel))
        ].copy()

        # Tratamento de Taxas
        def formatar_taxa(valor):
            if pd.isna(valor): return 0
            num = valor * 100 if valor <= 1.0 else valor
            return round(num, 1)

        df_filtrado[COL_ABERTURA] = df_filtrado[COL_ABERTURA].apply(formatar_taxa)
        df_filtrado[COL_CLIQUE] = df_filtrado[COL_CLIQUE].apply(formatar_taxa)

        # --- EXIBIÇÃO KPIs ---
        if not df_filtrado.empty:
            m1, m2, m3 = st.columns(3)
            media_ab = df_filtrado[COL_ABERTURA].mean()
            media_cl = df_filtrado[COL_CLIQUE].mean()
            
            m1.metric("Abertura Média", f"{media_ab:.1f}%", delta=f"{media_ab - 22:.1f}% vs Meta")
            m2.metric("Clique Médio (CTR)", f"{media_cl:.1f}%")
            m3.metric("Eficiência (CTO)", f"{(media_cl/media_ab)*100:.1f}%" if media_ab > 0 else "0%")

            # --- GRÁFICO DE EVOLUÇÃO ---
            st.markdown("---")
            st.subheader("📈 Evolução dos Disparos")
            
            fig_evol = px.line(df_filtrado, x=COL_DATA, y=COL_ABERTURA, color=COL_PRODUTO, markers=True)
            fig_evol.update_traces(
                hovertemplate="<b>Produto:</b> %{fullData.name}<br><b>Assunto:</b> %{customdata[0]}<br><b>Abertura:</b> %{y:.1f}%<extra></extra>",
                customdata=df_filtrado[[COL_ASSUNTO]]
            )
            st.plotly_chart(fig_evol, use_container_width=True)

            # Tabela
            with st.expander("📋 Ver Tabela de Dados"):
                st.dataframe(df_filtrado[[COL_DATA, COL_BU, COL_PRODUTO, COL_ASSUNTO, COL_ABERTURA]].sort_values(by=COL_DATA, ascending=False), use_container_width=True)
        else:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")

    except Exception as e:
        st.error(f"Erro: {e}")
else:
    st.info("👋 Arquivo de dados não encontrado no GitHub. Verifique o nome do arquivo.")
