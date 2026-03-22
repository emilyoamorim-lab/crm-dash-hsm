import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da Página
st.set_page_config(page_title="CRM V2 - Performance & Conversão", layout="wide")

# --- CONFIGURAÇÕES FIXAS ---
NOME_ARQUIVO_PADRAO = "Dados CRM 2026 - V3.xlsx"
META_ABERTURA, META_CTR, META_CTO = 22.0, 2.5, 12.0

st.title("🚀 Dashboard CRM V2: Conversão e CTAs")

# --- FUNÇÕES DE LIMPEZA ---
def padronizar_texto(txt):
    """Remove espaços, corrige erros comuns e padroniza para busca"""
    t = str(txt).strip().lower()
    t = t.replace("porgram", "program") # Correção automática para o erro detectado
    return t

def limpar_numeros(valor):
    """Garante que o número seja um inteiro puro"""
    try:
        if pd.isna(valor): return 0
        num = float(str(valor).replace('.', '').replace(',', '').strip())
        return int(num)
    except: return 0

# --- CARREGAMENTO ---
if os.path.exists(NOME_ARQUIVO_PADRAO):
    try:
        excel = pd.ExcelFile(NOME_ARQUIVO_PADRAO)
        df_perf = excel.parse(0) 
        df_conv = excel.parse(1) 

        # Padronizar nomes de colunas (Remove espaços)
        df_perf.columns = [str(col).strip() for col in df_perf.columns]
        df_conv.columns = [str(col).strip() for col in df_conv.columns]

        # Mapeamento da coluna de Envios (Pode ser 'Emails Env' ou 'Emails Enviados')
        def achar_col_envio(df):
            for c in df.columns:
                if "emails env" in c.lower(): return c
            return None

        col_env_perf = achar_col_envio(df_perf)
        col_env_conv = achar_col_envio(df_conv)

        # Preparação das Chaves de Cruzamento
        df_perf["_key_prod"] = df_perf["Produto"].apply(padronizar_texto)
        df_perf["_key_env"] = df_perf[col_env_perf].apply(limpar_numeros)
        
        df_conv["_key_prod"] = df_conv["Produto"].apply(padronizar_texto)
        df_conv["_key_env"] = df_conv[col_env_conv].apply(limpar_numeros)

        # Cruzamento
        df = pd.merge(df_perf, df_conv[["_key_prod", "_key_env", "CTA", "Formato", "Oportunidades"]], 
                      on=["_key_prod", "_key_env"], how="left")
        
        # Tratamento Final
        df["Oportunidades"] = pd.to_numeric(df["Oportunidades"], errors='coerce').fillna(0)
        df["Hora de Início do Envio"] = pd.to_datetime(df["Hora de Início do Envio"], errors='coerce')
        df = df.dropna(subset=["Hora de Início do Envio"])
        
        # Ajuste de Taxas
        for col in ["Taxa de Abertura", "Taxa de Click Through Total"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace('%','').str.replace(',','.'), errors='coerce').fillna(0)
                df[col] = df[col].apply(lambda x: x*100 if x <= 1.0 and x > 0 else x)

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
        st.stop()

if 'df' in locals() and not df.empty:
    # --- FILTROS ---
    st.sidebar.header("🎯 Filtros")
    bus_sel = st.sidebar.multiselect("BU:", options=sorted(df["BU"].unique()), default=df["BU"].unique())
    df_temp = df[df["BU"].isin(bus_sel)]
    prods_sel = st.sidebar.multiselect("Produto:", options=sorted(df_temp["Produto"].unique()), default=df_temp["Produto"].unique())
    
    df_filtrado = df[(df["BU"].isin(bus_sel)) & (df["Produto"].isin(prods_sel))].copy()

    if not df_filtrado.empty:
        # KPIs
        m1, m2, m3, m4, m5 = st.columns(5)
        t_base = df_filtrado[col_env_perf].sum()
        t_opts = df_filtrado["Oportunidades"].sum()
        media_ab = df_filtrado["Taxa de Abertura"].mean()
        media_cl = df_filtrado["Taxa de Click Through Total"].mean()
        
        m1.metric("Base de Envio", f"{t_base:,.0f}".replace(",", "."))
        m2.metric("Oportunidades", f"{t_opts:,.0f}")
        m3.metric("Abertura (OR)", f"{media_ab:.1f}%")
        m4.metric("Clique (CTR)", f"{media_cl:.1f}%")
        m5.metric("Eficiência (CTO)", f"{(media_cl/media_ab*100 if media_ab>0 else 0):.1f}%")

        # Gráficos de Conversão
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🎯 Oportunidades por CTA")
            df_cta = df_filtrado[df_filtrado["Oportunidades"] > 0].groupby("CTA")["Oportunidades"].sum().reset_index().sort_values("Oportunidades")
            if not df_cta.empty: st.plotly_chart(px.bar(df_cta, x="Oportunidades", y="CTA", orientation='h', color_discrete_sequence=['#00CC96']), use_container_width=True)
            else: st.info("Sem oportunidades para este filtro.")
        with c2:
            st.subheader("📱 Conversão por Formato")
            df_f = df_filtrado[df_filtrado["Oportunidades"] > 0].groupby("Formato")["Oportunidades"].sum().reset_index()
            if not df_f.empty: st.plotly_chart(px.pie(df_f, values="Oportunidades", names="Formato", hole=0.4), use_container_width=True)

        # Tendência
        st.markdown("---")
        st.subheader("📈 Tendência: Taxa de Abertura (OR)")
        st.plotly_chart(px.line(df_filtrado, x="Hora de Início do Envio", y="Taxa de Abertura", color="Produto", markers=True), use_container_width=True)

        with st.expander("📋 Ver Tabela de Auditoria (Cruzamento)"):
            st.write("Verifique se as colunas CTA e Oportunidades estão preenchidas:")
            st.dataframe(df_filtrado[["Hora de Início do Envio", "Produto", col_env_perf, "CTA", "Oportunidades"]])
    else:
        st.warning("Selecione os filtros.")
