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
def limpar_texto(txt):
    """Limpa textos para garantir o cruzamento (lowercase e sem espaços)"""
    return str(txt).strip().lower()

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

        # Limpeza de nomes de colunas
        df_perf.columns = [str(col).strip() for col in df_perf.columns]
        df_conv.columns = [str(col).strip() for col in df_conv.columns]

        # PREPARAÇÃO PARA O CRUZAMENTO FLEXÍVEL
        # Criamos chaves baseadas apenas em BU e Produto (limpos)
        df_perf["_chave_bu"] = df_perf["BU"].apply(limpar_texto)
        df_perf["_chave_prod"] = df_perf["Produto"].apply(limpar_texto)
        
        df_conv["_chave_bu"] = df_conv["BU"].apply(limpar_texto)
        df_conv["_chave_prod"] = df_conv["Produto"].apply(limpar_texto)

        # Na aba de conversão, vamos agrupar por BU e Produto para pegar o total de oportunidades
        # Isso resolve o problema de o volume de e-mails ser diferente entre as abas
        df_conv_agrupado = df_conv.groupby(["_chave_bu", "_chave_prod"]).agg({
            'Oportunidades': 'sum',
            'CTA': 'first',
            'Formato': 'first'
        }).reset_index()

        # Merge Flexível (Por BU e Produto)
        df = pd.merge(df_perf, df_conv_agrupado, on=["_chave_bu", "_chave_prod"], how="left")
        
        # Tratamento de dados finais
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

    # Filtro de Data
    df_filtrado = df[
        (df["Hora de Início do Envio"].dt.date >= date_range[0]) & 
        (df["Hora de Início do Envio"].dt.date <= date_range[1]) &
        (df["BU"].isin(bus_sel)) & 
        (df["Produto"].isin(prods_sel))
    ].copy()

    if not df_filtrado.empty:
        # KPIs
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        total_base = df_filtrado['Emails Enviados'].sum()
        total_opts = df_filtrado["Oportunidades"].sum()
        media_ab = df_filtrado[COL_AB].mean()
        media_cl = df_filtrado[COL_CL].mean()
        cto = (media_cl / media_ab * 100) if media_ab > 0 else 0
        
        m1.metric("Base de Envio", f"{total_base:,.0f}".replace(",", "."))
        m2.metric("Oportunidades", f"{total_opts:,.0f}")
        m3.metric("Abertura (OR)", f"{media_ab:.1f}%", delta=f"{media_ab-META_ABERTURA:.1f}%")
        m4.metric("Clique (CTR)", f"{media_cl:.1f}%", delta=f"{media_cl-META_CTR:.1f}%")
        m5.metric("Eficiência (CTO)", f"{cto:.1f}%", delta=f"{cto-META_CTO:.1f}%")
        m6.metric("Conv. Final", f"{(total_opts/total_base*100 if total_base > 0 else 0):.2f}%")

        # Análise do Especialista
        st.markdown("---")
        col_an1, col_an2 = st.columns([1.8, 1.2])
        rec_or = df_filtrado.loc[df_filtrado[COL_AB].idxmax()]
        rec_opt = df_filtrado.loc[df_filtrado["Oportunidades"].idxmax()] if total_opts > 0 else rec_or

        with col_an1:
            st.subheader("🕵️ Análise do Especialista")
            st.info(f"**Destaque: {rec_or['Produto']}**. O produto com mais oportunidades acumuladas no filtro é **{rec_opt['Produto']}** com **{total_opts:.0f}** oportunidades totais.")

        with col_an2:
            st.subheader("🏆 Recordistas")
            st.success(f"🔥 **OR:** {rec_or[COL_AB]:.1f}%")
            st.warning(f"💰 **Opts (Filtro):** {total_opts:.0f}")

        # Gráficos de Conversão
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🎯 Oportunidades por CTA")
            df_cta = df_filtrado.groupby("CTA")["Oportunidades"].sum().reset_index().sort_values("Oportunidades")
            df_cta = df_cta[df_cta["Oportunidades"] > 0]
            if not df_cta.empty:
                st.plotly_chart(px.bar(df_cta, x="Oportunidades", y="CTA", orientation='h', color_discrete_sequence=['#00CC96']), use_container_width=True)
            else: st.info("Nenhuma oportunidade para o produto/período.")
        with c2:
            st.subheader("📱 Conversão por Formato")
            df_form = df_filtrado.groupby("Formato")["Oportunidades"].sum().reset_index()
            df_form = df_form[df_form["Oportunidades"] > 0]
            if not df_form.empty:
                st.plotly_chart(px.pie(df_form, values="Oportunidades", names="Formato", hole=0.4), use_container_width=True)
            else: st.info("Nenhum formato convertido.")

        # Gráficos de Tendência
        st.markdown("---")
        st.subheader("📈 Tendência: Taxa de Abertura (OR)")
        st.plotly_chart(px.line(df_filtrado, x="Hora de Início do Envio", y=COL_AB, color="Produto", markers=True), use_container_width=True)
        
        st.subheader("📈 Tendência: Taxa de Clique (CTR)")
        st.plotly_chart(px.line(df_filtrado, x="Hora de Início do Envio", y=COL_CL, color="Produto", markers=True), use_container_width=True)

        with st.expander("📋 Depuração: Por que os dados não cruzam?"):
            st.write("Dados da Aba 1 (Performance):")
            st.dataframe(df_perf[["BU", "Produto", "Emails Enviados"]].head(10))
            st.write("Dados da Aba 2 (Conversão):")
            st.dataframe(df_conv[["BU", "Produto", "Oportunidades"]].head(10))
    else:
        st.warning("Selecione filtros válidos.")
else:
    st.info("👋 Suba o arquivo 'Dados CRM 2026 - V3.xlsx' para ativar.")
