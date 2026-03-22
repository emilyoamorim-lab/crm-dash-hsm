import streamlit as st
import pandas as pd
import os

# Configuração da Página
st.set_page_config(page_title="AUDITORIA CRM - Cruzamento de Dados", layout="wide")

NOME_ARQUIVO_PADRAO = "Dados CRM 2026 - V3.xlsx"

st.title("🛠️ Ferramenta de Diagnóstico de Dados")
st.info("Use as tabelas abaixo para identificar por que o 'Executive Program T16' não está cruzando.")

if os.path.exists(NOME_ARQUIVO_PADRAO):
    try:
        excel = pd.ExcelFile(NOME_ARQUIVO_PADRAO)
        df_perf = excel.parse(0) # Performance
        df_conv = excel.parse(1) # Conversão

        # Limpeza básica de nomes de colunas
        df_perf.columns = [str(col).strip() for col in df_perf.columns]
        df_conv.columns = [str(col).strip() for col in df_conv.columns]

        # --- PREPARAÇÃO DAS CHAVES ---
        def preparar_chave(df):
            temp = df.copy()
            temp["Produto_Limpo"] = temp["Produto"].astype(str).str.strip()
            # Garante que o número de envios seja um número inteiro puro
            temp["Envios_Limpo"] = pd.to_numeric(temp["Emails Enviados"], errors='coerce').fillna(0).astype(int)
            return temp

        df_perf_limpo = preparar_chave(df_perf)
        df_conv_limpo = preparar_chave(df_conv)

        # --- TABELAS DE COMPARAÇÃO ---
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("1. Na Planilha de Performance (Aba 1)")
            st.write("Estes são os disparos que o sistema está tentando cruzar:")
            # Mostra apenas as colunas que importam para o cruzamento
            perf_view = df_perf_limpo[["Produto_Limpo", "Envios_Limpo", "Taxa de Abertura"]].drop_duplicates()
            st.dataframe(perf_view)

        with col2:
            st.subheader("2. Na Planilha de Conversão (Aba 2)")
            st.write("Estes são os dados que você preencheu na segunda aba:")
            conv_view = df_conv_limpo[["Produto_Limpo", "Envios_Limpo", "Oportunidades", "CTA"]].drop_duplicates()
            st.dataframe(conv_view)

        # --- TENTATIVA DE CRUZAMENTO REAL ---
        st.markdown("---")
        st.subheader("🔍 Resultado do Cruzamento (O que o Dash enxerga)")
        
        # Cruzamento final
        df_final = pd.merge(
            df_perf_limpo, 
            df_conv_limpo[["Produto_Limpo", "Envios_Limpo", "Oportunidades", "CTA", "Formato"]], 
            on=["Produto_Limpo", "Envios_Limpo"], 
            how="left"
        )

        # Filtro rápido para o T16 para você ver o erro
        t16_audit = df_final[df_final["Produto_Limpo"].str.contains("T16", case=False, na=False)]
        
        st.write("Abaixo está o resultado exato para o 'Executive Program T16' após o cruzamento:")
        st.dataframe(t16_audit[["Hora de Início do Envio", "Produto_Limpo", "Envios_Limpo", "Oportunidades", "CTA"]])

        if t16_audit["Oportunidades"].sum() == 0:
            st.error("🚨 ATENÇÃO: O T16 continua com 0 oportunidades.")
            st.write("""
            **Como corrigir na sua planilha Excel:**
            1. Verifique se o nome na Aba 1 é exatamente igual ao da Aba 2 (Cuidado com espaços).
            2. Verifique se o número de **Emails Enviados** é IDENTICO. Se na Aba 1 for 9.776 e na Aba 2 for 13.808, o sistema entende que são e-mails diferentes e não vai somar.
            """)
        else:
            st.success("✅ O cruzamento funcionou! Agora você pode voltar para o código anterior do Dashboard.")

    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
else:
    st.error(f"Arquivo {NOME_ARQUIVO_PADRAO} não encontrado no GitHub.")
