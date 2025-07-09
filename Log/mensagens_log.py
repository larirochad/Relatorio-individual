import pandas as pd

def logs(caminho_arquivo, caminho_saida='Log/logs.csv'):
    try:
        df = None
        for enc in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
            try:
                df = pd.read_csv(caminho_arquivo, encoding=enc, low_memory=False)
                break
            except Exception:
                continue
        if df is None:
            print("❌ Não foi possível ler o arquivo.")
            return
        
        # Adicionar índice da linha original (considerando cabeçalho)
        df['Linha'] = df.index + 2  # +2 porque index começa em 0 e tem o cabeçalho
        
        df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
        df['Data/Hora Inclusão'] = pd.to_datetime(df['Data/Hora Inclusão'], errors='coerce')

        df_filtrado = df.dropna(subset=['Data/Hora Evento', 'Data/Hora Inclusão']).copy()

        df_filtrado['Delay'] = (df_filtrado['Data/Hora Inclusão'] - df_filtrado['Data/Hora Evento']).dt.total_seconds().astype(float)

        # se é log ou nao 
        df_filtrado['Log'] = df_filtrado['Delay'].apply(lambda x: 'Sim' if x > 60 else 'Não')

        # Filtrar apenas mensagens que são logs
        df_logs = df_filtrado[df_filtrado['Log'] == 'Sim'].copy()
        if not isinstance(df_logs, pd.DataFrame):
            df_logs = pd.DataFrame(df_logs)
        
        # Calcular estatísticas
        total_mensagens = len(df_filtrado)
        total_logs = len(df_logs)
        percentual_logs = (total_logs / total_mensagens * 100) if total_mensagens > 0 else 0
        media_delay = df_logs['Delay'].mean() if len(df_logs) > 0 else 0
        
        # Encontrar mensagem com maior delay
        if len(df_logs) > 0:
            delay_series = pd.Series(df_logs['Delay'].values, index=df_logs.index)
            max_delay_idx = delay_series.idxmax()
            mensagem_maior_delay = df_logs.loc[max_delay_idx, 'Tipo Mensagem']
            maior_delay = df_logs.loc[max_delay_idx, 'Delay']
            linha_maior_delay = df_logs.loc[max_delay_idx, 'Linha']
        else:
            mensagem_maior_delay = ""
            maior_delay = ""
            linha_maior_delay = ""

        # Criar DataFrame de resultado apenas com logs
        colunas = ['Linha', 'Tipo Mensagem', 'Data/Hora Inclusão', 'Data/Hora Evento', 'Delay', 'Log',
                   'Percentual_Logs_Total', 'Media_Delay_Logs', 'Mensagem_Maior_Delay', 'Maior_Delay_Encontrado', 'Linha_Maior_Delay']
        df_resultado = df_logs[['Linha', 'Tipo Mensagem', 'Data/Hora Inclusão', 'Data/Hora Evento', 'Delay', 'Log']].copy()
        for col in colunas[6:]:
            df_resultado[col] = ''
        df_resultado = df_resultado[colunas]  # garantir ordem
        if not isinstance(df_resultado, pd.DataFrame):
            df_resultado = pd.DataFrame(df_resultado)

        # Adicionar linha com estatísticas na primeira linha, apenas valores
        linha_estatisticas = pd.DataFrame({
            'Linha': [''],
            'Tipo Mensagem': [''],
            'Data/Hora Inclusão': [''],
            'Data/Hora Evento': [''],
            'Delay': [''],
            'Log': [''],
            'Percentual_Logs_Total': [f"{percentual_logs:.2f}%"],
            'Media_Delay_Logs': [f"{media_delay:.2f}s"],
            'Mensagem_Maior_Delay': [mensagem_maior_delay],
            'Maior_Delay_Encontrado': [f"{maior_delay:.2f}s"],
            'Linha_Maior_Delay': [linha_maior_delay]
        })[colunas]
        if not isinstance(linha_estatisticas, pd.DataFrame):
            linha_estatisticas = pd.DataFrame(linha_estatisticas)
        
        # Concatenar estatísticas antes dos logs
        df_final = pd.concat([linha_estatisticas, df_resultado], ignore_index=True)

        # Exibir resultado
        print("OK ")
        df_final.to_csv(caminho_saida, index=False)

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    logs('logs/analise_par09.csv') 