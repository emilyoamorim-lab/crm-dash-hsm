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
        m4.metric("Eficiência (CTO)", f"{cto_medio:.1f}%")

        # --- GRÁFICO ---
        st.markdown("---")
        fig_evol = px.line(df_filtrado, x=COL_DATA, y=COL_ABERTURA, color=COL_PRODUTO, markers=True, 
                           title="Tendência: Taxa de Abertura por Disparo")
        fig_evol.update_traces(
            hovertemplate="<b>Produto:</b> %{fullData.name}<br><b>Data:</b> %{x}<br><b>Base:</b> %{customdata[1]:,.0f}<br><b>Abertura:</b> %{y:.1f}%<extra></extra>",
            customdata=df_filtrado[[COL_ASSUNTO, COL_ENVIADO]]
        )
        st.plotly_chart(fig_evol, use_container_width=True)

        # --- ANÁLISE E RESUMO ---
        st.markdown("---")
        col_an1, col_an2 = st.columns([1.8, 1.2])

        # Localizar recordistas antecipadamente para usar em ambos os lados
        recordista_ab = df_filtrado.loc[df_filtrado[COL_ABERTURA].idxmax()]
        recordista_cl = df_filtrado.loc[df_filtrado[COL_CLIQUE].idxmax()]

        with col_an1:
            st.subheader("🕵️ Análise do Especialista")
            if len(produtos_sel) >= 1:
                # Lógica de Insight Baseada em Volume
                media_volume = df_filtrado[COL_ENVIADO].mean()
                tipo_sucesso = "Escala/Geral" if recordista_ab[COL_ENVIADO] > media_volume else "Nicho/Segmentado"
                
                st.info(f"""
                **Diagnóstico de Performance: {recordista_ab[COL_PRODUTO]}**
                
                O recorde de abertura foi de **{recordista_ab[COL_ABERTURA]:.1f}%** em **{recordista_ab[COL_DATA].strftime('%d/%m/%Y')}**. 
                Este disparo impactou **{recordista_ab[COL_ENVIADO]:,.0f} pessoas**, o que caracteriza um sucesso de estratégia de **{tipo_sucesso}**.
                
                **Análise de Conversão:** O melhor clique do período atingiu **{recordista_cl[COL_CLIQUE]:.1f}%** em uma base de **{recordista_cl[COL_ENVIADO]:,.0f} pessoas**. 
                {"Isso mostra que ofertas focadas em grupos menores estão convertendo melhor." if recordista_cl[COL_ENVIADO] < media_volume else "Este volume prova que a oferta tem alto poder de tração em bases maiores."}
                
                **Resumo Acumulado:** Nos filtros aplicados, o CRM gerou um impacto total de **{total_base:,.0f} contatos única/vezes**.
                """)
            else:
                st.write("Selecione um produto para análise detalhada.")

        with col_an2:
            st.subheader("🏆 Recordistas do Filtro")
            
            # Card de Melhor Abertura
            st.success(f"""
            🔥 **Melhor Taxa de Abertura: {recordista_ab[COL_ABERTURA]:.1f}%**  
            **Data:** {recordista_ab[COL_DATA].strftime('%d/%m/%Y')}  
            **Base Impactada:** {recordista_ab[COL_ENVIADO]:,.0f} pessoas  
            **Assunto:** *{recordista_ab[COL_ASSUNTO]}*
            """)

            # Card de Melhor Clique
            st.info(f"""
            🚀 **Melhor Taxa de Clique: {recordista_cl[COL_CLIQUE]:.1f}%**  
            **Data:** {recordista_cl[COL_DATA].strftime('%d/%m/%Y')}  
            **Base Impactada:** {recordista_cl[COL_ENVIADO]:,.0f} pessoas  
            **Assunto:** *{recordista_cl[COL_ASSUNTO]}*
            """)
                
            st.markdown("---")
            st.write("🌍 **Métricas de Mercado (Ed. Corporativa)**")
            
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                st.write(f"{'✅' if media_ab >= META_ABERTURA else '⚠️'} **Abertura:** {media_ab:.1f}%")
                st.caption(f"Meta: {META_ABERTURA}%")
            with c_m2:
                st.write(f"{'✅' if media_cl >= META_CTR else '⚠️'} **Clique:** {media_cl:.1f}%")
                st.caption(f"Meta: {META_CTR}%")

        with st.expander("📋 Ver Dados Completos"):
            st.dataframe(df_filtrado[[COL_DATA, COL_BU, COL_PRODUTO, COL_ASSUNTO, COL_ENVIADO, COL_ABERTURA, COL_CLIQUE]].sort_values(by=COL_DATA, ascending=False))
    else:
        st.warning("Selecione os filtros para carregar a análise.")
else:
    st.info("👋 Suba a base Excel para ativar o Dashboard.")
