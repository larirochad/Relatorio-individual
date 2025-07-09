import os
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

def analise_medias(caminho_arquivo):
    codificacoes = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    for encoding in codificacoes:
        try:
            df = pd.read_csv(caminho_arquivo, encoding=encoding, low_memory=False)
            break
        except UnicodeDecodeError:
            continue
    else:
        print("Erro: Não foi possível ler o arquivo com as codificações testadas.")
        return None

    df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
    df['Satélites'] = pd.to_numeric(df['Satélites'], errors='coerce')
    df['Precisão GNSS'] = pd.to_numeric(df['Precisão GNSS'], errors='coerce')

    df_filtrado = df.dropna(subset=['Data/Hora Evento', 'Satélites', 'Precisão GNSS'])

    coluna_dia = df_filtrado['Data/Hora Evento']
    satelites = df_filtrado['Satélites']
    hdop = df_filtrado['Precisão GNSS']

    # Calcular totais e válidos/invalidos separadamente para Satélites e HDOP
    total_registros_satelites = len(satelites)
    total_registros_hdop = len(hdop)
    satelites_invalidos = (satelites == 0).sum()
    hdop_invalidos = (hdop == 0).sum()
    registros_validos_satelites = (satelites > 0).sum()
    registros_validos_hdop = (hdop > 0).sum()

    print(f"=== RESUMO DOS DADOS ===")
    print(f"Total de registros: {total_registros_satelites}")
    print(f"Satélites inválidos (zeros): {satelites_invalidos} ({satelites_invalidos/total_registros_satelites*100:.2f}%)")
    print(f"HDOP inválidos (zeros): {hdop_invalidos} ({hdop_invalidos/total_registros_hdop*100:.2f}%)")

    # === ANÁLISE 1: CONSIDERANDO TODOS OS DADOS (INCLUINDO ZEROS) ===
    print(f"\n=== ANÁLISE 1: TODOS OS DADOS (INCLUINDO INVÁLIDOS) ===")
    
    # Estatísticas dos Satélites (todos os dados)
    media_todos = satelites.mean()
    moda_todos = stats.mode(satelites, keepdims=True).mode[0]
    desvio_padrao_todos = satelites.std()
    minimo_todos = satelites.min()
    maximo_todos = satelites.max()

    print(f"Satélites - Média: {media_todos:.2f}, Moda: {moda_todos}, Desvio: {desvio_padrao_todos:.2f}, Min: {minimo_todos}, Max: {maximo_todos}")

    # Estatísticas do HDOP (todos os dados)
    media_hdop_todos = hdop.mean()
    moda_hdop_todos = stats.mode(hdop, keepdims=True).mode[0]
    desvio_padrao_hdop_todos = hdop.std()
    minimo_hdop_todos = hdop.min()
    maximo_hdop_todos = hdop.max()

    print(f"HDOP - Média: {media_hdop_todos:.2f}, Moda: {moda_hdop_todos}, Desvio: {desvio_padrao_hdop_todos:.2f}, Min: {minimo_hdop_todos}, Max: {maximo_hdop_todos}")

    # === ANÁLISE 2: DESCONSIDERANDO DADOS INVÁLIDOS (ZEROS) ===
    print(f"\n=== ANÁLISE 2: DADOS VÁLIDOS (EXCLUINDO INVÁLIDOS) ===")
    
    # Filtrar dados válidos (excluindo zeros)
    satelites_validos = satelites[satelites > 0]
    hdop_validos = hdop[hdop > 0]
    
    registros_validos = len(satelites_validos)
    print(f"Registros válidos: {registros_validos} ({registros_validos/total_registros_satelites*100:.2f}%)")

    # Estatísticas dos Satélites (dados válidos)
    media_validos = satelites_validos.mean()
    moda_validos = stats.mode(satelites_validos, keepdims=True).mode[0]
    desvio_padrao_validos = satelites_validos.std()
    minimo_validos = satelites_validos.min()
    maximo_validos = satelites_validos.max()

    print(f"Satélites - Média: {media_validos:.2f}, Moda: {moda_validos}, Desvio: {desvio_padrao_validos:.2f}, Min: {minimo_validos}, Max: {maximo_validos}")

    # Estatísticas do HDOP (dados válidos)
    media_hdop_validos = hdop_validos.mean()
    moda_hdop_validos = stats.mode(hdop_validos, keepdims=True).mode[0]
    desvio_padrao_hdop_validos = hdop_validos.std()
    minimo_hdop_validos = hdop_validos.min()
    maximo_hdop_validos = hdop_validos.max()

    print(f"HDOP - Média: {media_hdop_validos:.2f}, Moda: {moda_hdop_validos}, Desvio: {desvio_padrao_hdop_validos:.2f}, Min: {minimo_hdop_validos}, Max: {maximo_hdop_validos}")

    # === SALVAR CSV COM DADOS DO GRÁFICO ===
    df_resultado = pd.DataFrame({
        'Data_Hora_Evento': coluna_dia.values,
        'Numero_Satelites': satelites.values,
        'HDOP': hdop.values
    })
    df_resultado.to_csv('Satelites/grafico_satelites.csv', index=False, encoding='utf-8-sig')
    # print(f"\n✅ Arquivo 'grafico_satelites.csv' gerado com sucesso.")

    # === SALVAR ESTATÍSTICAS EM CSV ===
    # Criar DataFrame com formato solicitado: Métrica | Satélites | HDOP
    df_estatisticas_formato = pd.DataFrame({
        'Métrica': [
            'Média (com válidos)',
            'Moda (com válidos)', 
            'Desvio Padrão (com válidos)',
            'Mínimo (com válidos)',
            'Máximo (com válidos)',
            'Média (todos os dados)',
            'Moda (todos os dados)',
            'Desvio Padrão (todos os dados)', 
            'Mínimo (todos os dados)',
            'Máximo (todos os dados)'
        ],
        'Satélites': [
            media_validos,
            moda_validos,
            desvio_padrao_validos,
            minimo_validos,
            maximo_validos,
            media_todos,
            moda_todos,
            desvio_padrao_todos,
            minimo_todos,
            maximo_todos
        ],
        'HDOP': [
            media_hdop_validos,
            moda_hdop_validos,
            desvio_padrao_hdop_validos,
            minimo_hdop_validos,
            maximo_hdop_validos,
            media_hdop_todos,
            moda_hdop_todos,
            desvio_padrao_hdop_todos,
            minimo_hdop_todos,
            maximo_hdop_todos
        ]
    })
    
    # Adicionar informações de contagem no final
    df_contagem = pd.DataFrame({
        'Métrica': [
            'Total de registros',
            'Registros inválidos (zeros)',
            'Registros válidos',
            'Percentual de inválidos (%)'
        ],
        'Satélites': [
            total_registros_satelites,
            satelites_invalidos,
            registros_validos_satelites,
            satelites_invalidos/total_registros_satelites*100 if total_registros_satelites > 0 else 0
        ],
        'HDOP': [
            total_registros_hdop,
            hdop_invalidos,
            registros_validos_hdop,
            hdop_invalidos/total_registros_hdop*100 if total_registros_hdop > 0 else 0
        ]
    })
    
    # Combinar as duas tabelas
    df_estatisticas_final = pd.concat([df_estatisticas_formato, df_contagem], ignore_index=True)
    df_estatisticas_final.to_csv('Satelites/estatisticas_gps.csv', index=False, encoding='utf-8-sig')
    print("✅ Arquivo 'estatisticas_gps.csv' gerado com sucesso.")

if __name__ == "__main__":
    analise_medias('logs/analise_par09.csv')
