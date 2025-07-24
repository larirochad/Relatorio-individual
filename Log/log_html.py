import pandas as pd
from pathlib import Path
from typing import Union

def calcular_estatisticas(df_base, nome_grupo=""):
    
    if df_base is None or df_base.empty:
        return {
            'percentual_logs': '',
            'media_delay': '',
            'maior_delay': '',
            'linha_maior_delay': '',
            'tipo_maior_delay': '',
            'row_maior_delay': None
        }
    total_mensagens = len(df_base)
    df_logs = df_base[df_base['Delay'] > 60]
    total_logs = len(df_logs)
    percentual_logs = (total_logs / total_mensagens * 100) if total_mensagens > 0 else 0
    media_delay = df_logs['Delay'].mean() if total_logs > 0 else 0
    if total_logs > 0:
        max_delay_idx = df_logs['Delay'].idxmax()
        row = df_logs.loc[max_delay_idx]
        maior_delay = row['Delay']
        linha_maior_delay = row['Linha']
        tipo_maior_delay = row['Tipo Mensagem']
        row_maior_delay = row
    else:
        maior_delay = ''
        linha_maior_delay = ''
        tipo_maior_delay = ''
        row_maior_delay = None
    return {
        'percentual_logs': f"{percentual_logs:.2f}%",
        'media_delay': f"{media_delay:.2f}s",
        'maior_delay': f"{maior_delay:.2f}s" if maior_delay != '' else '',
        'linha_maior_delay': linha_maior_delay,
        'tipo_maior_delay': tipo_maior_delay,
        'row_maior_delay': row_maior_delay
    }

def tabela_maior_delay(row, titulo):
    if row is None or pd.isna(row['Linha']):
        return ''
    data_evento = row['Data/Hora Evento']
    if pd.notnull(data_evento):
        data = pd.to_datetime(data_evento)
        data_str = data.strftime('%d/%m/%Y')
        hora_str = data.strftime('%H:%M:%S')
    else:
        data_str = ''
        hora_str = ''
    return f'''
    <div class="tabela-container">
        <div class="grafico-titulo-container">
            <h3 class="grafico-titulo">{titulo}</h3>
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

def gerar_bloco_log(
    df_logs: pd.DataFrame,
    df_estatisticas: pd.DataFrame,
    df_temporizadas: pd.DataFrame = None,
    df_periodicas: pd.DataFrame = None,
    df_eco: pd.DataFrame = None,
    filename='bloco_log.html'):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    # --- CSS do Satélites ---
    css = """
    <style>
    .bloco-log {
        background: #fff;
        border-radius: 30px;
        box-shadow: 0 8px 25px rgba(102, 51, 153, 0.10);
        padding: 50px 100px 60px 100px;
        max-width: 2000px;
        margin: 0 auto 40px auto;
    }
    .dashboard-title-log {
        font-family: 'Saira', sans-serif;
        background: linear-gradient(to right, #764ba2, #667eea);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        font-size: 2.1em;
        font-weight: 800;
        text-shadow: 2px 2px 4px rgba(102, 51, 153, 0.2);
        display: block;
        margin: 0 0 30px 0;
        text-align: center;
        padding: 0;
        border-radius: 0;
        box-shadow: none;
    }
    .log-btn-container {
        display: flex;
        justify-content: center;
        gap: 16px;
        margin-bottom: 24px;
    }
    .log-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 8px 22px;
        cursor: pointer;
        font-size: 1em;
        font-weight: 500;
        font-family: 'Saira', sans-serif;
        font-weight: 700;
        box-shadow: 0 2px 8px rgba(102,51,153,0.07);
        transition: all 0.3s ease;
    }
    .log-btn.active, .log-btn:focus {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        outline: none;
    }
    .log-btn:hover {
        transform: translateY(-2px);
        opacity: 0.9;
    }
    .resumo-anomalias-container {
        display: flex;
        justify-content: center;
        gap: 32px;
        margin: 0 0 24px 0;
    }
    .resumo-anomalia-card {
        background: #f8f9fa;
        border-radius: 18px;
        box-shadow: 0 2px 8px rgba(102,51,153,0.07);
        padding: 18px 36px 14px 36px;
        text-align: center;
        min-width: 160px;
        font-family: Arial, Helvetica, sans-serif;
    }
    .resumo-anomalia-titulo {
        font-size: 1.1em;
        color: #222;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .resumo-anomalia-numero {
        font-size: 2em;
        font-weight: bold;
        color: #764ba2;
        margin-bottom: 2px;
    }
    .resumo-anomalia-numero.red {
        color: #dc3545 !important;
    }
    .resumo-anomalia-legenda {
        font-size: 0.95em;
        color: #888;
    }
    .tabela-container {
        background: #fff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        margin-bottom: 30px;
        overflow-x: auto;
        transition: box-shadow 0.3s, transform 0.3s;
    }
    .tabela-container:hover { transform: translateY(-2px); box-shadow: 0 15px 35px rgba(0,0,0,0.15); transition: box-shadow 0.3s, transform 0.3s;}
    .tabela-estatisticas {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 1em;
        margin: 0 auto;
    }
    .tabela-estatisticas th, .tabela-estatisticas td {
        border: 1px solid #e9ecef;
        padding: 12px 18px;
        text-align: center;
    }
    .tabela-estatisticas th {
        background: #f8f9fa;
        color: #495057;
        font-weight: bold;
    }
    .grafico-titulo-container {
        text-align: center;
        margin-bottom: 10px;
    }
    .grafico-titulo {
        text-align: center;
        color: #495057;
        margin: 0;
        font-size: 1.5em;
        padding: 10px 25px;
        background: #f8f9fa;
        border-radius: 20px;
        display: inline-block;  
    }
    </style>
    """

    # Estatísticas para cada grupo
    stats_todas = calcular_estatisticas(df_logs)
    stats_periodicas = calcular_estatisticas(df_periodicas)
    stats_eco = calcular_estatisticas(df_eco)

    # Cards de resumo
    def resumo_html(stats, titulo):
        return f'''
        <div class="resumo-anomalias-container">
            <div class="resumo-anomalia-card">
                <div class="resumo-anomalia-titulo">Percentual de logs</div>
                <div class="resumo-anomalia-numero">{stats['percentual_logs']}</div>
                <div class="resumo-anomalia-legenda">em relação ao total de mensagens</div>
            </div>
            <div class="resumo-anomalia-card">
                <div class="resumo-anomalia-titulo">Média do tempo em delay</div>
                <div class="resumo-anomalia-numero">{stats['media_delay']}</div>
                <div class="resumo-anomalia-legenda">tempo médio de atraso</div>
            </div>
            <div class="resumo-anomalia-card">
                <div class="resumo-anomalia-titulo">Maior delay</div>
                <div class="resumo-anomalia-numero">{stats['maior_delay']}</div>
                <div class="resumo-anomalia-legenda">Linha: {stats['linha_maior_delay']} | Tipo: {stats['tipo_maior_delay']}</div>
            </div>
        </div>
        '''

    # Tabelas de maior delay (apenas uma linha)
    tabela_todas = tabela_maior_delay(stats_todas['row_maior_delay'], "Maior Delay - Todas as mensagens")
    tabela_periodicas = tabela_maior_delay(stats_periodicas['row_maior_delay'], "Maior Delay - Periódicas")
    tabela_eco = tabela_maior_delay(stats_eco['row_maior_delay'], "Maior Delay - Modo Econômico")

    # Bloco HTML com botões e tabelas
    html = f'''
    {css}
    <div class="bloco-log" id="bloco-log">
        <span class="dashboard-title-log">Resumo dos Logs de Mensagens</span>
        <div class="log-btn-container">
            <button class="log-btn active" id="btn-todas" onclick="mostrarTabelaLog('todas')">Todas as mensagens</button>
            <button class="log-btn" id="btn-periodicas" onclick="mostrarTabelaLog('periodicas')">Periódicas</button>
            <button class="log-btn" id="btn-eco" onclick="mostrarTabelaLog('eco')">Modo Econômico</button>
        </div>
        <div id="resumo-todas" style="display:flex;">{resumo_html(stats_todas, 'Todas as mensagens')}</div>
        <div id="resumo-periodicas" style="display:none;">{resumo_html(stats_periodicas, 'Periódicas')}</div>
        <div id="resumo-eco" style="display:none;">{resumo_html(stats_eco, 'Modo Econômico')}</div>
        <div id="tabela-log-todas" style="display:block; margin-top: 20px;">
            {tabela_todas}
        </div>
        <div id="tabela-log-periodicas" style="display:none; margin-top: 20px;">
            {tabela_periodicas}
        </div>
        <div id="tabela-log-eco" style="display:none; margin-top: 20px;">
            {tabela_eco}
        </div>
        <script>
        function mostrarTabelaLog(tipo) {{
            document.getElementById('tabela-log-todas').style.display = tipo === 'todas' ? 'block' : 'none';
            document.getElementById('tabela-log-periodicas').style.display = tipo === 'periodicas' ? 'block' : 'none';
            document.getElementById('tabela-log-eco').style.display = tipo === 'eco' ? 'block' : 'none';
            document.getElementById('resumo-todas').style.display = tipo === 'todas' ? 'flex' : 'none';
            document.getElementById('resumo-periodicas').style.display = tipo === 'periodicas' ? 'flex' : 'none';
            document.getElementById('resumo-eco').style.display = tipo === 'eco' ? 'flex' : 'none';
            document.getElementById('btn-todas').classList.toggle('active', tipo === 'todas');
            document.getElementById('btn-periodicas').classList.toggle('active', tipo === 'periodicas');
            document.getElementById('btn-eco').classList.toggle('active', tipo === 'eco');
        }}
        // Inicialmente mostra todas
        mostrarTabelaLog('todas');
        </script>
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
