import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da Página
st.set_page_config(page_title="CRM Performance - HSM & Singularity", layout="wide")

# --- CONFIGURAÇÕES FIXAS ---
NOME_ARQUIVO_PADRAO = "Dados CRM 2026 - V2.xlsx"
COL_BU = "BU"
COL_PRODUTO = "Produto"
COL_ASSUNTO = "Assunto"
COL_DATA = "Hora de Início do Envio"
COL_ENVIADO = "Emails Enviados"
COL_ABERTURA = "Taxa de Abertura"
COL_CLIQUE = "Taxa de Click Through Total"

# Benchmarks Mercado Educação Corporativa
META_ABERTURA = 22.0
META_CTR = 2.5
META_CTO = 12.0

st.title("📊 Dashboard de Performance CRM")

# --- FUNÇÃO DE LIMPEZA ---
def limpar_porcentagem(valor):
    if pd.isna(valor): return 0.0
    if isinstance(valor, str):
        valor = valor.replace('%', '').replace(',', '.')
        try: return float(valor)
        except: return 0.0
    return float(valor) * 100 if valor <= 1.0 else float(valor)

# --- CARREGAMENTO ---
df = None
if os.path.exists(NOME_ARQUIVO_PADRAO):
    try:
        df = pd.read_excel(NOME_ARQUIVO_PADRAO)
        df.columns = [str(col).strip() for col in df.columns]
        df[COL_DATA] = pd.to_datetime(df[COL_DATA], errors='coerce')
        df = df.dropna(subset=[COL_DATA])
        df[COL_ENVIADO] = pd.to_numeric(df[COL_ENVIADO], errors='coerce').fillna(0)
        df[COL_ABERTURA] = df[COL_ABERTURA].apply(limpar_porcentagem)
        df[COL_CLIQUE] = df[COL_CLIQUE].apply(limpar_porcentagem)
        df['Mês_Ref'] = df[COL_DATA].dt.strftime('%m - %B %Y')
        df = df.sort_values(by=COL_DATA)
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")

if df is not None:
    # --- FILTROS ---
    st.sidebar.header("🎯 Filtros de Busca")
    meses_disponiveis = sorted(df['Mês_Ref'].unique().tolist())
    meses_sel = st.sidebar.multiselect("1. Selecionar Período:", options=meses_disponiveis, default=meses_disponiveis)
    bus_disponiveis = sorted(df[COL_BU].unique().tolist())
    bus_sel = st.sidebar.multiselect("2. Selecionar BU:", options=bus_disponiveis, default=bus_disponiveis)
    df_temp = df[df[COL_BU].isin(bus_sel)]
    produtos_disponiveis = sorted(df_temp[COL_PRODUTO].unique().tolist())
    produtos_sel = st.sidebar.multiselect("3. Selecionar Produto:", options=produtos_disponiveis, default=produtos_disponiveis)

    df_filtrado = df[
        (df['Mês_Ref'].isin(meses_sel)) & 
        (df[COL_BU].isin(bus_sel)) & 
        (df[COL_PRODUTO].isin(produtos_sel))
    ].copy()

    if not df_filtrado.empty:
        # --- KPIs NO TOPO ---
        m1, m2, m3, m4 = st.columns(4)
        total_base = df_filtrado[COL_ENVIADO].sum()
        media_ab = df_filtrado[COL_ABERTURA].mean()
        media_cl = df_filtrado[COL_CLIQUE].mean()
        cto_medio = (media_cl / media_ab * 100) if media_ab > 0 else 0
        
        m1.metric("Base Total Impactada", f"{total_base:,.0f}".replace(",", "."))
        m2.metric("Abertura Média", f"{media_ab:.1f}%", delta=f"{media_ab - META_ABERTURA:.1f}% vs Mercado")
        m3.metric("Clique Médio (CTR)", f"{media_cl:.1f}%", delta=f"{media_cl - META_CTR:.1f}% vs Mercado")
        m4.metric("Eficiência (CTO)", f"{cto_medio:.1f}%", delta=f"{cto_medio - META_CTO:.1f}% vs Mercado")

        # --- GRÁFICOS EM DUAS COLUNAS ---
        st.markdown("---")
        col_gr1, col_gr2 = st.columns(2)

        with col_gr1:
            st.subheader("📈 Tendência: Abertura")
            fig_abert = px.line(df_filtrado, x=COL_DATA, y=COL_ABERTURA, color=COL_PRODUTO, markers=True)
            fig_abert.update_traces(
                hovertemplate="<b>Produto:</b> %{fullData.name}<br><b>Data:</b> %{x}<br><b>Base:</b> %{customdata[1]:,.0f}<br><b>Abertura:</b> %{y:.1f}%<extra></extra>",
                customdata=df_filtrado[[COL_ASSUNTO, COL_ENVIADO]]
            )
            st.plotly_chart(fig_abert, use_container_width=True)

        with col_gr2:
            st.subheader("📈 Tendência: Clique (CTR)")
            fig_clique = px.line(df_filtrado, x=COL_DATA, y=COL_CLIQUE, color=COL_PRODUTO, markers=True)
            # Definindo cor diferente para o gráfico de clique se quiser (opcional) ou manter a cor do produto
            fig_clique.update_traces(
                hovertemplate="<b>Produto:</b> %{fullData.name}<br><b>Data:</b> %{x}<br><b>Base:</b> %{customdata[1]:,.0f}<br><b>Clique:</b> %{y:.1f}%<extra></extra>",
                customdata=df_filtrado[[COL_ASSUNTO, COL_ENVIADO]]
            )
            st.plotly_chart(fig_clique, use_container_width=True)

        # --- ANÁLISE E RESUMO ---
        st.markdown("---")
        col_an1, col_an2 = st.columns([1.8, 1.2])

        recordista_ab = df_filtrado.loc[df_filtrado[COL_ABERTURA].idxmax()]
        recordista_cl = df_filtrado.loc[df_filtrado[COL_CLIQUE].idxmax()]

        with col_an1:
            st.subheader("🕵️ Análise do Especialista")
            if len(produtos_sel) >= 1:
                media_volume = df_filtrado[COL_ENVIADO].mean()
                tipo_sucesso = "Escala/Geral" if recordista_ab[COL_ENVIADO] > media_volume else "Nicho/Segmentado"
                status_cto = "Elite" if cto_medio > 40 else "Saudável"
                
                st.info(f"""
                **Diagnóstico de Performance: {recordista_ab[COL_PRODUTO]}**
                
                O recorde de abertura foi de **{recordista_ab[COL_ABERTURA]:.1f}%** (Base: **{recordista_ab[COL_ENVIADO]:,.0f}**).
                
                **Eficiência de Conteúdo (CTO):** Sua taxa interna está em **{cto_medio:.1f}%**. Isso é performance de **{status_cto}** (Mercado Ed. Corp: {META_CTO}%). 
                O público está altamente engajado com o conteúdo após a abertura.
                
                **Insight de Clique:** O melhor clique atingiu **{recordista_cl[COL_CLIQUE]:.1f}%** em uma base de **{recordista_cl[COL_ENVIADO]:,.0f}**. 
                {"O foco em segmentação está trazendo resultados superiores no clique." if recordista_cl[COL_ENVIADO] < media_volume else "A oferta tem tração massiva em bases de grande escala."}
                """)
            else:
                st.write("Selecione um produto para análise detalhada.")

        with col_an2:
            st.subheader("🏆 Recordistas do Filtro")
            
            st.success(f"""
            🔥 **Melhor Abertura: {recordista_ab[COL_ABERTURA]:.1f}%**  
            **Data:** {recordista_ab[COL_DATA].strftime('%d/%m/%Y')} | **Base:** {recordista_ab[COL_ENVIADO]:,.0f}  
            **Assunto:** *{recordista_ab[COL_ASSUNTO]}*
            """)

            st.info(f"""
            🚀 **Melhor Clique: {recordista_cl[COL_CLIQUE]:.1f}%**  
            **Data:** {recordista_cl[COL_DATA].strftime('%d/%m/%Y')} | **Base:** {recordista_cl[COL_ENVIADO]:,.0f}  
            **Assunto:** *{recordista_cl[COL_ASSUNTO]}*
            """)
                
            st.markdown("---")
            st.write("🌍 **Métricas de Mercado (Ed. Corporativa)**")
            
            c_m1, c_m2, c_m3 = st.columns(3)
            with c_m1:
                st.write(f"{'✅' if media_ab >= META_ABERTURA else '⚠️'} **Abr:** {media_ab:.1f}%")
            with c_m2:
                st.write(f"{'✅' if media_cl >= META_CTR else '⚠️'} **Cli:** {media_cl:.1f}%")
            with c_m3:
                st.write(f"{'✅' if cto_medio >= META_CTO else '⚠️'} **CTO:** {cto_medio:.1f}%")

        with st.expander("📋 Ver Dados Completos"):
            st.dataframe(df_filtrado[[COL_DATA, COL_BU, COL_PRODUTO, COL_ASSUNTO, COL_ENVIADO, COL_ABERTURA, COL_CLIQUE]].sort_values(by=COL_DATA, ascending=False))
    else:
        st.warning("Selecione os filtros para carregar a análise.")
else:
    st.info("👋 Suba a base Excel para ativar o Dashboard.")
