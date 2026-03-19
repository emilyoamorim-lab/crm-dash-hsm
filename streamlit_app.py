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
        
        # Mapeamento
        col_bu = st.sidebar.selectbox("Produto/BU:", df.columns, index=0)
        col_data_bruta = st.sidebar.selectbox("Coluna de Data/Hora:", df.columns, index=3)
        col_abertura = st.sidebar.selectbox("Taxa de Abertura:", df.columns, index=4)
        col_clique = st.sidebar.selectbox("Taxa de Clique:", df.columns, index=5)
        col_assunto = "Assunto" if "Assunto" in df.columns else df.columns[1]

        # Tratamento de Datas
        df[col_data_bruta] = pd.to_datetime(df[col_data_bruta], errors='coerce')
        df['Mês_Ref'] = df[col_data_bruta].dt.strftime('%m - %B %Y')
        df = df.sort_values(by=col_data_bruta)

        # Filtros
        st.sidebar.markdown("---")
        meses_selecionados = st.sidebar.multiselect("Mês:", options=df['Mês_Ref'].unique(), default=df['Mês_Ref'].unique())
        unidades_selecionadas = st.sidebar.multiselect("Unidade:", options=df[col_bu].unique(), default=df[col_bu].unique())

        df_filtrado = df[(df[col_bu].isin(unidades_selecionadas)) & (df['Mês_Ref'].isin(meses_selecionados))].copy()

        # --- AJUSTE E ARREDONDAMENTO (O segredo da limpeza) ---
        def ajustar_e_arredondar(valor):
            if pd.isna(valor): return 0
            # Se for decimal (0.22), multiplica por 100. Se for inteiro (22), mantém.
            num = valor * 100 if valor <= 1.0 else valor
            return round(num, 1) # Arredonda para 1 casa decimal

        df_filtrado[col_abertura] = df_filtrado[col_abertura].apply(ajustar_e_arredondar)
        df_filtrado[col_clique] = df_filtrado[col_clique].apply(ajustar_e_arredondar)

        # KPIs superiores
        m1, m2, m3 = st.columns(3)
        media_ab = df_filtrado[col_abertura].mean()
        m1.metric("Abertura Média", f"{media_ab:.1f}%", delta=f"{media_ab - 22:.1f}% vs Meta")
        m2.metric("Clique Médio", f"{df_filtrado[col_clique].mean():.1f}%")
        m3.metric("Eficiência (CTO)", f"{(df_filtrado[col_clique].mean()/media_ab)*100:.1f}%" if media_ab > 0 else "0%")

        # --- GRÁFICO REFINADO ---
        st.markdown("---")
        st.subheader("📈 Evolução Detalhada por Disparo")
        
        fig_evol = px.line(df_filtrado, 
                          x=col_data_bruta, 
                          y=col_abertura, 
                          color=col_bu,
                          markers=True,
                          title="Performance de Abertura")
        
        # Ajustando o que aparece no balão ao passar o mouse (hovertemplate)
        fig_evol.update_traces(
            hovertemplate="<b>Assunto:</b> %{customdata[0]}<br>" +
                          "<b>Data:</b> %{x|%d/%m %H:%M}<br>" +
                          "<b>Abertura:</b> %{y:.1f}%<extra></extra>",
            customdata=df_filtrado[[col_assunto]]
        )
        
        fig_evol.update_layout(xaxis_title="Data e Hora", yaxis_title="Abertura (%)")
        st.plotly_chart(fig_evol, use_container_width=True)

        # Tabela formatada
        st.subheader("📋 Detalhes dos E-mails")
        # Criamos uma cópia para exibição com o símbolo de % na tabela
        df_exibicao = df_filtrado[[col_data_bruta, col_bu, col_assunto, col_abertura]].copy()
        st.dataframe(df_exibicao.sort_values(by=col_data_bruta, ascending=False), use_container_width=True)

    except Exception as e:
        st.error(f"Erro: {e}")
else:
    st.info("👋 Suba sua planilha para ver os dados arredondados!")
