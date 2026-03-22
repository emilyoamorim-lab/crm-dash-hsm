import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re
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

# --- FUNÇÕES DE LIMPEZA PESADA ---
def limpar_valor_numerico(valor):
    """Remove pontos de milhar, espaços e converte para inteiro puro"""
    if pd.isna(valor): return 0
    # Converte para string e remove tudo que não for número
    s = re.sub(r'\D', '', str(valor))
    try:
        return int(s)
    except:
        return 0

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
        df_perf = excel.parse(0) 
        df_conv = excel.parse(1) 

        # 1. Padronização de Colunas
        df_perf.columns = [str(col).strip() for col in df_perf.columns]
        df_conv.columns = [str(col).strip() for col in df_conv.columns]

        # 2. CRIAÇÃO DE CHAVES DE CRUZAMENTO BLINDADAS
        # Limpamos BU, Produto e Emails Enviados em ambas as tabelas
        for d in [df_perf, df_conv]:
            d["BU_key"] = d["BU"].astype(str).str.strip().str.lower()
            d["Prod_key"] = d["Produto"].astype(str).str.strip().str.lower()
            # A mágica aqui: remove pontos de milhar que o Excel às vezes coloca
            d["Env_key"] = d["Emails Enviados"].apply(limpar_valor_numerico)

        # 3. MERGE (Cruzamento)
        chaves_merge = ["BU_key", "Prod_key", "Env_key"]
        
        # Selecionamos as colunas de resultado da aba de conversão
        cols_resultado = [c for c in ["CTA", "Formato", "Oportunidades"] if c in df_conv.columns]
        
        # Cruzamos as tabelas
        df = pd.merge(df_perf, df_conv[chaves_merge + cols_resultado], 
                      on=chaves_merge, how="left")

        # Limpeza pós-cruzamento
        df = df.drop(columns=["BU_key", "Prod_key", "Env_key"])
        df["Oportunidades"] = pd.to_numeric(df["Oportunidades"], errors='coerce').fillna(0)
        df["CTA"] = df["CTA"].fillna("Não Mapeado")
        df["Formato"] = df["Formato"].fillna("Não Mapeado")
        
        # Tratamento de Datas e Taxas
        df["Hora de Início do Envio"] = pd.to_datetime(df["Hora de Início do Envio"], errors='coerce')
        df = df.dropna(subset=["Hora de Início do Envio"])
        df["Emails Enviados"] = pd.to_numeric(df["Emails Enviados"], errors='coerce').fillna(0)
        
        COL_ABERTURA = "Taxa de Abertura"
        COL_CLIQUE = "Taxa de Click Through Total"
        df[COL_ABERTURA] = df[COL_ABERTURA].apply(limpar_porcentagem)
        df[COL_CLIQUE] = df[COL_CLIQUE].apply(limpar_porcentagem)

    except Exception as e:
        st.error(f"Erro ao processar as bases: {e}")
        st.stop()

if 'df' in locals() and not df.empty:
    # --- FILTROS ---
    st.sidebar.header("🎯 Filtros de Busca")
    
    # Datas
    min_date = df["Hora de Início do Envio"].min().date()
    max_date = df["Hora de Início do Envio"].max().date()
    date_range = st.sidebar.date_input("1. Período:", value=(min_date, max_date))

    # BU e Produto
    bus_sel = st.sidebar.multiselect("2. Selecionar BU:", options=sorted(df["BU"].unique()), default=df["BU"].unique())
    df_temp = df[df["BU"].isin(bus_sel)]
    prods_sel = st.sidebar.multiselect("3. Selecionar Produto:", options=sorted(df_temp["Produto"].unique()), default=df_temp["Produto"].unique())

    # Aplicação final do filtro
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
        # --- KPIs ---
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

        # --- ANÁLISE E RECORDISTAS ---
        st.markdown("---")
        col_an1, col_an2 = st.columns([1.8, 1.2])

        recordista_or = df_filtrado.loc[df_filtrado[COL_ABERTURA].idxmax()]
        # Recordista de Oportunidades
        if total_opts > 0:
            recordista_opt = df_filtrado.loc[df_filtrado["Oportunidades"].idxmax()]
            cta_venc = recordista_opt['CTA']
            val_opt = recordista_opt['Oportunidades']
        else:
            recordista_opt = recordista_or
            cta_venc = "Sem conversão no filtro"
            val_opt = 0

        with col_an1:
            st.subheader("🕵️ Análise do Especialista")
            st.info(f"""
            **Diagnóstico: {recordista_or['Produto']}**
            O melhor engajamento de abertura foi em **{recordista_or['Hora de Início do Envio'].strftime('%d/%m')}**.
            
            **Conversão de Negócio:** Atualmente, o produto **{recordista_opt['Produto']}** é o líder de fundo de funil, gerando **{val_opt:.0f} oportunidades**. 
            O CTA mais eficiente identificado é o: **"{cta_venc}"**.
            """)

        with col_an2:
            st.subheader("🏆 Recordistas")
            st.success(f"🔥 **Melhor OR:** {recordista_or[COL_ABERTURA]:.1f}%")
            st.warning(f"💰 **Mais Oportunidades:** {val_opt:.0f} Opts\n\n**CTA:** {cta_venc}")

        # --- GRÁFICOS ---
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🎯 Oportunidades por CTA")
            df_cta = df_filtrado[df_filtrado["CTA"] != "Não Mapeado"].groupby("CTA")["Oportunidades"].sum().reset_index().sort_values("Oportunidades")
            if not df_cta.empty:
                fig_cta = px.bar(df_cta, x="Oportunidades", y="CTA", orientation='h', color_discrete_sequence=['#00CC96'])
                st.plotly_chart(fig_cta, use_container_width=True)
            else: st.info("Nenhuma oportunidade mapeada para este filtro.")
        with c2:
            st.subheader("📱 Conversão por Formato")
            df_form = df_filtrado[df_filtrado["Formato"] != "Não Mapeado"].groupby("Formato")["Oportunidades"].sum().reset_index()
            if not df_form.empty:
                fig_form = px.pie(df_form, values="Oportunidades", names="Formato", hole=0.4)
                st.plotly_chart(fig_form, use_container_width=True)
            else: st.info("Nenhum formato mapeado.")

        with st.expander("📋 Ver Depuração de Dados (Cruzamento)"):
            st.write("Abaixo você vê como o sistema cruzou as tabelas. Verifique se a coluna Oportunidades está preenchida:")
            st.dataframe(df_filtrado[["Hora de Início do Envio", "Produto", "Emails Enviados", "CTA", "Oportunidades"]])
    else:
        st.warning("Selecione filtros válidos.")
else:
    st.info("👋 Suba o arquivo 'Dados CRM 2026 - V3.xlsx' para ativar.")
