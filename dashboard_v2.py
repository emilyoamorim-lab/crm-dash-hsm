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
def limpar_numeros_chave(valor):
    """Garante que o número seja um inteiro puro, tratando decimais e strings"""
    try:
        if pd.isna(valor): return 0
        # Converte para float primeiro para lidar com '3713.0' e depois para int
        num = float(str(valor).replace('.', '').replace(',', '').strip())
        # Se o número for muito pequeno (ex: 3.713), o Excel pode ter lido como float
        if num < 100 and "." in str(valor): 
            num = float(str(valor).replace(',', '.')) * 1000
        return int(num)
    except:
        return 0

def limpar_porcentagem(valor):
    if pd.isna(valor): return 0.0
    if isinstance(valor, str):
        valor = valor.replace('%', '').replace(',', '.')
        try: return float(valor)
        except: return 0.0
    return float(valor) * 100 if valor <= 1.0 else float(valor)

# --- CARREGAMENTO ---
if os.path.exists(NOME_ARQUIVO_PADRAO):
    try:
        excel = pd.ExcelFile(NOME_ARQUIVO_PADRAO)
        df_perf = excel.parse(0) 
        df_conv = excel.parse(1) 

        df_perf.columns = [str(col).strip() for col in df_perf.columns]
        df_conv.columns = [str(col).strip() for col in df_conv.columns]

        # Criando chaves de cruzamento idênticas
        for d in [df_perf, df_conv]:
            d["_join_bu"] = d["BU"].astype(str).str.strip().str.lower()
            d["_join_prod"] = d["Produto"].astype(str).str.strip().str.lower()
            d["_join_env"] = d["Emails Enviados"].apply(limpar_numeros_chave)

        # Merge
        chaves = ["_join_bu", "_join_prod", "_join_env"]
        df = pd.merge(df_perf, df_conv[chaves + ["CTA", "Formato", "Oportunidades"]], on=chaves, how="left")
        
        # Limpando e formatando
        df["Oportunidades"] = pd.to_numeric(df["Oportunidades"], errors='coerce').fillna(0)
        df["Hora de Início do Envio"] = pd.to_datetime(df["Hora de Início do Envio"], errors='coerce')
        df = df.dropna(subset=["Hora de Início do Envio"])
        
        COL_AB, COL_CL = "Taxa de Abertura", "Taxa de Click Through Total"
        df[COL_AB] = df[COL_AB].apply(limpar_porcentagem)
        df[COL_CL] = df[COL_CL].apply(limpar_porcentagem)

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

    if isinstance(date_range, tuple) and len(date_range) == 2:
        df_filtrado = df[(df["Hora de Início do Envio"].dt.date >= date_range[0]) & 
                         (df["Hora de Início do Envio"].dt.date <= date_range[1]) &
                         (df["BU"].isin(bus_sel)) & (df["Produto"].isin(prods_sel))].copy()
    else:
        df_filtrado = df[(df["BU"].isin(bus_sel)) & (df["Produto"].isin(prods_sel))].copy()

    if not df_filtrado.empty:
        # KPIs
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        media_ab = df_filtrado[COL_AB].mean()
        media_cl = df_filtrado[COL_CL].mean()
        cto = (media_cl / media_ab * 100) if media_ab > 0 else 0
        t_opts = df_filtrado["Oportunidades"].sum()
        
        m1.metric("Base de Envio", f"{df_filtrado['Emails Enviados'].sum():,.0f}".replace(",", "."))
        m2.metric("Oportunidades", f"{t_opts:,.0f}")
        m3.metric("Abertura (OR)", f"{media_ab:.1f}%", delta=f"{media_ab-META_ABERTURA:.1f}%")
        m4.metric("Clique (CTR)", f"{media_cl:.1f}%", delta=f"{media_cl-META_CTR:.1f}%")
        m5.metric("Eficiência (CTO)", f"{cto:.1f}%", delta=f"{cto-META_CTO:.1f}%")
        m6.metric("Conv. Final", f"{(t_opts/df_filtrado['Emails Enviados'].sum()*100):.2f}%")

        # Análise e Recordistas
        st.markdown("---")
        c_a1, c_a2 = st.columns([1.8, 1.2])
        rec_or = df_filtrado.loc[df_filtrado[COL_AB].idxmax()]
        rec_opt = df_filtrado.loc[df_filtrado["Oportunidades"].idxmax()] if t_opts > 0 else rec_or

        with c_a1:
            st.subheader("🕵️ Análise do Especialista")
            st.info(f"**Destaque: {rec_or['Produto']}** em {rec_or['Hora de Início do Envio'].strftime('%d/%m')}. "
                    f"O produto com mais oportunidades foi **{rec_opt['Produto']}** ({rec_opt['Oportunidades']:.0f} opts) via CTA: '{rec_opt.get('CTA','-')}'")

        with c_a2:
            st.subheader("🏆 Recordistas")
            st.success(f"🔥 **OR:** {rec_or[COL_AB]:.1f}%")
            st.warning(f"💰 **Opts:** {rec_opt['Oportunidades']:.0f} | CTA: {rec_opt.get('CTA','-')}")

        # Gráficos de Conversão
        st.markdown("---")
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("🎯 Oportunidades por CTA")
            df_cta = df_filtrado[df_filtrado["Oportunidades"] > 0].groupby("CTA")["Oportunidades"].sum().reset_index().sort_values("Oportunidades")
            if not df_cta.empty: st.plotly_chart(px.bar(df_cta, x="Oportunidades", y="CTA", orientation='h', color_discrete_sequence=['#00CC96']), use_container_width=True)
            else: st.info("Nenhuma oportunidade para os filtros selecionados.")
        with g2:
            st.subheader("📱 Conversão por Formato")
            df_f = df_filtrado[df_filtrado["Oportunidades"] > 0].groupby("Formato")["Oportunidades"].sum().reset_index()
            if not df_f.empty: st.plotly_chart(px.pie(df_f, values="Oportunidades", names="Formato", hole=0.4), use_container_width=True)
            else: st.info("Nenhum formato convertido.")

        # Gráficos de Tendência (Restauração da V1)
        st.markdown("---")
        st.subheader("📈 Tendência: Taxa de Abertura (OR)")
        st.plotly_chart(px.line(df_filtrado, x="Hora de Início do Envio", y=COL_AB, color="Produto", markers=True, labels={"Hora de Início do Envio":"Data"}), use_container_width=True)
        
        st.markdown("---")
        st.subheader("📈 Tendência: Taxa de Clique (CTR)")
        st.plotly_chart(px.line(df_filtrado, x="Hora de Início do Envio", y=COL_CL, color="Produto", markers=True, labels={"Hora de Início do Envio":"Data", COL_CL:"Taxa de Clique"}), use_container_width=True)

        with st.expander("📋 Ver Depuração de Dados (Cruzamento)"):
            st.write("Verifique se as colunas CTA e Oportunidades estão preenchidas para o T16:")
            st.dataframe(df_filtrado[["Hora de Início do Envio", "Produto", "Emails Enviados", "CTA", "Oportunidades"]])
