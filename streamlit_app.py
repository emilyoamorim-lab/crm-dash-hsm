import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="CRM Dash - HSM/Singularity", layout="wide")

st.title("📊 Dashboard de Performance CRM")
st.markdown("---")

st.sidebar.header("⚙️ Configurações")
arquivo = st.sidebar.file_uploader("Suba sua base semanal", type=["csv", "xlsx"])

if arquivo:
    try:
        df = pd.read_excel(arquivo) if arquivo.name.endswith('.xlsx') else pd.read_csv(arquivo)
        
        # Mapeamento Automático
        col_bu = st.sidebar.selectbox("Produto/BU:", df.columns, index=0)
        col_data_bruta = st.sidebar.selectbox("Coluna de Data/Hora:", df.columns, index=3)
        col_abertura = st.sidebar.selectbox("Taxa de Abertura:", df.columns, index=4)
        col_clique = st.sidebar.selectbox("Taxa de Clique:", df.columns, index=5)
        # Tenta achar a coluna de Assunto para o gráfico
        col_assunto = "Assunto" if "Assunto" in df.columns else df.columns[1]

        # Tratamento de Datas
        df[col_data_bruta] = pd.to_datetime(df[col_data_bruta], errors='coerce')
        df['Mês_Ref'] = df[col_data_bruta].dt.strftime('%m - %B %Y')
        df = df.sort_values(by=col_data_bruta)

        # Filtros
        st.sidebar.markdown("---")
        meses_selecionados = st.sidebar.multiselect("Selecionar Mês:", options=df['Mês_Ref'].unique(), default=df['Mês_Ref'].unique())
        unidades_selecionadas = st.sidebar.multiselect("Selecionar Unidade:", options=df[col_bu].unique(), default=df[col_bu].unique())

        df_filtrado = df[(df[col_bu].isin(unidades_selecionadas)) & (df['Mês_Ref'].isin(meses_selecionados))].copy()

        # Ajuste de %
        def ajustar_porcentagem(valor):
            if pd.isna(valor): return 0
            return valor * 100 if valor <= 1.0 else valor

        df_filtrado[col_abertura] = df_filtrado[col_abertura].apply(ajustar_porcentagem)
        df_filtrado[col_clique] = df_filtrado[col_clique].apply(ajustar_porcentagem)

        # KPIs
        m1, m2, m3 = st.columns(3)
        media_ab = df_filtrado[col_abertura].mean()
        m1.metric("Abertura Média", f"{media_ab:.2f}%", delta=f"{media_ab - 22:.1f}% vs Meta")
        m2.metric("Clique Médio", f"{df_filtrado[col_clique].mean():.2f}%")
        m3.metric("Eficiência (CTO)", f"{(df_filtrado[col_clique].mean()/media_ab)*100:.1f}%" if media_ab > 0 else "0%")

        # --- NOVO GRÁFICO: EVOLUÇÃO POR DISPARO ---
        st.markdown("---")
        st.subheader("📈 Evolução Detalhada por Disparo")
        st.write("Cada ponto representa um envio individual. Passe o mouse para ver o assunto.")
        
        fig_evol = px.line(df_filtrado, 
                          x=col_data_bruta, 
                          y=col_abertura, 
                          color=col_bu, # Diferencia cores por produto
                          markers=True,
                          hover_data={col_data_bruta: '|%d/%m %H:%M', col_assunto: True, col_abertura: ':.2f%'},
                          title="Performance de Abertura ao Longo do Tempo")
        
        # Estilizando o gráfico
        fig_evol.update_layout(xaxis_title="Data e Hora do Envio", yaxis_title="Taxa de Abertura (%)")
        st.plotly_chart(fig_evol, use_container_width=True)

        # Tabela
        st.subheader("📋 Detalhes dos E-mails Enviados")
        st.dataframe(df_filtrado[[col_data_bruta, col_bu, col_assunto, col_abertura]].sort_values(by=col_data_bruta, ascending=False))

    except Exception as e:
        st.error(f"Erro: {e}")
else:
    st.info("👋 Suba sua planilha para ver a evolução dos disparos!")
