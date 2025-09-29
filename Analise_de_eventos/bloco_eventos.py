import pandas as pd
import json
from pathlib import Path
from typing import Union

def gerar_bloco_eventos(df: pd.DataFrame, df_diario: pd.DataFrame = None, filename='bloco_eventos_diarios.html'):
    if 'Tipo mensagem' in df.columns:
        tipo_msg = df['Tipo mensagem'].str.strip()
        mask = (~tipo_msg.isin(['HBD', 'ACK'])) & (~tipo_msg.str.startswith('AT', na=False))
        df = df[mask].copy()

    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    if df_diario is None:
        df_diario = df.copy()

    label_map = {
        'Posicionamento por tempo em movimento': 'Temporizadas',
    }
    labels_barras = [label_map.get(lbl, lbl) for lbl in df['Tipo mensagem'].tolist()]
    valores_barras = df['Quantidade'].tolist()

    # Criar dados para a tabela
    dados_tabela = []
    for i, (tipo, quantidade) in enumerate(zip(labels_barras, valores_barras)):
        dados_tabela.append({
            'tipo': tipo,
            'quantidade': quantidade
        })

    cores_eventos = [
        "#BDB76B", "#DAA520", "#708090", "#0000FF", "#836FFF",
        "#191970", "#4B0082", "#FF1493", "#7FFFD4", "#66c7ff", "#1C1C1C",  "#808000", "#A020F0", 	"#87CEEB","	#BC8F8F"
    ]
    background_colors = [cores_eventos[i % len(cores_eventos)] for i in range(len(labels_barras))]

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

    labels_json = json.dumps(labels_linha)
    datasets_json = json.dumps(datasets_linha)
    labels_barras_json = json.dumps(labels_barras)
    valores_barras_json = json.dumps(valores_barras)
    cores_barras_json = json.dumps(background_colors)
    dados_tabela_json = json.dumps(dados_tabela)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-zoom/1.2.1/chartjs-plugin-zoom.min.js"></script>
        </head>
        <body>
        <style>
        .btn-maximizar {{ position: absolute; top: 15px; right: 15px; padding: 8px 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 20px; cursor: pointer; font-size: 12px; font-weight: 500; z-index: 10; transition: all 0.3s ease; }}
        .btn-maximizar:hover {{ transform: scale(1.05); }}
        .grafico-container {{ width: 100%; max-width: 900px; background: white; padding: 25px; border-radius: 20px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); position: relative; text-align: center; border: 1px solid #e9ecef; transition: transform 0.3s ease; margin: 0 auto 40px auto; }}
        .grafico-container:hover {{ transform: translateY(-2px); box-shadow: 0 15px 35px rgba(0,0,0,0.15); }}
        .grafico-titulo-container {{ display: flex; justify-content: center; width: 100%; margin-bottom: 15px; }}
        .grafico-titulo {{ text-align: center; color: #495057; margin: 0; font-size: 1.5em; padding: 10px 25px; background: #f8f9fa; border-radius: 20px; display: inline-block; }}
        .chart-wrapper {{ position: relative; height: 400px; width: 100%; margin-bottom: 15px; }}
        .zoom-controls {{ display: flex; justify-content: center; gap: 10px; margin: 15px 0; }}
        .zoom-controls button {{ padding: 6px 15px; border: none; border-radius: 15px; font-size: 12px; cursor: pointer; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-weight: 500; transition: all 0.3s ease; }}
        .zoom-controls button:hover {{ transform: translateY(-2px); opacity: 0.9; }}
        .dashboard-bloco-analise {{ background: #fff; border-radius: 30px; box-shadow: 0 8px 25px rgba(102, 51, 153, 0.10); padding: 40px 30px 30px 30px; margin: 0 auto 40px auto; max-width: 2000px; }}
        .dashboard-title-analise {{ font-family: 'Saira', sans-serif; background: linear-gradient(to right, #764ba2, #667eea); -webkit-background-clip: text; background-clip: text; color: transparent; font-size: 2.5em; font-weight: 800; text-shadow: 2px 2px 4px rgba(102, 51, 153, 0.2); display: block; margin: 0 0 30px 0; text-align: center; padding: 0; border-radius: 0; box-shadow: none; }}
        .legend-controls {{ display: flex; justify-content: center; gap: 10px; margin: 10px 0; }}
        .legend-controls button {{ padding: 6px 15px; border: none; border-radius: 15px; font-size: 12px; cursor: pointer; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-weight: 500; transition: all 0.3s ease; }}
        .legend-controls button:hover {{ transform: translateY(-1px); opacity: 0.9; }}
        
        .linha-oculta {{
            display: none;
        }}
        
        /* Estilos para os botões de alternância */
        .botoes-alternancia {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 20px; }}
        .btn-alternancia {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            border: none; 
            border-radius: 12px; 
            padding: 8px 22px; 
            cursor: pointer; 
            font-size: 15px; 
            margin: 3px 15px; 
            transition: all 0.3s ease; 
            font-family: 'Saira', sans-serif; 
            font-weight: 700; 
            box-shadow: 0px 8px rgba(102, 51, 153, 0.07); 
        }}
        .btn-alternancia.ativo {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            transform: translateY(2px);
            box-shadow: 0px 4px rgba(102, 51, 153, 0.07); 
        }}
        .btn-alternancia.inativo {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            transform: translateY(0px);
            box-shadow: 0px 8px rgba(102, 51, 153, 0.07); 
        }}
        .btn-alternancia:hover {{ 
            transform: translateY(1px);
            box-shadow: 0px 6px rgba(102, 51, 153, 0.07); 
        }}
        
        .btn-mostrar-todos {{
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
        }}
        .btn-mostrar-todos:hover {{
            transform: translateY(-2px);
            opacity: 0.9;
        }}
        
        /* Estilos para a tabela */
        .tabela-container {{
            background: #fff;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            margin: 0 auto 40px auto;
            max-width: 900px;
            overflow-x: auto;
            transition: box-shadow 0.3s, transform 0.3s;
        }}
        .tabela-container:hover {{
            transform: translateY(-2px); 
            box-shadow: 0 15px 35px rgba(0,0,0,0.15); 
            transition: box-shadow 0.3s, transform 0.3s;
        }}
        .tabela-eventos {{
            width: 100%; 
            border-collapse: collapse; 
            font-family: Arial, Helvetica, sans-serif; 
            font-size: 1em; 
            margin: 0 auto; 
        }}
        .tabela-eventos th, .tabela-eventos td {{ 
            border: 1px solid #e9ecef; 
            padding: 12px 18px; 
            text-align: center; 
        }}
        .tabela-eventos th {{ 
            background: #f8f9fa; 
            color: #495057; 
            font-weight: bold; 
        }}

        /* Estilos para modo maximizado */
        .maximized-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: white;
            z-index: 10000;
            display: none;
            flex-direction: column;
        }}
        
        .maximized-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .maximized-title {{
            font-size: 1.8em;
            font-weight: 600;
            color: #495057;
            margin: 0;
        }}
        
        .maximized-controls {{
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .maximized-controls button {{
            padding: 10px 18px;
            border: none;
            border-radius: 12px;
            font-size: 13px;
            cursor: pointer;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 500;
            transition: all 0.3s ease;
            white-space: nowrap;
        }}
        
        .maximized-controls button:hover {{
            transform: translateY(-2px);
            opacity: 0.9;
        }}
        
        .btn-fechar-max {{
            background: #dc3545 !important;
            padding: 12px 20px !important;
            font-weight: 600 !important;
        }}
        
        .btn-fechar-max:hover {{
            background: #c82333 !important;
        }}
        
        .maximized-canvas-container {{
            flex: 1;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
        }}
        
        .maximized-canvas-container canvas {{
            max-width: 100%;
            max-height: 100%;
        }}

        /* Ocultar controles originais quando maximizado */
        .chart-maximized .btn-maximizar,
        .chart-maximized .zoom-controls,
        .chart-maximized .legend-controls {{
            display: none !important;
        }}
        </style>

        <div class='dashboard-bloco-analise' id='bloco-eventos'>
            <span class='dashboard-title-analise'>Análise de eventos</span>

            <!-- Botões de alternância -->
            <div class='botoes-alternancia'>
                <button id='btn-tabela' class='btn-alternancia ativo' onclick="mostrarTabela()">Visualizar em Tabela</button>
                <button id='btn-grafico' class='btn-alternancia inativo' onclick="mostrarGrafico()">Visualizar em Gráfico</button>
            </div>

            <!-- Container da Tabela -->
            <div id='container-tabela' class='tabela-container'>
                <div class='grafico-titulo-container'>
                    <h3 class='grafico-titulo'>Total de Eventos por Categoria</h3>
                </div>
                <table class='tabela-eventos' id='tabela-eventos'>
                    <thead>
                        <tr>
                            <th>Tipo de Evento</th>
                            <th>Quantidade</th>
                        </tr>
                    </thead>
                    <tbody id='tbody-eventos'>
                        <!-- Dados serão inseridos via JavaScript -->
                    </tbody>
                </table>
                <div id='btn-ver-todos-container' style='text-align: center; display: none;'>
                    <button class='btn-mostrar-todos' data-tabela='tabela-eventos' onclick="toggleLinhasUniversal('tabela-eventos')">
                        Ver todos os dados
                    </button>
                </div>
            </div>

            <!-- Container do Gráfico de Barras -->
            <div id='container-grafico' class='grafico-container' style='display: none;'>
                <button class='btn-maximizar' onclick="maximizeChart('barrasTotais', 'Total de Eventos por Categoria')">🔍 Maximizar</button>
                <div class='grafico-titulo-container'>
                    <h3 class='grafico-titulo'>Total de Eventos por Categoria</h3>
                </div>
                <div class='chart-wrapper'><canvas id="barrasTotais"></canvas></div>
                <div class='zoom-controls'><button onclick="resetZoom('barrasTotais')">Reset Zoom</button></div>
            </div>

            <!-- Gráfico de Evolução Diária (sempre visível) -->
            <div id='container-linha' class='grafico-container'>
                <button class='btn-maximizar' onclick="maximizeChart('linhaEventos', 'Evolução Diária dos Eventos')">🔍 Maximizar</button>
                <div class='grafico-titulo-container'>
                    <h3 class='grafico-titulo'>Evolução Diária dos Eventos</h3>
                </div>
                <div class='chart-wrapper'><canvas id="linhaEventos"></canvas></div>
                <div class='zoom-controls'><button onclick="resetZoom('linhaEventos')">Reset Zoom</button></div>
                <div class='legend-controls'>
                    <button onclick="mostrarTodos('linhaEventos')">Mostrar Todos</button>
                    <button onclick="ocultarTodos('linhaEventos')">Ocultar Todos</button>
                </div>
            </div>
        </div>

        <!-- Overlay para modo maximizado -->
        <div id="maximized-overlay" class="maximized-overlay">
            <div class="maximized-header">
                <h2 id="maximized-title" class="maximized-title">Gráfico Maximizado</h2>
                <div class="maximized-controls">
                    <button onclick="resetZoomMaximized()">🔄 Reset Zoom</button>
                    <div id="legend-controls-maximized" style="display: none;">
                        <button onclick="mostrarTodosMaximized()">👁️ Mostrar Todos</button>
                        <button onclick="ocultarTodosMaximized()">🚫 Ocultar Todos</button>
                    </div>
                    <button class="btn-fechar-max" onclick="closeMaximized()">✕ Fechar</button>
                </div>
            </div>
            <div class="maximized-canvas-container">
                <canvas id="maximized-canvas"></canvas>
            </div>
        </div>

        <script>
        // Registro do plugin de zoom
        Chart.register(ChartZoom);
        
        let controleFiltros = {{ filtroAtivo: null, estadoOriginal: {{}}, estadoIndividual: {{}}, estadoMostrarTodos: false, estadoOcultarTodos: false }};
        const dadosTabela = {dados_tabela_json};
        let currentMaximizedChart = null;
        let maximizedChart = null;
        window.charts = {{}};

        // Função GLOBAL para toggle de linhas (DEVE estar no escopo global)
        window.toggleLinhasUniversal = function(tabelaId) {{
            console.log('toggleLinhasUniversal chamada com:', tabelaId);
            
            const tabela = document.getElementById(tabelaId);
            const btn = document.querySelector(`[data-tabela="${{tabelaId}}"]`);
            
            console.log('Tabela encontrada:', tabela);
            console.log('Botão encontrado:', btn);
            
            if (!tabela || !btn) {{
                console.error('Tabela ou botão não encontrado:', tabelaId);
                return;
            }}
            
            const linhas = tabela.querySelectorAll('.linha-extra-eventos');
            console.log('Linhas encontradas:', linhas.length);
            
            if (!linhas.length) {{
                console.error('Nenhuma linha extra encontrada');
                return;
            }}
            
            const todasOcultas = Array.from(linhas).every(linha => 
                linha.classList.contains('linha-oculta'));
            
            console.log('Todas ocultas?', todasOcultas);
            
            linhas.forEach(linha => {{
                if (todasOcultas) {{
                    linha.classList.remove('linha-oculta');
                }} else {{
                    linha.classList.add('linha-oculta');
                }}
            }});
            
            // Atualiza texto do botão
            btn.textContent = todasOcultas ? 'Mostrar apenas 5 registros' : 'Ver todos os dados';
            
            // Scroll suave para a tabela
            const y = tabela.getBoundingClientRect().top + window.scrollY - 80;
            window.scrollTo({{ top: y, behavior: 'smooth' }});
        }};

        // Funções GLOBAIS para alternar entre tabela e gráfico
        window.mostrarTabela = function() {{
            console.log('mostrarTabela() chamada');
            document.getElementById('container-tabela').style.display = 'block';
            document.getElementById('container-grafico').style.display = 'none';
            document.getElementById('btn-tabela').className = 'btn-alternancia ativo';
            document.getElementById('btn-grafico').className = 'btn-alternancia inativo';
        }};

        window.mostrarGrafico = function() {{
            console.log('mostrarGrafico() chamada');
            document.getElementById('container-tabela').style.display = 'none';
            document.getElementById('container-grafico').style.display = 'block';
            document.getElementById('btn-tabela').className = 'btn-alternancia inativo';
            document.getElementById('btn-grafico').className = 'btn-alternancia ativo';
        }}

        // Função para popular a tabela
        function popularTabela() {{
            console.log('popularTabela() chamada');
            console.log('Dados da tabela:', dadosTabela);
            
            const tbody = document.getElementById('tbody-eventos');
            const btnContainer = document.getElementById('btn-ver-todos-container');
            tbody.innerHTML = '';
            
            const maxLinhas = 5;
            dadosTabela.forEach((item, index) => {{
                const row = tbody.insertRow();
                const cellTipo = row.insertCell(0);
                const cellQuantidade = row.insertCell(1);
                cellTipo.textContent = item.tipo;
                cellQuantidade.textContent = item.quantidade;
                
                // Adiciona classe para linhas ocultas
                if (index >= maxLinhas) {{
                    row.classList.add('linha-oculta', 'linha-extra-eventos');
                    console.log('Linha', index, 'marcada como oculta');
                }}
            }});
            
            // Mostra botão apenas se houver mais de 5 registros
            if (dadosTabela.length > maxLinhas) {{
                btnContainer.style.display = 'block';
                console.log('Botão Ver todos os dados exibido');
            }} else {{
                console.log('Menos de 5 registros, botão não será exibido');
            }}
        }}

        // Inicialização
        document.addEventListener('DOMContentLoaded', function() {{
            // Popular a tabela
            popularTabela();
            
            // Criar gráfico de linha
            const linhaCanvas = document.getElementById('linhaEventos');
            if (linhaCanvas) {{
                window.charts['linhaEventos'] = new Chart(linhaCanvas.getContext('2d'), {{
                    type: 'line',
                    data: {{ labels: {labels_json}, datasets: {datasets_json} }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {{ mode: 'index', intersect: false }},
                        plugins: {{
                            legend: {{ position: 'top' }},
                            zoom: {{
                                pan: {{ enabled: true, mode: 'xy', scaleMode: 'xy' }},
                                zoom: {{
                                    wheel: {{ enabled: true, speed: 0.1 }},
                                    pinch: {{ enabled: true }},
                                    drag: {{ enabled: true }},
                                    mode: 'xy',
                                    scaleMode: 'xy'
                                }}
                            }},
                            tooltip: {{
                                callbacks: {{
                                    label: function(context) {{
                                        let label = context.dataset.label || '';
                                        let value = context.parsed.y;
                                        return label + ': ' + value;
                                    }}
                                }}
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
                inicializarControle('linhaEventos');
            }}

            // Criar gráfico de barras
            const barrasCanvas = document.getElementById('barrasTotais');
            if (barrasCanvas) {{
                window.charts['barrasTotais'] = new Chart(barrasCanvas.getContext('2d'), {{
                    type: 'bar',
                    data: {{
                        labels: {labels_barras_json},
                        datasets: [{{
                            label: 'Total por categoria',
                            data: {valores_barras_json},
                            backgroundColor: {cores_barras_json},
                            borderColor: {cores_barras_json},
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{ display: false }},
                            zoom: {{
                                pan: {{ enabled: true, mode: 'xy', scaleMode: 'xy' }},
                                zoom: {{
                                    wheel: {{ enabled: true, speed: 0.1 }},
                                    pinch: {{ enabled: true }},
                                    drag: {{ enabled: true }},
                                    mode: 'xy',
                                    scaleMode: 'xy'
                                }}
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
            }}
        }});

        function inicializarControle(chartId) {{
            const chart = window.charts[chartId];
            if (!chart) return;
            controleFiltros.estadoOriginal[chartId] = {{}};
            controleFiltros.estadoIndividual[chartId] = {{}};
            chart.data.datasets.forEach((dataset, index) => {{
                controleFiltros.estadoOriginal[chartId][index] = !dataset.hidden;
                controleFiltros.estadoIndividual[chartId][dataset.label] = !dataset.hidden;
            }});
        }}

        window.mostrarTodos = function(chartId) {{
            const chart = window.charts[chartId];
            if (!chart) return;
            chart.data.datasets.forEach((dataset, idx) => {{
                dataset.hidden = false;
            }});
            chart.update();
        }};

        window.ocultarTodos = function(chartId) {{
            const chart = window.charts[chartId];
            if (!chart) return;
            chart.data.datasets.forEach((dataset, idx) => {{
                dataset.hidden = true;
            }});
            chart.update();
        }};

        window.resetZoom = function(chartId) {{
            const chart = window.charts[chartId];
            if (chart && chart.resetZoom) {{
                chart.resetZoom();
            }}
        }};

        // Funções para modo maximizado
        window.maximizeChart = function(chartId, title) {{
            const originalChart = window.charts[chartId];
            if (!originalChart) return;
            
            currentMaximizedChart = chartId;
            const overlay = document.getElementById('maximized-overlay');
            const titleElement = document.getElementById('maximized-title');
            const legendControls = document.getElementById('legend-controls-maximized');
            
            titleElement.textContent = title;
            overlay.style.display = 'flex';
            
            // Mostrar controles de legenda apenas para gráfico de linha
            if (chartId === 'linhaEventos') {{
                legendControls.style.display = 'flex';
            }} else {{
                legendControls.style.display = 'none';
            }}
            
            // Adicionar classe para ocultar controles originais
            const container = document.getElementById(chartId === 'linhaEventos' ? 'container-linha' : 'container-grafico');
            if (container) {{
                container.classList.add('chart-maximized');
            }}
            
            // Criar novo gráfico no canvas maximizado
            const maximizedCanvas = document.getElementById('maximized-canvas');
            const ctx = maximizedCanvas.getContext('2d');
            
            // Limpar canvas anterior se existir
            if (maximizedChart) {{
                maximizedChart.destroy();
            }}
            
            // Copiar configuração do gráfico original
            const config = JSON.parse(JSON.stringify(originalChart.config));
            config.options.responsive = true;
            config.options.maintainAspectRatio = false;
            
            maximizedChart = new Chart(ctx, config);
        }}

        window.closeMaximized = function() {{
            const overlay = document.getElementById('maximized-overlay');
            overlay.style.display = 'none';
            
            // Remover classe dos controles originais
            const containers = document.querySelectorAll('.chart-maximized');
            containers.forEach(container => {{
                container.classList.remove('chart-maximized');
            }});
            
            if (maximizedChart) {{
                maximizedChart.destroy();
                maximizedChart = null;
            }}
            currentMaximizedChart = null;
        }};

        window.resetZoomMaximized = function() {{
            if (maximizedChart && maximizedChart.resetZoom) {{
                maximizedChart.resetZoom();
            }}
        }};

        window.mostrarTodosMaximized = function() {{
            if (!maximizedChart || currentMaximizedChart !== 'linhaEventos') return;
            
            maximizedChart.data.datasets.forEach((dataset) => {{
                dataset.hidden = false;
            }});
            maximizedChart.update();
            
            // Sincronizar com gráfico original
            window.mostrarTodos(currentMaximizedChart);
        }};

        window.ocultarTodosMaximized = function() {{
            if (!maximizedChart || currentMaximizedChart !== 'linhaEventos') return;
            
            maximizedChart.data.datasets.forEach((dataset) => {{
                dataset.hidden = true;
            }});
            maximizedChart.update();
            
            // Sincronizar com gráfico original
            ocultarTodos(currentMaximizedChart);
        }}

        // Fechar com ESC
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape' && currentMaximizedChart) {{
                closeMaximized();
            }}
        }});
        </script>
        </body>
        </html>
        """)

if __name__ == "__main__":
    pass