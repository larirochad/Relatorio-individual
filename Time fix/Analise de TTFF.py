import pandas as pd

def calcular_time_fix(caminho_csv, caminho_saida='Time fix/time_fix_resultado.csv'):
    try:
        # Tenta múltiplas codificações
        codificacoes = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        for encoding in codificacoes:
            try:
                df = pd.read_csv(caminho_csv, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            print("❌ Erro: Não foi possível ler o arquivo com as codificações testadas.")
            return

        # Converte datas
        df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
        df['GNSS UTC Time'] = pd.to_datetime(df['GNSS UTC Time'], errors='coerce')

        df_filtrado = df.dropna(subset=['Data/Hora Evento', 'GNSS UTC Time']).copy()

        df_filtrado['Time fix'] = (df_filtrado['Data/Hora Evento'] - df_filtrado['GNSS UTC Time']).dt.total_seconds()

        # Calcula as médias
        media_geral = df_filtrado['Time fix'].mean()
        
        # Média desconsiderando valores 0 (apenas valores com delay)
        valores_com_delay = df_filtrado[df_filtrado['Time fix'] > 0]['Time fix']
        media_com_delay = valores_com_delay.mean() if len(valores_com_delay) > 0 else 0

        # Adiciona o número da linha (contando o cabeçalho)
        df_filtrado['Linha'] = df_filtrado.index + 2  # +2 porque o cabeçalho é linha 1 e o index começa em 0

        # Adiciona as colunas de médias
        df_filtrado['Média Geral'] = media_geral
        df_filtrado['Média dos valores com delay'] = media_com_delay

        # Reorganiza as colunas para ficar mais clara
        colunas_ordenadas = ['Linha', 'Data/Hora Evento', 'Time fix', 'Média Geral', 'Média dos valores com delay']
        colunas_restantes = [col for col in df_filtrado.columns if col not in colunas_ordenadas]
        df_final = df_filtrado[colunas_ordenadas]

        df_final.to_csv(caminho_saida, index=False)
        print(f'✅ Arquivo salvo como: {caminho_saida}')
        print(f'📊 Média geral do Time fix: {media_geral:.2f} segundos')
        print(f'📈 Média dos valores com delay: {media_com_delay:.2f} segundos')
        print(f'🔢 Total de registros processados: {len(df_filtrado)}')
        print(f'⏱️ Registros com delay (>0): {len(valores_com_delay)}')

    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")

if __name__ == "__main__":
    calcular_time_fix('logs/analise_par09.csv')
