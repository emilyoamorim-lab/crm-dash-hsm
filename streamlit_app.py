import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da Página
st.set_page_config(page_title="CRM Performance - Ecossistema HSM", layout="wide")

# --- CONFIGURAÇÕES FIXAS ---
NOME_ARQUIVO_PADRAO = "Dados CRM 2026 - V2.xlsx"
COL_BU = "BU"
COL_PRODUTO = "Produto"
COL_DATA = "Hora de Início do Envio"
COL_ABERTURA = "Taxa de Abertura"
COL_CLIQUE = "Taxa de Cliques" # Verifique se na sua planilha o nome é este exatamente
COL_ASSUNTO = "Assunto"
COL_ENVIADO = "Enviado" # Coluna que contém o volume da base

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
        df[COL_DATA] = pd.to_datetime(df[COL_DATA], errors='coerce')
        df = df.dropna(subset=[COL_DATA])
        
        # Garantir que Enviado seja número
        df[COL_ENVIADO] = pd.to_numeric(df[COL_ENVIADO], errors='coerce').fillna(0)
        
        # Limpar taxas
        df[COL_ABERTURA] = df[COL_ABERTURA].apply(limpar_porcentagem)
        df[COL_CLIQUE] = df[COL_CLIQUE].apply(limpar_porcentagem)
        
        df['Mês_Ref'] = df[COL_DATA].dt.strftime('%m - %B %Y')
        df = df.sort_values(by=COL_DATA)
    except Exception as e:
        st.error(f"Erro ao carregar a base: {e}")

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
        # --- KPIs NO TOPO (Agora com 4 colunas) ---
        m1, m2, m3, m4 = st.columns(4)
        
        total_base = df_filtrado[COL_ENVIADO].sum()
        media_ab = df_filtrado[COL_ABERTURA].mean()
        media_cl = df_filtrado[COL_CLIQUE].mean()
        cto_medio = (media_cl / media_ab * 100) if media_ab > 0 else 0
        
        m1.metric("Base Impactada", f"{total_base:,.0f}".replace(",", "."))
        m2.metric("Abertura Média", f"{media_ab:.1f}%", delta=f"{media_ab - 22:.1f}% vs Meta")
        m3.metric("Clique Médio (CTR)", f"{media_cl:.1f}%")
        m4.metric("Eficiência (CTO)", f"{cto_medio:.1f}%")

        # --- GRÁFICO ---
        st.markdown("---")
        fig_evol = px.line(df_filtrado, x=COL_DATA, y=COL_ABERTURA, color=COL_PRODUTO, markers=True)
        # Incluindo Volume e Clique no Hover (passar o mouse)
        fig_evol.update_traces(
            hovertemplate="<b>Produto:</b> %{fullData.name}<br><b>Data:</b> %{x}<br><b>Base:</b> %{customdata[1]:,.0f}<br><b>Abertura:</b> %{y:.1f}%<br><b>Clique:</b> %{customdata[2]:.1f}%<extra></extra>",
            customdata=df_filtrado[[COL_ASSUNTO, COL_ENVIADO, COL_CLIQUE]]
        )
        st.plotly_chart(fig_evol, use_container_width=True)

        # --- ANÁLISE DO ESPECIALISTA ---
        st.markdown("---")
        col_an1, col_an2 = st.columns([2, 1])

        with col_an1:
            st.subheader("🕵️ Análise do Especialista")
            if len(produtos_sel) >= 1:
                # Localizar o melhor envio por abertura
                melhor_envio = df_filtrado.loc[df_filtrado[COL_ABERTURA].idxmax()]
                data_str = melhor_envio[COL_DATA].strftime('%d/%m/%Y')
                base_vol = melhor_envio[COL_ENVIADO]
                clique_vol = melhor_envio[COL_CLIQUE]
                
                st.info(f"""
                **Diagnóstico de Performance:**
                
                O disparo realizado em **{data_str}** para o produto **{melhor_envio[COL_PRODUTO]}** foi o de maior impacto.
                Ele alcançou uma base de **{base_vol:,.0f} pessoas** e obteve uma taxa de abertura excepcional de **{melhor_envio[COL_ABERTURA]:.1f}%**.
                
                **Engajamento de Clique:**
                Neste mesmo envio, a taxa de clique foi de **{clique_vol:.1f}%**. 
                Isso indica que, além de um assunto atrativo (*"{melhor_envio[COL_ASSUNTO]}"*), o conteúdo interno conseguiu converter o interesse em ação.
                
                **Panorama Geral:**
                No total, para os filtros selecionados, você impactou **{total_base:,.0f} contatos**. A média de clique (CTR) está em **{media_cl:.1f}%**.
                """)

                # Alertas inteligentes
                if media_cl < 2.0:
                    st.warning("⚠️ **Atenção:** Sua taxa de clique média está baixa. O público está abrindo o e-mail, mas o botão (CTA) ou a oferta não estão sendo clicados.")
                elif cto_medio > 50:
                    st.success("🚀 **Alta Conversão:** Seu CTO está acima de 50%, o que significa que mais da metade das pessoas que abrem o e-mail clicam em algo. Conteúdo muito relevante!")

            else:
                st.write("Selecione um produto para ver a análise detalhada.")

        with col_an2:
            st.subheader("🌟 Resumo do Filtro")
            st.write(f"**Total Base:** {total_base:,.0f}".replace(",", "."))
            st.write(f"**Melhor Clique:** {df_filtrado[COL_CLIQUE].max():.1f}%")
            st.write(f"**Volume Médio/Envio:** {df_filtrado[COL_ENVIADO].mean():,.0f}".replace(",", "."))
            st.write("---")
            st.caption("Meta de Abertura: 22.0%")

        with st.expander("📋 Ver Dados Completos"):
            st.dataframe(df_filtrado[[COL_DATA, COL_BU, COL_PRODUTO, COL_ASSUNTO, COL_ENVIADO, COL_ABERTURA, COL_CLIQUE]].sort_values(by=COL_DATA, ascending=False))
    else:
        st.warning("Selecione os filtros para carregar a análise.")
else:
    st.info("👋 Suba a base Excel para ativar o Dashboard.")
