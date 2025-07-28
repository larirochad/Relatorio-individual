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
    registros_validos = ((satelites > 0) & (hdop > 0)).sum()
    registros_invalidos = total_registros - registros_validos
    perc_invalidos = (registros_invalidos / total_registros * 100) if total_registros > 0 else 0
    perc_validos = (registros_validos / total_registros * 100) if total_registros > 0 else 0
    # === TABELA 1: TODOS OS DADOS ===
    def stats_serie(serie):
        if serie.empty:
            return {
                'Média': '0',
                'Moda': '0',
                'Desvio Padrão': '0',
                'Valor máximo': '0',
                'Valor mínimo': '0'
            }
        else:
            return {
                'Média': f"{serie.mean():.2f}",
                'Moda': f"{stats.mode(serie, keepdims=True).mode[0] if not serie.empty else 0}",
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

    # === TABELA 3: APENAS INVÁLIDOS ===
    satelites_invalidos_serie = satelites[hdop == 0]
    hdop_invalidos_serie = hdop[hdop == 0]
    tabela_invalidos = pd.DataFrame([
        {'Dado': 'Satélites', **stats_serie(satelites_invalidos_serie)},
        {'Dado': 'Hdop', **stats_serie(hdop_invalidos_serie)}
    ])
    if salvar_csv:
        tabela_invalidos.to_csv('Satelites/estatisticas_gps_invalidos.csv', index=False, encoding='utf-8-sig')

    # === NOVO: INVÁLIDOS ECO/PERIODICO ===
    # Considera inválidos apenas onde hdop == 0
    df_invalidos = df_filtrado[hdop == 0].copy()
    # motion_prefix e report_type
    def get_motion_prefix(row):
        motion = row.get('Motion Status', '')
        if isinstance(motion, (float, int)):
            if pd.notna(motion):
                motion_str = str(int(motion))
            else:
                motion_str = ''
        elif isinstance(motion, (str, bytes)):
            motion_str = str(motion)
        else:
            motion_str = ''
        return motion_str[0] if len(motion_str) > 0 else None
    def get_report_type(row):
        report_type_raw = row.get('Position Report Type', '')
        report_type = ''
        try:
            if report_type_raw is not None and str(report_type_raw).strip():
                report_type = str(int(float(str(report_type_raw))))
        except (ValueError, TypeError):
            pass
        return report_type
    def get_codigo(row):
        return str(row.get('Tipo Mensagem', '')).strip()
    def is_eco(row):
        tipo = str(row.get('Tipo Mensagem', '')).strip().upper()
        motion = str(row.get('Motion Status', '')).strip()
        motion_prefix = motion[0] if motion else ''
        return tipo == 'GTERI' and motion_prefix == '1'
    def is_periodico(row):
        motion_prefix = get_motion_prefix(row)
        report_type = get_report_type(row)
        codigo = get_codigo(row)
        return (motion_prefix == '2' and report_type == '10') or codigo == '30'

    # === NOVO: CONTAGEM TOTAL DE ECO E PERIÓDICO ===
    total_eco = df_filtrado.apply(is_eco, axis=1).sum()
    total_peri = df_filtrado.apply(is_periodico, axis=1).sum()
    resumo_modos = pd.DataFrame([
        {'Métrica': 'Total de registros modo eco', 'Valor': total_eco},
        {'Métrica': 'Total de registros modo periódico', 'Valor': total_peri}
    ])

    df_invalidos_eco = df_invalidos[df_invalidos.apply(is_eco, axis=1)]
    df_invalidos_peri = df_invalidos[df_invalidos.apply(is_periodico, axis=1)]

    tabela_invalidos_eco = pd.DataFrame([
        {'Dado': 'Satélites', **stats_serie(df_invalidos_eco['Satélites'])},
        {'Dado': 'Hdop', **stats_serie(df_invalidos_eco['Precisão GNSS'])}
    ])
    tabela_invalidos_peri = pd.DataFrame([
        {'Dado': 'Satélites', **stats_serie(df_invalidos_peri['Satélites'])},
        {'Dado': 'Hdop', **stats_serie(df_invalidos_peri['Precisão GNSS'])}
    ])

    # === RESUMO ===
    resumo = pd.DataFrame([
        {'Métrica': 'Total de registros', 'Valor': total_registros},
        {'Métrica': 'Registros válidos', 'Valor': registros_validos},
        {'Métrica': '% Válidos', 'Valor': f"{perc_validos:.1f}%"}
    ])
    if salvar_csv:
        resumo.to_csv('Satelites/estatisticas_gps_resumo.csv', index=False, encoding='utf-8-sig')

    # === RESUMOS ESPECÍFICOS ===
    resumo_eco = pd.DataFrame([
        {'Métrica': 'Total de registros inválidos eco', 'Valor': len(df_invalidos_eco)},
        {'Métrica': '% Inválidos eco', 'Valor': f"{(len(df_invalidos_eco)/total_registros*100 if total_registros else 0):.1f}%"}
    ])
    resumo_peri = pd.DataFrame([
        {'Métrica': 'Total de registros inválidos periódicos', 'Valor': len(df_invalidos_peri)},
        {'Métrica': '% Inválidos periódicos', 'Valor': f"{(len(df_invalidos_peri)/total_registros*100 if total_registros else 0):.1f}%"}
    ])

    # print("✅ Arquivos de estatísticas gerados com sucesso.")
    return tabela_todos, tabela_validos, tabela_invalidos, resumo, tabela_invalidos_eco, tabela_invalidos_peri, resumo_eco, resumo_peri, resumo_modos

if __name__ == "__main__":
    # This part of the code will need to be updated to pass a DataFrame instead of a file path
    # For example, if you have a DataFrame 'df_example'
    # analise_medias(df_example)
    pass # Placeholder for actual DataFrame usage
