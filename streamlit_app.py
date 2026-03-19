import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da Página
st.set_page_config(page_title="CRM Performance - HSM/Singularity", layout="wide")

# --- CONFIGURAÇÕES FIXAS (NOMES DAS COLUNAS NA SUA PLANILHA) ---
NOME_ARQUIVO_PADRAO = "Dados CRM 2026 - V2.xlsx"
COL_PRODUTO = "Produto"
COL_DATA = "Hora de Início do Envio"
COL_ABERTURA = "Taxa de Abertura"
COL_CLIQUE = "Taxa de Click Through Total"
COL_ASSUNTO = "Assunto"

st.title("📊 Dashboard de Performance CRM")
st.markdown("Relatório estratégico consolidado de campanhas.")

# --- CARREGAMENTO AUTOMÁTICO ---
df = None
if os.path.exists(NOME_ARQUIVO_PADRAO):
    try:
        df = pd.read_excel(NOME_ARQUIVO_PADRAO)
    except Exception as e:
        st.error(f"Erro ao carregar a base: {e}")

if df is not None:
    try:
        # Tratamento de Datas e Meses
        df[COL_DATA] = pd.to_datetime(df[COL_DATA], errors='coerce')
        df['Mês_Ref'] = df[COL_DATA].dt.strftime('%m - %B %Y')
        df = df.sort_values(by=COL_DATA)

        # --- FILTROS LATERAIS (Apenas para consulta) ---
        st.sidebar.header("🎯 Filtros de Consulta")
        
        meses_disponiveis = df['Mês_Ref'].unique().tolist()
        meses_selecionados = st.sidebar.multiselect("Selecionar Mês:", options=meses_disponiveis, default=meses_disponiveis)
        
        unidades_disponiveis = df[COL_PRODUTO].unique().tolist()
        unidades_selecionadas = st.sidebar.multiselect("Selecionar Unidade:", options=unidades_disponiveis, default=unidades_disponiveis)

        # Aplicação dos Filtros
        df_filtrado = df[(df[COL_PRODUTO].isin(unidades_selecionadas)) & (df['Mês_Ref'].isin(meses_selecionados))].copy()

        # --- TRATAMENTO DAS TAXAS (Arredondamento e Escala) ---
        def formatar_taxa(valor):
            if pd.isna(valor): return 0
            # Se o dado vier como 0.22, transforma em 22. Se vier como 22, mantém 22.
            num = valor * 100 if valor <= 1.0 else valor
            return round(num, 1)

        df_filtrado[COL_ABERTURA] = df_filtrado[COL_ABERTURA].apply(formatar_taxa)
        df_filtrado[COL_CLIQUE] = df_filtrado[COL_CLIQUE].apply(formatar_taxa)

        # --- EXIBIÇÃO KPIs ---
        m1, m2, m3 = st.columns(3)
        media_ab = df_filtrado[COL_ABERTURA].mean()
        media_cl = df_filtrado[COL_CLIQUE].mean()
        
        m1.metric("Abertura Média", f"{media_ab:.1f}%", delta=f"{media_ab - 22:.1f}% vs Meta")
        m2.metric("Clique Médio (CTR)", f"{media_cl:.1f}%")
        m3.metric("Eficiência (CTO)", f"{(media_cl/media_ab)*100:.1f}%" if media_ab > 0 else "0%")

        # --- GRÁFICO DE EVOLUÇÃO ---
        st.markdown("---")
        st.subheader("📈 Evolução Detalhada por Disparo")
        
        fig_evol = px.line(df_filtrado, 
                          x=COL_DATA, 
                          y=COL_ABERTURA, 
                          color=COL_PRODUTO,
                          markers=True,
                          title="Taxa de Abertura ao Longo do Período")
        
        fig_evol.update_traces(
            hovertemplate="<b>Assunto:</b> %{customdata[0]}<br><b>Abertura:</b> %{y:.1f}%<extra></extra>",
            customdata=df_filtrado[[COL_ASSUNTO]]
        )
        
        fig_evol.update_layout(xaxis_title="Data do Envio", yaxis_title="Abertura (%)")
        st.plotly_chart(fig_evol, use_container_width=True)

        # Tabela Detalhada
        with st.expander("📋 Ver Detalhes dos E-mails"):
            st.dataframe(df_filtrado[[COL_DATA, COL_PRODUTO, COL_ASSUNTO, COL_ABERTURA]].sort_values(by=COL_DATA, ascending=False), use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao processar os dados: {e}. Verifique se as colunas da planilha não mudaram de nome.")
else:
    st.info("👋 O arquivo de dados não foi encontrado. Certifique-se de subir 'Dados CRM 2026 - V2.xlsx' para o GitHub.")
