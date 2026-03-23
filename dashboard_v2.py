import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da Página
st.set_page_config(page_title="CRM V2 - Performance & Leads", layout="wide")

# --- CONFIGURAÇÕES FIXAS ---
NOME_ARQUIVO_PADRAO = "Dados CRM 2026 - V3.xlsx"
META_ABERTURA, META_CTR, META_CTO = 22.0, 2.5, 12.0

st.title("🚀 Dashboard CRM V2: Geração de Leads e CTAs")

# --- FUNÇÕES DE LIMPEZA ---
def padronizar_texto(txt):
    t = str(txt).strip().lower()
    t = t.replace("porgram", "program") 
    return t

def limpar_numeros(valor):
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

        df_perf.columns = [str(col).strip() for col in df_perf.columns]
        df_conv.columns = [str(col).strip() for col in df_conv.columns]

        def achar_col_envio(df):
            for c in df.columns:
                if "emails env" in c.lower(): return c
            return "Emails Enviados"

        col_env_perf = achar_col_envio(df_perf)
        col_env_conv = achar_col_envio(df_conv)

        df_perf["_key_prod"] = df_perf["Produto"].apply(padronizar_texto)
        df_perf["_key_env"] = df_perf[col_env_perf].apply(limpar_numeros)
        df_conv["_key_prod"] = df_conv["Produto"].apply(padronizar_texto)
        df_conv["_key_env"] = df_conv[col_env_conv].apply(limpar_numeros)

        # Mapeando Oportunidades como Leads
        df_conv = df_conv.rename(columns={"Oportunidades": "Leads"})

        df = pd.merge(df_perf, df_conv[["_key_prod", "_key_env", "CTA", "Formato", "Leads"]], 
                      on=["_key_prod", "_key_env"], how="left")
        
        df["Leads"] = pd.to_numeric(df["Leads"], errors='coerce').fillna(0)
        df["Hora de Início do Envio"] = pd.to_datetime(df["Hora de Início do Envio"], errors='coerce')
        df = df.dropna(subset=["Hora de Início do Envio"])
        
        # Padronização de Taxas
        COL_AB, COL_CL = "Taxa de Abertura", "Taxa de Click Through Total"
        for col in [COL_AB, COL_CL]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace('%','').str.replace(',','.'), errors='coerce').fillna(0)
                df[col] = df[col].apply(lambda x: x*100 if x <= 1.0 and x > 0 else x)

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
        st.stop()

if 'df' in locals() and not df.empty:
    # --- FILTROS ---
    st.sidebar.header("🎯 Filtros")
    date_range = st.sidebar.date_input("Período:", value=(df["Hora de Início do Envio"].min(), df["Hora de Início do Envio"].max()))
    bus_sel = st.sidebar.multiselect("BU:", options=sorted(df["BU"].unique()), default=df["BU"].unique())
    df_temp = df[df["BU"].isin(bus_sel)]
    prods_sel = st.sidebar.multiselect("Produto:", options=sorted(df_temp["Produto"].unique()), default=df_temp["Produto"].unique())
    
    df_filtrado = df[(df["BU"].isin(bus_sel)) & (df["Produto"].isin(prods_sel)) & 
                     (df["Hora de Início do Envio"].dt.date >= date_range[0]) & 
                     (df["Hora de Início do Envio"].dt.date <= date_range[1])].copy()

    if not df_filtrado.empty:
        # --- 1. KPIs ---
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        t_base = df_filtrado[col_env_perf].sum()
        t_leads = df_filtrado["Leads"].sum()
        media_ab = df_filtrado[COL_AB].mean()
        media_cl = df_filtrado[COL_CL].mean()
        cto = (media_cl/media_ab*100 if media_ab>0 else 0)
        
        m1.metric("Base de Envio", f"{t_base:,.0f}".replace(",", "."))
        m2.metric("Leads Gerados", f"{t_leads:,.0f}")
        m3.metric("Abertura (OR)", f"{media_ab:.1f}%", delta=f"{media_ab-META_ABERTURA:.1f}% vs Mercado")
        m4.metric("Clique (CTR)", f"{media_cl:.1f}%", delta=f"{media_cl-META_CTR:.1f}% vs Mercado")
        m5.metric("Eficiência (CTO)", f"{cto:.1f}%")
        m6.metric("Conv. Leads", f"{(t_leads/t_base*100 if t_base > 0 else 0):.2f}%")

        # --- 2. ANÁLISE DO ESPECIALISTA E RECORDISTAS ---
        st.markdown("---")
        col_an1, col_an2 = st.columns([1.6, 1.4])

        recordista_or = df_filtrado.loc[df_filtrado[COL_AB].idxmax()]
        recordista_ctr = df_filtrado.loc[df_filtrado[COL_CL].idxmax()]
        recordista_lead = df_filtrado.loc[df_filtrado["Leads"].idxmax()] if t_leads > 0 else recordista_or

        with col_an1:
            st.subheader("🕵️ Análise do Especialista")
            st.info(f"""
            **Insight sobre Assuntos (OR):** O assunto campeão de curiosidade foi **"{recordista_or['Assunto']}"** ({recordista_or[COL_AB]:.1f}%). 

            **Insight sobre CTAs (Leads):** O CTA **"{recordista_lead['CTA']}"** provou ser o mais eficiente, 
            gerando {recordista_lead['Leads']:.0f} leads para o produto **{recordista_lead['Produto']}**. 

            **Diagnóstico Geral:** Sua eficiência (CTO) de **{cto:.1f}%** é de elite. Isso indica que a base é altamente responsiva ao conteúdo interno dos e-mails.
            """)

        with col_an2:
            st.subheader("🏆 Recordistas do Filtro")
            
            # Card Melhor Abertura
            st.success(f"""
            🔥 **Melhor Abertura (OR): {recordista_or[COL_AB]:.1f}%**  
            **Data:** {recordista_or['Hora de Início do Envio'].strftime('%d/%m/%Y')}  
            **Produto:** {recordista_or['Produto']}  
            **Base de Envio:** {recordista_or[col_env_perf]:,.0f} pessoas  
            **Assunto:** *{recordista_or['Assunto']}*
            """)

            # Card Maior Geração de Leads
            st.warning(f"""
            💰 **Maior Geração de Leads: {recordista_lead['Leads']:.0f} Leads**  
            **Data:** {recordista_lead['Hora de Início do Envio'].strftime('%d/%m/%Y')}  
            **Produto:** {recordista_lead['Produto']}  
            **Base de Envio:** {recordista_lead[col_env_perf]:,.0f} pessoas  
            **CTA:** *{recordista_lead['CTA']}*
            """)

        # --- 3. CONVERSÃO ---
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🎯 Leads por CTA")
            df_cta = df_filtrado[df_filtrado["Leads"] > 0].groupby("CTA")["Leads"].sum().reset_index().sort_values("Leads")
            if not df_cta.empty: st.plotly_chart(px.bar(df_cta, x="Leads", y="CTA", orientation='h', color_discrete_sequence=['#00CC96']), use_container_width=True)
            else: st.info("Sem leads registrados no filtro.")
        with c2:
            st.subheader("📱 Leads por Formato")
            df_f = df_filtrado[df_filtrado["Leads"] > 0].groupby("Formato")["Leads"].sum().reset_index()
            if not df_f.empty: st.plotly_chart(px.pie(df_f, values="Leads", names="Formato", hole=0.4), use_container_width=True)

        # --- 4. GRÁFICOS DE TENDÊNCIA ---
        st.markdown("---")
        fig_or = px.line(df_filtrado, x="Hora de Início do Envio", y=COL_AB, color="Produto", markers=True,
                         labels={"Hora de Início do Envio": "Data", COL_AB: "Taxa de Abertura (OR)"},
                         title="📈 Tendência: Taxa de Abertura (OR)")
        fig_or.update_traces(hovertemplate="<b>Produto:</b> %{fullData.name}<br><b>Data:</b> %{x}<br><b>Base de Envio:</b> %{customdata[1]:,.0f}<br><b>Abertura:</b> %{y:.1f}%<extra></extra>",
                             customdata=df_filtrado[["Assunto", col_env_perf]])
        st.plotly_chart(fig_or, use_container_width=True)

        st.markdown("---")
        fig_ctr = px.line(df_filtrado, x="Hora de Início do Envio", y=COL_CL, color="Produto", markers=True,
                          labels={"Hora de Início do Envio": "Data", COL_CL: "Taxa de Clique"},
                          title="📈 Tendência: Taxa de Clique (CTR)")
        fig_ctr.update_traces(hovertemplate="<b>Produto:</b> %{fullData.name}<br><b>Data:</b> %{x}<br><b>Base de Envio:</b> %{customdata[1]:,.0f}<br><b>Clique:</b> %{y:.1f}%<extra></extra>",
                              customdata=df_filtrado[["Assunto", col_env_perf]])
        st.plotly_chart(fig_ctr, use_container_width=True)

    else:
        st.warning("Selecione os filtros.")
