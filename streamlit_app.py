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
COL_CLIQUE = "Taxa de Cliques"
COL_ASSUNTO = "Assunto"
COL_ENVIADO = "Enviado"  # Nova coluna identificada na sua planilha

st.title("📊 Dashboard de Performance CRM")

# --- FUNÇÃO DE LIMPEZA DE DADOS ---
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
        
        # Tratamento de tipos
        df[COL_DATA] = pd.to_datetime(df[COL_DATA], errors='coerce')
        df = df.dropna(subset=[COL_DATA])
        
        # Garante que "Enviado" seja número (volume da base)
        df[COL_ENVIADO] = pd.to_numeric(df[COL_ENVIADO], errors='coerce').fillna(0)
        
        # Limpa as taxas
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

    # Aplicação Final dos Filtros
    df_filtrado = df[
        (df['Mês_Ref'].isin(meses_sel)) & 
        (df[COL_BU].isin(bus_sel)) & 
        (df[COL_PRODUTO].isin(produtos_sel))
    ].copy()

    if not df_filtrado.empty:
        # --- KPIs GERAIS (Agora com a Base Impactada) ---
        m1, m2, m3, m4, m5 = st.columns(5)
        
        total_base = df_filtrado[COL_ENVIADO].sum()
        media_ab = df_filtrado[COL_ABERTURA].mean()
        media_cl = df_filtrado[COL_CLIQUE].mean()
        cto_medio = (media_cl / media_ab * 100) if media_ab > 0 else 0
        total_envios = len(df_filtrado)
        
        m1.metric("Base Impactada", f"{total_base:,.0f}".replace(",", "."))
        m2.metric("Abertura Média", f"{media_ab:.1f}%", delta=f"{media_ab - 22:.1f}% vs Meta")
        m3.metric("Clique Médio", f"{media_cl:.1f}%")
        m4.metric("Eficiência (CTO)", f"{cto_medio:.1f}%")
        m5.metric("Qtd. Disparos", total_envios)

        # --- GRÁFICO ---
        st.markdown("---")
        st.subheader("📈 Evolução de Performance")
        fig_evol = px.line(df_filtrado, x=COL_DATA, y=COL_ABERTURA, color=COL_PRODUTO, 
                           markers=True, hover_data=[COL_ASSUNTO, COL_ENVIADO])
        
        fig_evol.update_traces(
            hovertemplate="<b>Produto:</b> %{fullData.name}<br><b>Data:</b> %{x}<br><b>Base:</b> %{customdata[1]}<br><b>Abertura:</b> %{y:.1f}%<extra></extra>",
            customdata=df_filtrado[[COL_ASSUNTO, COL_ENVIADO]]
        )
        st.plotly_chart(fig_evol, use_container_width=True)

        # --- ANÁLISE DO ESPECIALISTA (Com dados de volume) ---
        st.markdown("---")
        col_an1, col_an2 = st.columns([2, 1])

        with col_an1:
            st.subheader("🕵️ Análise do Especialista")
            if len(produtos_sel) >= 1:
                melhor_envio = df_filtrado.loc[df_filtrado[COL_ABERTURA].idxmax()]
                data_str = melhor_envio[COL_DATA].strftime('%d/%m/%Y')
                base_recorde = melhor_envio[COL_ENVIADO]
                
                # Texto dinâmico
                st.info(f"""
                **Análise de Alcance e Conversão:**
                
                No período selecionado, o produto **{melhor_envio[COL_PRODUTO]}** teve seu maior pico de engajamento no dia **{data_str}**. 
                Neste disparo, impactamos uma base de **{base_recorde:,.0f} pessoas**, alcançando uma taxa de abertura recorde de **{melhor_envio[COL_ABERTURA]:.1f}%**.
                
                **Resumo Acumulado:**
                Somando todos os disparos dos filtros atuais, você impactou um total de **{total_base:,.0f} contatos**. 
                Isso representa um esforço de **{total_envios} campanhas** distintas.
                """)

                if total_base > 50000 and media_ab < 15:
                    st.warning("⚠️ **Atenção ao Volume:** Você está impactando uma base muito grande, mas a taxa de abertura está caindo. Considere segmentar mais os envios para aumentar a relevância.")
                elif media_ab > 25:
                    st.success("🚀 **Alta Relevância:** Sua taxa de abertura está excelente para o volume enviado. O público está bem engajado com os assuntos atuais.")
            else:
                st.write("Selecione produtos para uma análise volumétrica.")

        with col_an2:
            st.subheader("🌟 Resumo do Filtro")
            st.write(f"**Total de Contatos:** {total_base:,.0f}".replace(",", "."))
            st.write(f"**Abertura Máxima:** {df_filtrado[COL_ABERTURA].max():.1f}%")
            st.write(f"**Volume Médio por Envio:** {df_filtrado[COL_ENVIADO].mean():,.0f}".replace(",", "."))
            st.write("---")
            st.caption("Meta sugerida para CRM HSM: 22%")

        with st.expander("📋 Ver Dados Brutos"):
            st.dataframe(df_filtrado[[COL_DATA, COL_BU, COL_PRODUTO, COL_ASSUNTO, COL_ENVIADO, COL_ABERTURA, COL_CLIQUE]].sort_values(by=COL_DATA, ascending=False))
    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
else:
    st.info("👋 Aguardando arquivo 'Dados CRM 2026 - V2.xlsx' para iniciar.")
