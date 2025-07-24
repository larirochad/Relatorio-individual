import pandas as pd

def calcular_time_fix(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Converte datas
    df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
    df['GNSS UTC Time'] = pd.to_datetime(df['GNSS UTC Time'], errors='coerce')

    df_filtrado = df.dropna(subset=['Data/Hora Evento', 'GNSS UTC Time']).copy()

    # Filtrar apenas linhas em que o ano de evento e GNSS UTC Time são iguais
    df_filtrado = df_filtrado[df_filtrado['Data/Hora Evento'].dt.year == df_filtrado['GNSS UTC Time'].dt.year]

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
    colunas_ordenadas = ['Linha', 'Data/Hora Evento', 'GNSS UTC Time', 'Time fix', 'Média Geral', 'Média dos valores com delay']
    colunas_restantes = [col for col in df_filtrado.columns if col not in colunas_ordenadas]
    df_final = df_filtrado[colunas_ordenadas]

    return df_final

if __name__ == "__main__":
    calcular_time_fix('logs/867488061317839_decoded.csv')
