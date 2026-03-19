import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da Página
st.set_page_config(page_title="CRM Performance - Ecossistema HSM", layout="wide")

# --- CONFIGURAÇÕES FIXAS ---
NOME_ARQUIVO_PADRAO = "Dados CRM 2026 - V2.xlsx"
COL_BU = "BU"
COL_PRODUTO = "Produto"
COL_DATA = "Hora de Início do Envio"
COL_ABERTURA = "Taxa de Abertura"
COL_CLIQUE = "Taxa de Click Through Total"
COL_ASSUNTO = "Assunto"

st.title("📊 Dashboard de Performance CRM")

# --- CARREGAMENTO ---
df = None
if os.path.exists(NOME_ARQUIVO_PADRAO):
    try:
        df = pd.read_excel(NOME_ARQUIVO_PADRAO)
    except Exception as e:
        st.error(f"Erro ao carregar a base: {e}")

if df is not None:
    try:
        df[COL_DATA] = pd.to_datetime(df[COL_DATA], errors='coerce')
        df['Mês_Ref'] = df[COL_DATA].dt.strftime('%m - %B %Y')
        df = df.sort_values(by=COL_DATA)

        # --- FILTROS EM CASCATA ---
        st.sidebar.header("🎯 Filtros de Busca")
        meses_disponiveis = sorted(df['Mês_Ref'].unique().tolist())
        meses_sel = st.sidebar.multiselect("1. Selecionar Período:", options=meses_disponiveis, default=meses_disponiveis)

        bus_disponiveis = sorted(df[COL_BU].unique().tolist())
        bus_sel = st.sidebar.multiselect("2. Selecionar BU:", options=bus_disponiveis, default=bus_disponiveis)

        df_temp = df[df[COL_BU].isin(bus_sel)]
        produtos_disponiveis = sorted(df_temp[COL_PRODUTO].unique().tolist())
        produtos_sel = st.sidebar.multiselect("3. Selecionar Produto:", options=produtos_disponiveis, default=produtos_disponiveis)

        # Aplicação dos Filtros
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

            # --- GRÁFICO ---
            st.markdown("---")
            st.subheader("📈 Evolução dos Disparos")
            fig_evol = px.line(df_filtrado, x=COL_DATA, y=COL_ABERTURA, color=COL_PRODUTO, markers=True)
            fig_evol.update_traces(
                hovertemplate="<b>Produto:</b> %{fullData.name}<br><b>Assunto:</b> %{customdata[0]}<br><b>Abertura:</b> %{y:.1f}%<extra></extra>",
                customdata=df_filtrado[[COL_ASSUNTO]]
            )
            st.plotly_chart(fig_evol, use_container_width=True)

            # --- NOVO: ANÁLISE DE CENÁRIOS E HIGHLIGHTS ---
            st.markdown("---")
            col_an1, col_an2 = st.columns([2, 1])

            with col_an1:
                st.subheader("🕵️ Análise do Especialista")
                
                # Lógica de análise baseada no filtro
                if len(produtos_sel) == 1:
                    prod_nome = produtos_sel[0]
                    melhor_disparo = df_filtrado.loc[df_filtrado[COL_ABERTURA].idxmax()]
                    
                    st.write(f"Analisando o desempenho de **{prod_nome}**:")
                    
                    if "March" in str(meses_sel):
                        st.info(f"**Cenário de Março:** Observamos picos de engajamento que sugerem uma base mais qualificada. O ponto alto de **{melhor_disparo[COL_ABERTURA]}%** de abertura mostra que o assunto abordado gerou alta curiosidade ou urgência no público de educação executiva.")
                    
                    if media_ab >= 22:
                        st.success(f"🚀 O produto está **acima da meta de mercado**. A estratégia de segmentação está validada.")
                    else:
                        st.warning(f"⚠️ O desempenho médio está **abaixo da meta (22%)**. Recomendamos testar novos ganchos de assunto para aumentar a atratividade.")

                else:
                    st.write("Selecione **apenas um produto** para ver a análise detalhada de cenário.")

            with col_an2:
                st.subheader("🌟 Highlights")
                if not df_filtrado.empty:
                    melhor = df_filtrado.nlargest(1, COL_ABERTURA).iloc[0]
                    st.write(f"🏆 **Melhor Assunto:** \n*{melhor[COL_ASSUNTO]}*")
                    st.write(f"🔥 **Pico de Abertura:** {melhor[COL_ABERTURA]}%")
                    st.write(f"📅 **Data do Top Result:** {melhor[COL_DATA].strftime('%d/%m/%Y')}")

            # Tabela
            with st.expander("📋 Ver Tabela de Dados Completa"):
                st.dataframe(df_filtrado[[COL_DATA, COL_BU, COL_PRODUTO, COL_ASSUNTO, COL_ABERTURA]].sort_values(by=COL_DATA, ascending=False), use_container_width=True)
        else:
            st.warning("Selecione os filtros na barra lateral para carregar a análise.")

    except Exception as e:
        st.error(f"Erro: {e}")
else:
    st.info("👋 Aguardando base de dados...")
