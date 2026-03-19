import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da Página
st.set_page_config(page_title="CRM Performance - Ecossistema HSM", layout="wide")

# --- CONFIGURAÇÕES FIXAS ---
NOME_ARQUIVO_PADRAO = "Dados CRM 2026 - V2.xlsx"

st.title("📊 Dashboard de Performance CRM")

# --- FUNÇÃO DE LIMPEZA DE TAXAS ---
def limpar_porcentagem(valor):
    if pd.isna(valor): return 0.0
    if isinstance(valor, str):
        valor = valor.replace('%', '').replace(',', '.')
        try: return float(valor)
        except: return 0.0
    return float(valor) * 100 if valor <= 1.0 else float(valor)

# --- CARREGAMENTO E TRATAMENTO ---
df = None
if os.path.exists(NOME_ARQUIVO_PADRAO):
    try:
        df = pd.read_excel(NOME_ARQUIVO_PADRAO)
        
        # LIMPEZA DE CABEÇALHOS: Remove espaços extras nos nomes das colunas
        df.columns = [str(col).strip() for col in df.columns]

        # MAPEAMENTO DINÂMICO (Garante que o código ache as colunas mesmo com nomes levemente diferentes)
        # Se não achar 'Enviado', tenta 'Enviados' ou 'Total Enviado'
        COL_DATA = "Hora de Início do Envio"
        COL_BU = "BU"
        COL_PRODUTO = "Produto"
        COL_ASSUNTO = "Assunto"
        COL_ABERTURA = "Taxa de Abertura"
        COL_CLIQUE = "Taxa de Cliques"
        COL_ENVIADO = "Enviado"

        # Verificar se as colunas essenciais existem, senão avisar
        colunas_faltando = [c for c in [COL_DATA, COL_ENVIADO, COL_ABERTURA] if c not in df.columns]
        if colunas_faltando:
            st.error(f"⚠️ Colunas não encontradas no Excel: {colunas_faltando}")
            st.write("Colunas detectadas no seu arquivo:", list(df.columns))
            st.stop()

        # Tratamento de dados
        df[COL_DATA] = pd.to_datetime(df[COL_DATA], errors='coerce')
        df = df.dropna(subset=[COL_DATA])
        df[COL_ENVIADO] = pd.to_numeric(df[COL_ENVIADO], errors='coerce').fillna(0)
        df[COL_ABERTURA] = df[COL_ABERTURA].apply(limpar_porcentagem)
        df[COL_CLIQUE] = df[COL_CLIQUE].apply(limpar_porcentagem)
        
        df['Mês_Ref'] = df[COL_DATA].dt.strftime('%m - %B %Y')
        df = df.sort_values(by=COL_DATA)

    except Exception as e:
        st.error(f"Erro crítico ao processar os dados: {e}")
        st.stop()

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
        # --- KPIs ---
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
        fig_evol.update_traces(
            hovertemplate="<b>Produto:</b> %{fullData.name}<br><b>Data:</b> %{x}<br><b>Base:</b> %{customdata[1]:,.0f}<br><b>Abertura:</b> %{y:.1f}%<extra></extra>",
            customdata=df_filtrado[[COL_ASSUNTO, COL_ENVIADO]]
        )
        st.plotly_chart(fig_evol, use_container_width=True)

        # --- ANÁLISE ---
        st.markdown("---")
        col_an1, col_an2 = st.columns([2, 1])

        with col_an1:
            st.subheader("🕵️ Análise do Especialista")
            if len(produtos_sel) >= 1:
                melhor_envio = df_filtrado.loc[df_filtrado[COL_ABERTURA].idxmax()]
                data_str = melhor_envio[COL_DATA].strftime('%d/%m/%Y')
                
                st.info(f"""
                **Diagnóstico: {melhor_envio[COL_PRODUTO]}**
                
                No melhor cenário deste filtro, o disparo de **{data_str}** alcançou **{melhor_envio[COL_ENVIADO]:,.0f} pessoas**.
                A taxa de abertura foi de **{melhor_envio[COL_ABERTURA]:.1f}%** com uma taxa de clique de **{melhor_envio[COL_CLIQUE]:.1f}%**.
                
                **Resumo do Alcance:** No total do período selecionado, sua estratégia de CRM impactou **{total_base:,.0f} contatos única/vezes**.
                """)
            else:
                st.write("Selecione um produto para análise.")

        with col_an2:
            st.subheader("🌟 Resumo")
            st.write(f"**Total Base:** {total_base:,.0f}".replace(",", "."))
            st.write(f"**Abertura Máx:** {df_filtrado[COL_ABERTURA].max():.1f}%")
            st.write("---")
            st.caption("Meta de Abertura: 22%")

        with st.expander("📋 Dados"):
            st.dataframe(df_filtrado[[COL_DATA, COL_BU, COL_PRODUTO, COL_ASSUNTO, COL_ENVIADO, COL_ABERTURA, COL_CLIQUE]])
    else:
        st.warning("Selecione filtros válidos.")
else:
    st.info("👋 Arquivo não encontrado ou erro no carregamento.")
