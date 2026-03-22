import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="CRM V2 - Performance & Conversão", layout="wide")

# --- CONFIGURAÇÕES FIXAS ---
NOME_ARQUIVO_PADRAO = "Dados CRM 2026 - V3.xlsx"

# Benchmarks Mercado Educação Corporativa
META_ABERTURA = 22.0
META_CTR = 2.5
META_CTO = 12.0

st.title("🚀 Dashboard CRM V2: Conversão e CTAs")

# --- FUNÇÃO DE LIMPEZA ---
def limpar_porcentagem(valor):
    if pd.isna(valor): return 0.0
    if isinstance(valor, str):
        valor = valor.replace('%', '').replace(',', '.')
        try: return float(valor)
        except: return 0.0
    return float(valor) * 100 if valor <= 1.0 else float(valor)

# --- CARREGAMENTO E CRUZAMENTO ---
if os.path.exists(NOME_ARQUIVO_PADRAO):
    try:
        excel = pd.ExcelFile(NOME_ARQUIVO_PADRAO)
        
        # Lendo abas por posição (0=Perf, 1=Conv)
        df_perf = excel.parse(0) 
        df_conv = excel.parse(1) 

        df_perf.columns = [str(col).strip() for col in df_perf.columns]
        df_conv.columns = [str(col).strip() for col in df_conv.columns]

        # Chaves para cruzamento
        chaves_merge = ["BU", "Produto", "Emails Enviados"]
        colunas_conv = [c for c in ["CTA", "Formato", "Oportunidades"] if c in df_conv.columns]
        
        df = pd.merge(df_perf, df_conv[chaves_merge + colunas_conv], on=chaves_merge, how="left")

        # Tratamento de dados
        df["Hora de Início do Envio"] = pd.to_datetime(df["Hora de Início do Envio"], errors='coerce')
        df = df.dropna(subset=["Hora de Início do Envio"])
        df["Emails Enviados"] = pd.to_numeric(df["Emails Enviados"], errors='coerce').fillna(0)
        df["Oportunidades"] = pd.to_numeric(df.get("Oportunidades", 0), errors='coerce').fillna(0)
        
        # Padronização de nomes de colunas de taxa para facilidade no código
        COL_ABERTURA = "Taxa de Abertura"
        COL_CLIQUE = "Taxa de Click Through Total"
        
        df[COL_ABERTURA] = df[COL_ABERTURA].apply(limpar_porcentagem)
        df[COL_CLIQUE] = df[COL_CLIQUE].apply(limpar_porcentagem)
        
        df = df.sort_values(by="Hora de Início do Envio")

    except Exception as e:
        st.error(f"Erro ao processar as bases: {e}")
        st.stop()

if 'df' in locals() and not df.empty:
    # --- FILTROS DINÂMICOS NA LATERAL ---
    st.sidebar.header("🎯 Filtros de Busca")

    # 1. Calendário
    min_date = df["Hora de Início do Envio"].min().date()
    max_date = df["Hora de Início do Envio"].max().date()
    date_range = st.sidebar.date_input("1. Período:", value=(min_date, max_date))

    # 2. BU
    bus_disponiveis = sorted(df["BU"].unique())
    bus_sel = st.sidebar.multiselect("2. Selecionar BU:", options=bus_disponiveis, default=bus_disponiveis)

    # 3. Produto (Em cascata)
    df_temp = df[df["BU"].isin(bus_sel)]
    prods_disponiveis = sorted(df_temp["Produto"].unique())
    prods_sel = st.sidebar.multiselect("3. Selecionar Produto:", options=prods_disponiveis, default=prods_disponiveis)

    # Aplicação Final dos Filtros
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        df_filtrado = df[
            (df["Hora de Início do Envio"].dt.date >= start_date) & 
            (df["Hora de Início do Envio"].dt.date <= end_date) &
            (df["BU"].isin(bus_sel)) &
            (df["Produto"].isin(prods_sel))
        ].copy()
    else:
        df_filtrado = df[(df["BU"].isin(bus_sel)) & (df["Produto"].isin(prods_sel))].copy()

    if not df_filtrado.empty:
        # --- KPIs DE TOPO (Com Comparações de Mercado) ---
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        
        total_base = df_filtrado["Emails Enviados"].sum()
        total_opts = df_filtrado["Oportunidades"].sum()
        media_or = df_filtrado[COL_ABERTURA].mean()
        media_ctr = df_filtrado[COL_CLIQUE].mean()
        cto_medio = (media_ctr / media_or * 100) if media_or > 0 else 0
        taxa_conv = (total_opts / total_base * 100) if total_base > 0 else 0

        m1.metric("Base de Envio", f"{total_base:,.0f}".replace(",", "."))
        m2.metric("Oportunidades", f"{total_opts:,.0f}")
        m3.metric("Abertura (OR)", f"{media_or:.1f}%", delta=f"{media_or - META_ABERTURA:.1f}%")
        m4.metric("Clique (CTR)", f"{media_ctr:.1f}%", delta=f"{media_ctr - META_CTR:.1f}%")
        m5.metric("Eficiência (CTO)", f"{cto_medio:.1f}%", delta=f"{cto_medio - META_CTO:.1f}%")
        m6.metric("Conv. Final", f"{taxa_conv:.2f}%")

        # --- ANÁLISE DO ESPECIALISTA E RECORDISTAS ---
        st.markdown("---")
        col_an1, col_an2 = st.columns([1.8, 1.2])

        recordista_or = df_filtrado.loc[df_filtrado[COL_ABERTURA].idxmax()]
        recordista_ctr = df_filtrado.loc[df_filtrado[COL_CLIQUE].idxmax()]
        recordista_opt = df_filtrado.loc[df_filtrado["Oportunidades"].idxmax()]

        with col_an1:
            st.subheader("🕵️ Análise do Especialista")
            status_cto = "Elite" if cto_medio > 40 else "Saudável"
            st.info(f"""
            **Diagnóstico de Performance: {recordista_or['Produto']}**
            
            No período analisado, o destaque de engajamento inicial foi o disparo de **{recordista_or['Hora de Início do Envio'].strftime('%d/%m')}**, que alcançou uma abertura de **{recordista_or[COL_ABERTURA]:.1f}%**.
            
            **Conversão de Negócio:** O produto que mais gerou oportunidades reais foi o **{recordista_opt['Produto']}**, convertendo **{recordista_opt['Oportunidades']:.0f} leads** qualificados através do CTA **"{recordista_opt.get('CTA', 'N/A')}"**. 
            
            **Eficiência de Conteúdo:** O seu CTO médio de **{cto_medio:.1f}%** (Meta: {META_CTO}%) valida que a régua de comunicação está com performance de **{status_cto}**, garantindo que quem abre o e-mail tem alta propensão ao clique.
            """)

        with col_an2:
            st.subheader("🏆 Recordistas do Filtro")
            st.success(f"🔥 **Melhor OR:** {recordista_or[COL_ABERTURA]:.1f}% \n\n **Assunto:** {recordista_or['Assunto']}")
            st.info(f"🚀 **Melhor CTR:** {recordista_ctr[COL_CLIQUE]:.1f}% \n\n **Base Envio:** {recordista_ctr['Emails Enviados']:,.0f}")
            st.warning(f"💰 **Mais Oportunidades:** {recordista_opt['Oportunidades']:.0f} Opts \n\n **CTA:** {recordista_opt.get('CTA', 'N/A')}")

        # --- GRÁFICOS DE CONVERSÃO ---
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🎯 Oportunidades por CTA")
            df_cta = df_filtrado.groupby("CTA")["Oportunidades"].sum().reset_index().sort_values("Oportunidades")
            fig_cta = px.bar(df_cta, x="Oportunidades", y="CTA", orientation='h', color_discrete_sequence=['#00CC96'])
            st.plotly_chart(fig_cta, use_container_width=True)
        with c2:
            st.subheader("📱 Conversão por Formato")
            df_form = df_filtrado.groupby("Formato")["Oportunidades"].sum().reset_index()
            fig_form = px.pie(df_form, values="Oportunidades", names="Formato", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_form, use_container_width=True)

        # --- GRÁFICOS DE TENDÊNCIA (V1 Estilo) ---
        st.markdown("---")
        st.subheader("📈 Tendência: Taxa de Abertura (OR)")
        fig_or = px.line(df_filtrado, x="Hora de Início do Envio", y=COL_ABERTURA, color="Produto", markers=True, labels={"Hora de Início do Envio": "Data"})
        st.plotly_chart(fig_or, use_container_width=True)

        st.subheader("📈 Tendência: Taxa de Clique (CTR)")
        fig_ctr = px.line(df_filtrado, x="Hora de Início do Envio", y=COL_CLIQUE, color="Produto", markers=True, labels={"Hora de Início do Envio": "Data", COL_CLIQUE: "Taxa de Clique"})
        st.plotly_chart(fig_ctr, use_container_width=True)

        with st.expander("📋 Ver Dados Cruzados Completos"):
            st.dataframe(df_filtrado)
    else:
        st.warning("Selecione filtros válidos para visualizar os dados.")
else:
    st.info("👋 Suba o arquivo 'Dados CRM 2026 - V3.xlsx' com as duas abas para ativar.")
