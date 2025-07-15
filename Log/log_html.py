import pandas as pd
from pathlib import Path
from typing import Union

def gerar_bloco_log(df_logs: pd.DataFrame, df_estatisticas: pd.DataFrame, filename='bloco_log.html'):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    # Verificar se os DataFrames são válidos
    if not isinstance(df_logs, pd.DataFrame) or not isinstance(df_estatisticas, pd.DataFrame):
        print('❌ Inputs devem ser DataFrames.')
        return

    # Verificar se o DataFrame de estatísticas tem dados
    if df_estatisticas.empty:
        print('❌ DataFrame de estatísticas está vazio.')
        return

    # Pegar a primeira linha das estatísticas
    stats = df_estatisticas.iloc[0]
    percentual_logs = stats['Percentual_Logs_Total']
    media_delay = stats['Media_Delay_Logs']
    tipo_maior_delay = stats['Mensagem_Maior_Delay']
    maior_delay = stats['Maior_Delay_Encontrado']
    linha_maior_delay = stats['Linha_Maior_Delay']

    # Montar tabela detalhada da mensagem crítica
    tabela_critica = ''
    if not pd.isna(linha_maior_delay) and linha_maior_delay != '':
        # Encontrar a linha correspondente no df_logs
        linha_critica = df_logs[df_logs['Linha'] == linha_maior_delay]
        if not linha_critica.empty:
            row = linha_critica.iloc[0]
            data_evento = row['Data/Hora Evento']
            if pd.notnull(data_evento):
                data = pd.to_datetime(data_evento)
                data_str = data.strftime('%d/%m/%Y')
                hora_str = data.strftime('%H:%M:%S')
            else:
                data_str = ''
                hora_str = ''
            tabela_critica = f'''
            <div class="tabela-container">
                <div class="grafico-titulo-container">
                    <h3 class="grafico-titulo">Detalhes da Mensagem Crítica (Maior Delay)</h3>
                </div>
                <table class="tabela-estatisticas">
                    <thead>
                        <tr>
                            <th>Linha</th>
                            <th>Data</th>
                            <th>Hora</th>
                            <th>Tipo de mensagem</th>
                            <th>Delay (s)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>{row['Linha']}</td>
                            <td>{data_str}</td>
                            <td>{hora_str}</td>
                            <td>{row['Tipo Mensagem']}</td>
                            <td>{row['Delay']:.2f}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            '''

    # Bloco HTML
    html = f'''
    <div class="bloco-temporizadas">
        <span class="dashboard-title-temporizadas">Resumo dos Logs de Mensagens</span>
        <div class="resumo-anomalias-container" style="justify-content: center; gap: 40px;">
            <div class="resumo-anomalia-card">
                <div class="resumo-anomalia-titulo">Percentual de logs totais</div>
                <div class="resumo-anomalia-numero">{percentual_logs}</div>
                <div class="resumo-anomalia-legenda">em relação ao total de mensagens</div>
            </div>
            <div class="resumo-anomalia-card">
                <div class="resumo-anomalia-titulo">Média do tempo em delay</div>
                <div class="resumo-anomalia-numero">{media_delay}</div>
                <div class="resumo-anomalia-legenda">tempo médio de atraso</div>
            </div>
        </div>
        {tabela_critica}
    </div>
    '''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # print(f"✅ Bloco de log salvo em: {output_path.resolve()}")

if __name__ == "__main__":
    # This part of the code will now require two DataFrames to be passed.
    # For demonstration, we'll create dummy DataFrames.
    df_logs_dummy = pd.DataFrame({
        'Linha': [1, 2, 3],
        'Tipo Mensagem': ['Mensagem1', 'Mensagem2', 'Mensagem3'],
        'Data/Hora Inclusão': ['2023-01-01 10:00:00', '2023-01-01 10:01:00', '2023-01-01 10:02:00'],
        'Data/Hora Evento': ['2023-01-01 09:58:00', '2023-01-01 09:59:00', '2023-01-01 10:00:00'],
        'Delay': [120, 120, 120],
        'Log': ['Sim', 'Sim', 'Sim']
    })
    
    df_estatisticas_dummy = pd.DataFrame({
        'Tipo Mensagem': ['ESTATÍSTICAS'],
        'Percentual_Logs_Total': ['15.50%'],
        'Media_Delay_Logs': ['120.00s'],
        'Mensagem_Maior_Delay': ['Mensagem1'],
        'Maior_Delay_Encontrado': ['180.00s'],
        'Linha_Maior_Delay': [1]
    })
    
    gerar_bloco_log(df_logs_dummy, df_estatisticas_dummy)
