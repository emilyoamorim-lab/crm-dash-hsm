# --- CARREGAMENTO E CRUZAMENTO ---
if os.path.exists(NOME_ARQUIVO_PADRAO):
    try:
        excel = pd.ExcelFile(NOME_ARQUIVO_PADRAO)
        
        # VERIFICAÇÃO DE SEGURANÇA: Quantas abas existem?
        abas_encontradas = excel.sheet_names
        if len(abas_encontradas) < 2:
            st.error(f"⚠️ O arquivo no GitHub só tem {len(abas_encontradas)} aba: {abas_encontradas}")
            st.info("Para o Dashboard V2 funcionar, o seu Excel precisa ter 2 abas: uma com a Performance e outra com as Oportunidades/CTAs.")
            st.stop()
        
        # Se chegou aqui, tem pelo menos 2 abas
        df_perf = excel.parse(0) 
        df_conv = excel.parse(1) 

        # ... (resto do código de limpeza e merge igual ao anterior)
