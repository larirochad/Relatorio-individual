import pandas as pd

def logs(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    try:
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
            # print(maior_delay)
            linha_maior_delay = df_logs.loc[max_delay_idx, 'Linha']
        else:
            mensagem_maior_delay = ""
            maior_delay = ""
            linha_maior_delay = ""

        # Criar DataFrame de resultado apenas com logs
        colunas = ['Linha', 'Tipo Mensagem', 'Data/Hora Inclusão', 'Data/Hora Evento', 'Delay', 'Log']
        df_resultado = df_logs[colunas].copy()
        if not isinstance(df_resultado, pd.DataFrame):
            df_resultado = pd.DataFrame(df_resultado)

        # Criar DataFrame separado com estatísticas
        df_estatisticas = pd.DataFrame({
            'Tipo Mensagem': ['ESTATÍSTICAS'],
            'Percentual_Logs_Total': [f"{percentual_logs:.2f}%"],
            'Media_Delay_Logs': [f"{media_delay:.2f}s"],
            'Mensagem_Maior_Delay': [mensagem_maior_delay],
            'Maior_Delay_Encontrado': [f"{maior_delay:.2f}s"],
            'Linha_Maior_Delay': [linha_maior_delay]
        })

        # Exibir resultado
        # print("OK ")
        # print(df_resultado)
        return df_resultado, df_estatisticas
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return pd.DataFrame(), pd.DataFrame() # Retorna DataFrames vazios em caso de erro

if __name__ == "__main__":
    df = pd.read_csv('logs/867488065171646_decoded.csv', encoding='iso-8859-1')
    logs(df)     