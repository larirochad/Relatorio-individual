import os
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

def analise_medias(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    salvar_csv = False

    df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
    df['Satélites'] = pd.to_numeric(df['Satélites'], errors='coerce')
    df['Precisão GNSS'] = pd.to_numeric(df['Precisão GNSS'], errors='coerce')

    df_filtrado = df.dropna(subset=['Data/Hora Evento', 'Satélites', 'Precisão GNSS'])

    coluna_dia = df_filtrado['Data/Hora Evento']
    satelites = df_filtrado['Satélites']
    hdop = df_filtrado['Precisão GNSS']

    # Calcular totais e válidos/invalidos separadamente para Satélites e HDOP
    total_registros = len(df_filtrado)
    satelites_invalidos = (satelites == 0).sum()
    hdop_invalidos = (hdop == 0).sum()
    registros_validos = ((satelites > 0) & (hdop > 0)).sum()
    registros_invalidos = total_registros - registros_validos
    perc_invalidos = (registros_invalidos / total_registros * 100) if total_registros > 0 else 0
    perc_validos = (registros_validos / total_registros * 100) if total_registros > 0 else 0
    # === TABELA 1: TODOS OS DADOS ===
    def stats_serie(serie):
        return {
            'Média': f"{serie.mean():.2f}",
            'Moda': f"{stats.mode(serie, keepdims=True).mode[0] if not serie.empty else '-'}",
            'Desvio Padrão': f"{serie.std():.2f}",
            'Valor máximo': f"{serie.max():.2f}",
            'Valor mínimo': f"{serie.min():.2f}"
        }

    tabela_todos = pd.DataFrame([
        {'Dado': 'Satélites', **stats_serie(satelites)},
        {'Dado': 'Hdop', **stats_serie(hdop)}
    ])
    if salvar_csv:
        tabela_todos.to_csv('Satelites/estatisticas_gps_todos.csv', index=False, encoding='utf-8-sig')

    # === TABELA 2: APENAS VÁLIDOS ===
    satelites_validos = satelites[satelites > 0]
    hdop_validos = hdop[hdop > 0]
    tabela_validos = pd.DataFrame([
        {'Dado': 'Satélites', **stats_serie(satelites_validos)},
        {'Dado': 'Hdop', **stats_serie(hdop_validos)}
    ])
    if salvar_csv:
        tabela_validos.to_csv('Satelites/estatisticas_gps_validos.csv', index=False, encoding='utf-8-sig')

    # === RESUMO ===
    resumo = pd.DataFrame([
        {'Métrica': 'Total de registros', 'Valor': total_registros},
        {'Métrica': 'Registros válidos', 'Valor': registros_validos},
        {'Métrica': '% Válidos', 'Valor': f"{perc_validos:.1f}%"}
    ])
    if salvar_csv:
        resumo.to_csv('Satelites/estatisticas_gps_resumo.csv', index=False, encoding='utf-8-sig')

    # print("✅ Arquivos de estatísticas gerados com sucesso.")
    return tabela_todos, tabela_validos, resumo

if __name__ == "__main__":
    # This part of the code will need to be updated to pass a DataFrame instead of a file path
    # For example, if you have a DataFrame 'df_example'
    # analise_medias(df_example)
    pass # Placeholder for actual DataFrame usage
