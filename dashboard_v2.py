import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="CRM V2 - Conversão & CTAs", layout="wide")

# --- CONFIGURAÇÕES FIXAS ---
NOME_ARQUIVO_PADRAO = "Dados CRM 2026 - V2.xlsx"

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
        
        # --- MUDANÇA AQUI: Lendo por POSIÇÃO e não por NOME ---
        # 0 é a primeira aba, 1 é a segunda aba
        df_perf = excel.parse(0) 
        df_conv = excel.parse(1) 

        df_perf.columns = [str(col).strip() for col in df_perf.columns]
        df_conv.columns = [str(col).strip() for col in df_conv.columns]

        # Cruzamento (Merge)
        chaves_merge = ["BU", "Produto", "Emails Enviados"]
        df = pd.merge(df_perf, df_conv[chaves_merge + ["CTA", "Formato", "Oportunidades"]], 
                      on=chaves_merge, how="left")

        # Tratamento de Datas e Tipos
        df["Hora de Início do Envio"] = pd.to_datetime(df["Hora de Início do Envio"], errors='coerce')
        df = df.dropna(subset=["Hora de Início do Envio"])
        df["Emails Enviados"] = pd.to_numeric(df["Emails Enviados"], errors='coerce').fillna(0)
        df["Oportunidades"] = pd.to_numeric(df["Oportunidades"], errors='coerce').fillna(0)
        
        df["Taxa de Abertura"] = df["Taxa de Abertura"].apply(limpar_porcentagem)
        df["Taxa de Click Through Total"] = df["Taxa de Click Through Total"].apply(limpar_porcentagem)
        
        df = df.sort_values(by="Hora de Início do Envio")

    except Exception as e:
        st.error(f"Erro crítico ao cruzar bases: {e}")
        st.stop()

if 'df' in locals() and not df.empty:
    # --- FILTROS NA LATERAL ---
    st.sidebar.header("🎯 Filtros Dinâmicos")

    min_date = df["Hora de Início do Envio"].min().date()
    max_date = df["Hora de Início do Envio"].max().date()
    
    date_range = st.sidebar.date_input(
        "1. Selecionar Período (Início - Fim):",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    bus_disponiveis = sorted(df["BU"].unique())
    bus_sel = st.sidebar.multiselect("2. Selecionar BU:", options=bus_disponiveis, default=bus_disponiveis)

    # Aplicação dos Filtros
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        df_filtrado = df[
            (df["Hora de Início do Envio"].dt.date >= start_date) & 
            (df["Hora de Início do Envio"].dt.date <= end_date) &
            (df["BU"].isin(bus_sel))
        ].copy()
    else:
        df_filtrado = df[df["BU"].isin(bus_sel)].copy()

    if not df_filtrado.empty:
        # --- 1. KPIs DE NEGÓCIO ---
        m1, m2, m3, m4 = st.columns(4)
        total_base = df_filtrado["Emails Enviados"].sum()
        total_opts = df_filtrado["Oportunidades"].sum()
        media_or = df_filtrado["Taxa de Abertura"].mean()
        taxa_conv = (total_opts / total_base * 100) if total_base > 0 else 0

        m1.metric("Base Total de Envio", f"{total_base:,.0f}".replace(",", "."))
        m2.metric("Oportunidades Geradas", f"{total_opts:,.0f}")
        m3.metric("Abertura Média (OR)", f"{media_or:.1f}%")
        m4.metric("Taxa de Conversão Final", f"{taxa_conv:.2f}%")

        # --- 2. ANÁLISE DE CTAs ---
        st.markdown("---")
        col_cta1, col_cta2 = st.columns(2)

        with col_cta1:
            st.subheader("🎯 Oportunidades por CTA")
            df_cta = df_filtrado.groupby("CTA")["Oportunidades"].sum().reset_index().sort_values("Oportunidades", ascending=True)
            fig_cta = px.bar(df_cta, x="Oportunidades", y="CTA", orientation='h', color_discrete_sequence=['#00CC96'])
            st.plotly_chart(fig_cta, use_container_width=True)

        with col_cta2:
            st.subheader("📱 Conversão por Formato")
            df_form = df_filtrado.groupby("Formato")["Oportunidades"].sum().reset_index()
            fig_form = px.pie(df_form, values="Oportunidades", names="Formato", hole=0.4)
            st.plotly_chart(fig_form, use_container_width=True)

        # --- 3. ANÁLISE DO ESPECIALISTA ---
        st.markdown("---")
        if total_opts > 0:
            recordista_opts = df_filtrado.loc[df_filtrado["Oportunidades"].idxmax()]
            st.info(f"""
            **🕵️ Análise de Conversão V2**
            O produto **{recordista_opts['Produto']}** lidera em geração de negócios com **{recordista_opts['Oportunidades']} oportunidades**.
            O canal de maior relevância atual é o formato de CTA via **{df_form.sort_values('Oportunidades', ascending=False).iloc[0]['Formato']}**.
            """)
        else:
            st.warning("Nenhuma oportunidade registrada no período selecionado.")

        # --- 4. GRÁFICOS DE TENDÊNCIA ---
        st.markdown("---")
        st.subheader("📈 Tendência: Taxa de Abertura (OR)")
        fig_abert = px.line(df_filtrado, x="Hora de Início do Envio", y="Taxa de Abertura", color="Produto", markers=True)
        st.plotly_chart(fig_abert, use_container_width=True)

        with st.expander("📋 Ver Tabela de Dados Cruzados"):
            st.dataframe(df_filtrado[["Hora de Início do Envio", "BU", "Produto", "Assunto", "Emails Enviados", "CTA", "Formato", "Oportunidades"]])
    else:
        st.warning("Selecione um intervalo de datas e BU para carregar os dados.")
else:
    st.info("👋 Por favor, verifique se o arquivo 'Dados CRM 2026 - V2.xlsx' está no GitHub.")
