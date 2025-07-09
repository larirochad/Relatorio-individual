import pandas as pd
import json
from pathlib import Path

def gerar_bloco_eventos(
    csv_totais='Analise de eventos/quantidade_tipos_mensagem.csv',
    csv_diario='Analise de eventos/quantidade_tipos_mensagem_por_dia.csv',
    filename='bloco_eventos_diarios.html'
):
    # Diretório de saída
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    # --- Lê os dados ---
    df_totais = pd.read_csv(csv_totais)
    df_diario = pd.read_csv(csv_diario)

    # --- Gráfico de barras (totais) ---
    label_map = {
        'Posicionamento por tempo em movimento': 'Temporizadas',
    }
    labels_barras = [label_map.get(lbl, lbl) for lbl in df_totais['Tipo mensagem'].tolist()]
    valores_barras = df_totais['Quantidade'].tolist()

    # Defina as cores para cada evento 
    cores_eventos = [
        "#0e0561", "#3ae8ff", "#3b08b3", "#4ff9ff", "#3c04d6",
        "#00bfff", "#2519CC", "#48d8f1", "#9370db", "#000000"
    ]
    # Repete as cores se tiver mais eventos
    background_colors = [cores_eventos[i % len(cores_eventos)] for i in range(len(labels_barras))]

    # --- Gráfico de linha (por dia) ---
    df_diario['Dia'] = pd.to_datetime(df_diario['Dia'], format='%d/%m/%Y')
    df_diario = df_diario.sort_values('Dia')
    labels_linha = df_diario['Dia'].dt.strftime('%d/%m/%Y').tolist()
    datasets_linha = []
    for idx, col in enumerate(df_diario.columns[1:]):
        label = label_map.get(col, col)
        datasets_linha.append({
            "label": label,
            "data": df_diario[col].tolist(),
            "borderColor": cores_eventos[idx % len(cores_eventos)],
            "backgroundColor": cores_eventos[idx % len(cores_eventos)],
            "fill": False,
            "tension": 0.3,
            "pointRadius": 4,
            "pointHoverRadius": 6,
            "pointBackgroundColor": cores_eventos[idx % len(cores_eventos)],
            "pointBorderColor": cores_eventos[idx % len(cores_eventos)],
            "hidden": False
        })

    # --- HTML/CSS/JS do bloco ---
    css_local = """
    <style>
    .btn-maximizar { position: absolute; top: 15px; right: 15px; padding: 8px 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 20px; cursor: pointer; font-size: 12px; font-weight: 500; z-index: 10; transition: all 0.3s ease; }
    .btn-maximizar:hover { transform: scale(1.05); }
    .grafico-container { width: 100%; max-width: 900px; background: white; padding: 25px; border-radius: 20px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); position: relative; text-align: center; border: 1px solid #e9ecef; transition: transform 0.3s ease; margin: 0 auto 40px auto;}
    .grafico-container:hover { transform: translateY(-5px); box-shadow: 0 15px 35px rgba(0,0,0,0.15);}
    .grafico-titulo-container { display: flex; justify-content: center; width: 100%; margin-bottom: 15px;}
    .grafico-titulo { text-align: center; color: #495057; margin: 0; font-size: 1.5em; padding: 10px 25px; background: #f8f9fa; border-radius: 20px; display: inline-block;}
    .chart-wrapper { position: relative; height: 400px; width: 100%; margin-bottom: 15px;}
    .zoom-controls { display: flex; justify-content: center; gap: 10px; margin: 15px 0;}
    .zoom-controls button { padding: 6px 15px; border: none; border-radius: 15px; font-size: 12px; cursor: pointer; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-weight: 500; transition: all 0.3s ease;}
    .zoom-controls button:hover { transform: translateY(-1px); opacity: 0.9;}
    .dashboard-bloco-analise {
        background: #fff;
        border-radius: 30px;
        box-shadow: 0 8px 25px rgba(102, 51, 153, 0.10);
        padding: 40px 30px 30px 30px;
        margin: 0 auto 40px auto;
        max-width: 2000px;
    }
    .dashboard-title-analise {
        font-family: 'Saira', sans-serif;
        background: linear-gradient(to right, #764ba2, #667eea);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        font-size: 2.5em;
        font-weight: 800;
        text-shadow: 2px 2px 4px rgba(102, 51, 153, 0.2);
        display: block;
        margin: 0 0 30px 0;
        text-align: center;
        padding: 0;
        border-radius: 0;
        box-shadow: none;
    }
    </style>
    """

    html = f"""{css_local}
    <!-- BLOCO DE GRÁFICO - INÍCIO -->
    <div class='dashboard-bloco-analise'>
        <span class='dashboard-title-analise'>Análise de eventos</span>
        <div class='grafico-container'>
            <button class='btn-maximizar' onclick="maximizeChart('barrasTotais')">🔍 Maximizar</button>
            <div class='grafico-titulo-container'>
                <h3 class='grafico-titulo'>Total de Eventos por Categoria</h3>
            </div>
            <div class='chart-wrapper'>
                <canvas id="barrasTotais"></canvas>
            </div>
            <div class='zoom-controls'>
                <button onclick="resetZoom('barrasTotais')">Reset Zoom</button>
            </div>
            <div class='zoom-instruction' style='margin-top:8px; color:#666; font-size:0.8em; font-style:italic;'>
                Use o scroll do mouse para zoom ou duplo clique para resetar
            </div>
        </div>
        <div class='grafico-container'>
            <button class='btn-maximizar' onclick="maximizeChart('linhaEventos')">🔍 Maximizar</button>
            <div class='grafico-titulo-container'>
                <h3 class='grafico-titulo'>Evolução Diária dos Eventos</h3>
            </div>
            <div class='chart-wrapper'>
                <canvas id="linhaEventos"></canvas>
            </div>
            <div class='zoom-controls'>
                <button onclick="resetZoom('linhaEventos')">Reset Zoom</button>
            </div>
            <div class='zoom-instruction' style='margin-top:8px; color:#666; font-size:0.8em; font-style:italic;'>
                Use o scroll do mouse para zoom ou duplo clique para resetar
            </div>
        </div>
    </div>
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        setTimeout(function() {{
            if (typeof window.charts === 'undefined') {{
                window.charts = {{}};
            }}
            if (typeof Chart !== 'undefined' && Chart.register && typeof ChartZoom !== 'undefined') {{
                Chart.register(ChartZoom);
            }}
            // Barras
            const barrasCanvas = document.getElementById('barrasTotais');
            if (barrasCanvas && !window.charts['barrasTotais']) {{
                window.charts['barrasTotais'] = new Chart(barrasCanvas.getContext('2d'), {{
                    type: 'bar',
                    data: {{
                        labels: {json.dumps(labels_barras)},
                        datasets: [{{
                            label: 'Total por categoria',
                            data: {json.dumps(valores_barras)},
                            backgroundColor: {json.dumps(background_colors)},
                            borderColor: {json.dumps(background_colors)},
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {{
                            mode: 'nearest',
                            intersect: false
                        }},
                        plugins: {{
                            legend: {{ display: false }},
                            zoom: {{
                                pan: {{ enabled: true, mode: 'xy' }},
                                zoom: {{ wheel: {{ enabled: true }}, pinch: {{ enabled: true }}, drag: {{ enabled: true }}, mode: 'xy' }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                title: {{
                                    display: true,
                                    text: 'TOTAL',
                                    font: {{ size: 14, weight: 'bold', family: 'Arial' }},
                                    color: '#000000'
                                }}
                            }},
                            x: {{
                                title: {{
                                    display: true,
                                    text: 'CATEGORIA',
                                    font: {{ size: 14, weight: 'bold', family: 'Arial' }},
                                    color: '#000000'
                                }}
                            }}
                        }}
                    }}
                }});
                barrasCanvas.addEventListener('dblclick', function() {{
                    if(window.charts['barrasTotais']) {{
                        window.charts['barrasTotais'].resetZoom();
                    }}
                }});
            }}
            // Linha
            const linhaCanvas = document.getElementById('linhaEventos');
            if (linhaCanvas && !window.charts['linhaEventos']) {{
                window.charts['linhaEventos'] = new Chart(linhaCanvas.getContext('2d'), {{
                    type: 'line',
                    data: {{
                        labels: {json.dumps(labels_linha)},
                        datasets: {json.dumps(datasets_linha)}
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {{
                            mode: 'index',
                            intersect: false
                        }},
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
                                title: {{
                                    display: true,
                                    text: 'QUANTIDADE',
                                    font: {{ size: 14, weight: 'bold', family: 'Arial' }},
                                    color: '#000000'
                                }}
                            }},
                            x: {{
                                title: {{
                                    display: true,
                                    text: 'DIAS',
                                    font: {{ size: 14, weight: 'bold', family: 'Arial' }},
                                    color: '#000000'
                                }}
                            }}
                        }}
                    }}
                }});
                linhaCanvas.addEventListener('dblclick', function() {{
                    if(window.charts['linhaEventos']) {{
                        window.charts['linhaEventos'].resetZoom();
                    }}
                }});
            }}
        }}, 100);
    }});
    </script>
    <!-- BLOCO DE GRÁFICO - FIM -->
    """

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Bloco de eventos salvo em: {output_path.resolve()}")

if __name__ == "__main__":
    gerar_bloco_eventos()
