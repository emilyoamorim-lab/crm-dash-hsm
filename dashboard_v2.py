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

# --- FUNÇÃO DE LIMPEZA DE PORCENTAGEM ---
def limpar_porcentagem(valor):
    if pd.isna(valor): return 0.0
    if isinstance(valor, str):
        valor = valor.replace('%', '').replace(',', '.')
        try: return float(valor)
        except: return 0.0
    return float(valor) * 100 if valor <= 1.0 else float(valor)

# --- CARREGAMENTO E CRUZAMENTO ---
df = pd.DataFrame() # Cria um dataframe vazio por segurança

if os.path.exists(NOME_ARQUIVO_PADRAO):
    try:
        excel = pd.ExcelFile(NOME_ARQUIVO_PADRAO)
        
        # Verificação de Abas
        abas_encontradas = excel.sheet_names
        if len(abas_encontradas) < 2:
            st.error(f"⚠️ O arquivo no GitHub só tem {len(abas_encontradas)} aba: {abas_encontradas}")
            st.info("Para a V2 funcionar, o Excel precisa de 2 abas: 1ª Performance e 2ª Conversão.")
            st.stop()
        
        # Lendo abas por posição (0 e 1)
        df_perf = excel.parse(0) 
        df_conv = excel.parse(1) 

        # Limpeza de nomes de colunas
        df_perf.columns = [str(col).strip() for col in df_perf.columns]
        df_conv.columns = [str(col).strip() for col in df_conv.columns]

        # Cruzamento (Merge) usando as 3 chaves que definimos
        chaves_merge = ["BU", "Produto", "Emails Enviados"]
        
        # Selecionamos apenas as colunas necessárias da aba de conversão para não poluir
        colunas_conv = chaves_merge + ["CTA", "Formato", "Oportunidades"]
        # Filtramos apenas as colunas que realmente existem na aba de conversão para evitar erro
        colunas_existentes = [c for c in colunas_conv if c in df_conv.columns]
        
        df = pd.merge(df_perf, df_conv[colunas_existentes], on=chaves_merge, how="left")

        # Tratamento de tipos
        df["Hora de Início do Envio"] = pd.to_datetime(df["Hora de Início do Envio"], errors='coerce')
        df = df.dropna(subset=["Hora de Início do Envio"])
        df["Emails Enviados"] = pd.to_numeric(df["Emails Enviados"], errors='coerce').fillna(0)
        df["Oportunidades"] = pd.to_numeric(df.get("Oportunidades", 0), errors='coerce').fillna(0)
        
        # Limpeza de Taxas
        col_ab = "Taxa de Abertura"
        col_cl = "Taxa de Click Through Total"
        if col_ab in df.columns: df[col_ab] = df[col_ab].apply(limpar_porcentagem)
        if col_cl in df.columns: df[col_cl] = df[col_cl].apply(limpar_porcentagem)
        
        df = df.sort_values(by="Hora de Início do Envio")

    except Exception as e:
        st.error(f"Erro crítico ao processar os dados: {e}")
        st.stop()
else:
    st.info(f"👋 Arquivo '{NOME_ARQUIVO_PADRAO}' não encontrado no GitHub.")
    st.stop()

# --- INTERFACE E GRÁFICOS ---
if not df.empty:
    # Filtros Laterais
    st.sidebar.header("🎯 Filtros Dinâmicos")
    
    min_date = df["Hora de Início do Envio"].min().date()
    max_date = df["Hora de Início do Envio"].max().date()
    
    date_range = st.sidebar.date_input("1. Período (Início - Fim):", value=(min_date, max_date))
    bus_sel = st.sidebar.multiselect("2. Selecionar BU:", options=sorted(df["BU"].unique()), default=df["BU"].unique())

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
        # KPIs
        m1, m2, m3, m4 = st.columns(4)
        total_base = df_filtrado["Emails Enviados"].sum()
        total_opts = df_filtrado["Oportunidades"].sum()
        media_or = df_filtrado["Taxa de Abertura"].mean()
        taxa_conv = (total_opts / total_base * 100) if total_base > 0 else 0

        m1.metric("Base Total de Envio", f"{total_base:,.0f}".replace(",", "."))
        m2.metric("Oportunidades Geradas", f"{total_opts:,.0f}")
        m3.metric("Abertura Média (OR)", f"{media_or:.1f}%")
        m4.metric("Taxa de Conversão Final", f"{taxa_conv:.2f}%")

        # Gráficos de Conversão
        st.markdown("---")
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.subheader("🎯 Oportunidades por CTA")
            if "CTA" in df_filtrado.columns:
                df_cta = df_filtrado.groupby("CTA")["Oportunidades"].sum().reset_index().sort_values("Oportunidades")
                fig_cta = px.bar(df_cta, x="Oportunidades", y="CTA", orientation='h', color_discrete_sequence=['#00CC96'])
                st.plotly_chart(fig_cta, use_container_width=True)
            else:
                st.warning("Coluna 'CTA' não encontrada na aba de conversão.")

        with col_c2:
            st.subheader("📱 Conversão por Formato")
            if "Formato" in df_filtrado.columns:
                df_form = df_filtrado.groupby("Formato")["Oportunidades"].sum().reset_index()
                fig_form = px.pie(df_form, values="Oportunidades", names="Formato", hole=0.4)
                st.plotly_chart(fig_form, use_container_width=True)

        # Gráficos de Tendência (V1)
        st.markdown("---")
        st.subheader("📈 Tendência: Taxa de Abertura (OR)")
        fig_line = px.line(df_filtrado, x="Hora de Início do Envio", y="Taxa de Abertura", color="Produto", markers=True)
        st.plotly_chart(fig_line, use_container_width=True)

        with st.expander("📋 Ver Dados Cruzados"):
            st.dataframe(df_filtrado)
