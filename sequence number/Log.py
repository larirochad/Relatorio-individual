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
        
        df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
        df['Data/Hora Inclusão'] = pd.to_datetime(df['Data/Hora Inclusão'], errors='coerce')

        df_filtrado = df.dropna(subset=['Data/Hora Evento', 'Data/Hora Inclusão']).copy()

        df_filtrado['Delay'] = (df_filtrado['Data/Hora Inclusão'] - df_filtrado['Data/Hora Evento']).dt.total_seconds()

        # se é log ou nao 
        df_filtrado['Log'] = df_filtrado['Delay'].apply(lambda x: 'Sim' if x > 60 else 'Não')

        # Filtrar apenas mensagens que são logs
        df_logs = df_filtrado[df_filtrado['Log'] == 'Sim'].copy()
        
        # Calcular estatísticas
        total_mensagens = len(df_filtrado)
        total_logs = len(df_logs)
        percentual_logs = (total_logs / total_mensagens * 100) if total_mensagens > 0 else 0
        media_delay = df_logs['Delay'].mean() if len(df_logs) > 0 else 0
        
        # Encontrar mensagem com maior delay
        if len(df_logs) > 0:
            max_delay_idx = df_logs['Delay'].idxmax()
            mensagem_maior_delay = df_logs.loc[max_delay_idx, 'Tipo Mensagem']
            maior_delay = df_logs.loc[max_delay_idx, 'Delay']
        else:
            mensagem_maior_delay = "N/A"
            maior_delay = 0

        # Criar DataFrame de resultado apenas com logs
        df_resultado = df_logs[['Tipo Mensagem', 'Data/Hora Inclusão', 'Data/Hora Evento', 'Delay', 'Log']].copy()
        
        # Adicionar linha com estatísticas
        linha_estatisticas = pd.DataFrame({
            'Tipo Mensagem': ['ESTATÍSTICAS'],
            'Data/Hora Inclusão': [''],
            'Data/Hora Evento': [''],
            'Delay': [''],
            'Log': [''],
            'Percentual_Logs_Total': [f"{percentual_logs:.2f}%"],
            'Media_Delay_Logs': [f"{media_delay:.2f}s"],
            'Mensagem_Maior_Delay': [mensagem_maior_delay],
            'Maior_Delay_Encontrado': [f"{maior_delay:.2f}s"]
        })
        
        # Concatenar dados dos logs com estatísticas
        df_final = pd.concat([df_resultado, linha_estatisticas], ignore_index=True)

        # Exibir resultado
        print("OK ")
        df_final.to_csv(caminho_saida, index=False)

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    logs('logs/analise_par09.csv')