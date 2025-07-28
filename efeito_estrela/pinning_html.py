import pandas as pd
import json
from pathlib import Path
from typing import Union
import numpy as np

def gerar_bloco_pinning(df_inc: pd.DataFrame, df_blocos: pd.DataFrame = None, filename='bloco_pinning.html'):
    # Caminhos
    base_dir = Path(__file__).parent.parent
    if df_blocos is None:
        csv_blocos = base_dir / 'efeito_estrela' / 'distancia_blocos.csv'
    else:
        csv_blocos = df_blocos
    output_path = base_dir / 'temp_blocos' / filename

    # Lê os DataFrames ou CSVs
    if isinstance(csv_blocos, pd.DataFrame):
        blocos = csv_blocos.copy()
    else:
        blocos = pd.read_csv(csv_blocos)

    # Corrigir nome da coluna de distância para o nome correto do CSV
    dist_col = 'Distância incremental (m)'
    linha_col = 'linha' if 'linha' in blocos.columns else 'Linha'

    # --- Tabela 2: todos com incremento > 0 (usada para gráfico e tabela)
    blocos_nonzero = blocos[blocos[dist_col] > 0]

    # Garantir que o gráfico use apenas motion = 21
    if 'Motion Status' in blocos.columns:
        blocos_motion21 = blocos[blocos['Motion Status'] == 21]
        blocos_nonzero = blocos_motion21[blocos_motion21[dist_col] > 0]

    # --- Tabela 2: todos com incremento > 40 (usada para gráfico e tabela)
    blocos_maior_40 = blocos[blocos[dist_col] > 40]

    # Primeira tabela: motion = 21 e distância > 40m
    tabela1_df = blocos[(blocos['Motion Status'] == 21) & (blocos[dist_col] > 40)]
    # Segunda tabela: incremento de hodômetro, independente da distância
    tabela2_df = df_inc[df_inc['Hodômetro anterior'] != df_inc['Hodômetro Total']]

    # --- Dados para gráfico (usar blocos_nonzero)
    if not isinstance(blocos_nonzero, pd.DataFrame):
        blocos_nonzero = pd.DataFrame({linha_col: [], dist_col: []})
    x_raw = blocos_nonzero[linha_col] if linha_col in blocos_nonzero.columns else pd.Series([], dtype=int)
    y_raw = blocos_nonzero[dist_col] if dist_col in blocos_nonzero.columns else pd.Series([], dtype=float)
    x = [int(v) for v in x_raw.tolist()] if not x_raw.empty else [0]
    y = [float(v) for v in y_raw.tolist()] if not y_raw.empty else [0]
    if not (x and x[0] == 0 and y[0] == 0):
        x = [0] + x
        y = [0] + y
    else:
        x = [0]
        y = [0]

    def make_table(df, titulo, legenda, tipo, max_linhas=5):
        table_id = f"tabela_{tipo}"
        # Limita a 5 linhas inicialmente
        df_display = df.head(max_linhas)
        tem_mais = len(df) > max_linhas
        # Novo cabeçalho de exibição
        display_headers = [
            "Linha",
            "Hodômetro antes da parada",
            "Hodômetro com status parado",
            "Tipo de mensagem",
            "Motion Status",
            "Distância até detecção de parada (m)"
        ]
        # Mapeamento dos nomes de exibição para os nomes das colunas do DataFrame
        data_columns = [
            linha_col,
            'Hodômetro anterior',
            'Hodômetro Total',
            'Tipo Mensagem',
            'Motion Status',
            dist_col
        ]
        html = f'''
        <div class="tabela-container">
            <div class="grafico-titulo-container">
                <h3 class="grafico-titulo">{titulo}</h3>
            </div>
            <div class="faixa-legenda">{legenda}</div>
            <table class="tabela-estatisticas" id="{table_id}">
                <thead><tr>{''.join(f'<th>{header}</th>' for header in display_headers)}</tr></thead>
                <tbody>
        '''
        if df.empty:
            html += f'<tr><td colspan="{len(display_headers)}">Nenhum dado encontrado</td></tr>'
        else:
            for _, row in df_display.iterrows():
                html += '<tr>'
                for col in data_columns:
                    val = row.get(col, "")
                    if col == dist_col and val != "":
                        try:
                            val = f"{float(val):.2f}"
                        except Exception:
                            pass
                    html += f'<td>{val}</td>'
                html += '</tr>'
            # Linhas extras ocultas
            if tem_mais:
                for _, row in df.iloc[max_linhas:].iterrows():
                    html += '<tr class="linha-extra" data-tabela="tabela_' + tipo + '" style="display:none;">'
                    for col in data_columns:
                        val = row.get(col, "")
                        if col == dist_col and val != "":
                            try:
                                val = f"{float(val):.2f}"
                            except Exception:
                                pass
                        html += f'<td>{val}</td>'
                    html += '</tr>'
        html += '</tbody></table>'
        if tem_mais and not df.empty:
            html += f'''
            <div style="text-align: center;">
                <button class="btn-mostrar-todos" data-tabela="tabela_{tipo}">Ver todos os dados</button>
            </div>
            '''
        html += '</div>'
        return html

    # Tabela 1: motion = 21 e distância > 40m
    table1 = make_table(
        tabela1_df,
        'Mensagens com Motion = 21 e Distância > 40m',
        'Inclui todas as mensagens com Motion Status igual a 21 e distância incremental maior que 40 metros.',
        'motion21_40m'
    )
    # Tabela 2: incremento de hodômetro
    table2 = make_table(
        tabela2_df,
        'Mensagens com incremento de hodômetro',
        'Inclui todas as mensagens que tiveram qualquer incremento de hodômetro, independente da distância.',
        'incremento_hodo'
    )

    # --- Card resumo ---
    acima_40 = blocos_nonzero[blocos_nonzero[dist_col] > 40]
    if not acima_40.empty:
        dist_series = pd.Series(list(acima_40[dist_col]))
        soma_uniq = dist_series.drop_duplicates().sum()
        card_valor = f"{soma_uniq:.2f} m"
        card_legenda = "Soma dos valores únicos acima de 40m"
    else:
        card_valor = "0 m"
        card_legenda = "Nenhum incremento acima de 40m encontrado"
    card = f'''
    <div class="resumo-anomalias-container">
      <div class="resumo-anomalia-card">
        <div class="resumo-anomalia-titulo">Soma dos incrementos únicos &gt; 40m</div>
        <div class="resumo-anomalia-numero">{card_valor}</div>
        <div class="resumo-anomalia-legenda">{card_legenda}</div>
      </div>
    </div>
    '''

    # --- Novo Card: Soma dos incrementos de hodômetro parado ---
    # Considera apenas linhas onde Hodômetro Total > Hodômetro anterior
    if 'Hodômetro Total' in blocos.columns and 'Hodômetro anterior' in blocos.columns:
        df_incremento_parado = blocos[(blocos['Hodômetro Total'] > blocos['Hodômetro anterior'])].copy()
        soma_incremento_parado = (df_incremento_parado['Hodômetro Total'] - df_incremento_parado['Hodômetro anterior']).sum()
        # Se os valores estiverem em metros, converta para km se necessário. Aqui mantemos como está, mas pode ajustar a unidade se quiser.
        card_incremento_parado = f'''
        <div class="resumo-anomalias-container">
          <div class="resumo-anomalia-card" style="background:#f8f9fa;">
            <div class="resumo-anomalia-titulo">Soma dos incrementos de hodômetro parado</div>
            <div class="resumo-anomalia-numero">{soma_incremento_parado:.2f} km</div>
            <div class="resumo-anomalia-legenda">Total de hodômetro incrementado enquanto status era parado</div>
          </div>
        </div>
        '''
    else:
        card_incremento_parado = ''

    # --- Cards lado a lado ---
    cards_html = f'''
    <div style="display: flex; gap: 30px; justify-content: center; margin-bottom: 30px;">
      {card}
      {card_incremento_parado}
    </div>
    '''

    # --- CSS ---
    css = '''
    <style>
    .bloco-pinning {
        background: #fff;
        border-radius: 30px;
        box-shadow: 0 8px 25px rgba(102, 51, 153, 0.10);
        padding: 50px 100px 60px 100px;
        max-width: 2000px;
        margin: 0 auto 40px auto;
    }
    .dashboard-title-analise {
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
    .tabela-container {
        background: #fff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        margin-bottom: 30px;
        overflow-x: auto;
        transition: box-shadow 0.3s, transform 0.3s;
    }
    .tabela-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    }
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
    .faixa-legenda {
        text-align: center;
        font-size: 14px;
        color: #898989;
        margin-bottom: 18px;
        background: #f8f9fa;
        font-weight: 500;
        border-radius: 10px;
        padding: 10px;
        margin-top: 8px;
    }
    .btn-mostrar-todos {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 8px 22px;
        cursor: pointer;
        font-size: 1em;
        font-weight: 500;
        margin-top: 15px;
        transition: all 0.3s ease;
        font-family: 'Saira', sans-serif;
        font-weight: 700;
        box-shadow: 0 2px 8px rgba(102,51,153,0.07);
    }
    .btn-mostrar-todos:hover {
        transform: translateY(-2px);
        opacity: 0.9;
    }
    .linha-oculta {
        display: none;
    }
    /* Gráfico Chart.js igual bloco_eventos */
    .grafico-container { width: 100%; max-width: 900px; background: white; padding: 25px; border-radius: 20px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); position: relative; text-align: center; border: 1px solid #e9ecef; transition: transform 0.3s ease; margin: 0 auto 40px auto;}
    .grafico-container:hover { transform: translateY(-2px); box-shadow: 0 15px 35px rgba(0,0,0,0.15); transition: box-shadow 0.3s, transform 0.3s;}
    .chart-wrapper { position: relative; height: 400px; width: 100%; margin-bottom: 15px;}
    .btn-maximizar { position: absolute; top: 15px; right: 15px; padding: 8px 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 20px; cursor: pointer; font-size: 12px; font-weight: 500; z-index: 10; transition: all 0.3s ease; }
    .btn-maximizar:hover { transform: scale(1.05); }
    .zoom-controls { display: flex; justify-content: center; gap: 10px; margin: 15px 0;}
    .zoom-controls button { padding: 6px 15px; border: none; border-radius: 15px; font-size: 12px; cursor: pointer; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-weight: 500; transition: all 0.3s ease;}
    .zoom-controls button:hover { transform: translateY(-2px); opacity: 0.9;}
    </style>
    '''

    # --- HTML ---
    html = f'''
    {css}
    <div class="bloco-pinning" id="bloco-pinning">
        <span class="dashboard-title-analise">Análise de Pinning (Distância Incremental)</span>
        {cards_html}
        <div class='grafico-container'>
            <button class='btn-maximizar' onclick="maximizeChart('graficoPinning')">🔍 Maximizar</button>
            <div class='grafico-titulo-container'>
                <h3 class='grafico-titulo'>Gráfico de todas as distâncias com motion = 21 </h3>
            </div>
            <div class='chart-wrapper'>
                <canvas id="graficoPinning"></canvas>
            </div>
            <div class='zoom-controls'>
                <button onclick="resetZoom('graficoPinning')">Reset Zoom</button>
            </div>
            <div class='zoom-instruction' style='margin-top:8px; color:#666; font-size:0.8em; font-style:italic;'>
                Use o scroll do mouse para zoom ou duplo clique para resetar
            </div>
        </div>
        {table1}
        {table2}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@1.2.1/dist/chartjs-plugin-zoom.min.js"></script>
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        setTimeout(function() {{
            if (typeof window.charts === 'undefined') {{ window.charts = {{}}; }}
            if (typeof Chart !== 'undefined' && Chart.register && typeof ChartZoom !== 'undefined') {{ Chart.register(ChartZoom); }}
            const ctx = document.getElementById('graficoPinning').getContext('2d');
            if (!window.charts['graficoPinning']) {{
                window.charts['graficoPinning'] = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: {json.dumps(x)},
                        datasets: [
                            {{
                                label: 'Distância Incremental',
                                data: {json.dumps(y)},
                                borderColor: 'blue',
                                backgroundColor: 'rgba(30, 136, 229, 0.08)',
                                borderWidth: 2,
                                pointRadius: 2,
                                fill: false,
                                tension: 0.2
                            }},
                            {{
                                label: 'Limite 40m',
                                data: Array({len(x)}).fill(40),
                                borderColor: 'red',
                                borderWidth: 2,
                                borderDash: [8,6],
                                pointRadius: 0,
                                fill: false,
                                tension: 0
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {{ mode: 'nearest', intersect: false }},
                        plugins: {{
                            legend: {{ position: 'top' }},
                            zoom: {{
                                pan: {{ enabled: true, mode: 'xy' }},
                                zoom: {{ wheel: {{ enabled: true }}, pinch: {{ enabled: true }}, drag: {{ enabled: true }}, mode: 'xy' }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                title: {{ display: true, text: 'DISTÂNCIA ENTRE OS PONTOS(m)', font: {{ size: 14, weight: 'bold', family: 'Arial' }}, color: '#000' }}
                            }},
                            x: {{
                                title: {{ display: true, text: 'LINHA DA PLANILHA ', font: {{ size: 14, weight: 'bold', family: 'Arial' }}, color: '#000' }}
                            }}
                        }}
                    }}
                }});
                ctx.canvas.addEventListener('dblclick', function() {{
                    if(window.charts['graficoPinning']) {{ window.charts['graficoPinning'].resetZoom(); }}
                }});
            }}
        }}, 100);
    }});
    </script>
    '''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

# Fim da função. Nenhuma execução automática fora dela.
