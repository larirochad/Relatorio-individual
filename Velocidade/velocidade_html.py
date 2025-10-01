import pandas as pd
from pathlib import Path
from typing import Union

def gerar_bloco_velocidade(df: pd.DataFrame, filename='bloco_velocidade.html'):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    # Filtro correto: só linhas com valor numérico válido
    absurda_numeric = pd.Series(pd.to_numeric(df['Velocidade absurda'], errors='coerce'))
    ignicao_off_numeric = pd.Series(pd.to_numeric(df['Velocidade com ignição OFF'], errors='coerce'))
    df_absurda = df[absurda_numeric.notna()].copy()
    df_ignicao_off = df[ignicao_off_numeric.notna()].copy()

    # Processa as colunas de data/hora
    df_absurda['Data'] = ''
    df_absurda['Hora'] = ''
    df_ignicao_off['Data'] = ''
    df_ignicao_off['Hora'] = ''
    
    # Extrai data e hora das strings
    for idx, row in df_absurda.iterrows():
        try:
            data_hora = str(row['Data/Hora Evento'])
            if ' ' in data_hora:
                data, hora = data_hora.split(' ', 1)
                df_absurda.at[idx, 'Data'] = data[8:10] + '/' + data[5:7]
                df_absurda.at[idx, 'Hora'] = hora[:8]
        except:
            pass
    
    for idx, row in df_ignicao_off.iterrows():
        try:
            data_hora = str(row['Data/Hora Evento'])
            if ' ' in data_hora:
                data, hora = data_hora.split(' ', 1)
                df_ignicao_off.at[idx, 'Data'] = data[8:10] + '/' + data[5:7]
                df_ignicao_off.at[idx, 'Hora'] = hora[:8]
        except:
            pass

    # Conta os totais
    total_absurda = len(df_absurda)
    total_ignicao_off = len(df_ignicao_off)

    # Verifica se há dados para cada tipo
    tem_absurda = total_absurda > 0
    tem_ignicao_off = total_ignicao_off > 0

    # CSS isolado
    css = """
    <style>
    .bloco-velocidade {
        background: #fff;
        border-radius: 30px;
        box-shadow: 0 8px 25px rgba(102, 51, 153, 0.10);
        padding: 50px 100px 60px 100px;
        max-width: 2000px;
        margin: 0 auto 40px auto;
    }
    .bloco-velocidade .dashboard-title-velocidade {
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
    .resumo-velocidade-container {
        display: flex;
        justify-content: center;
        gap: 32px;
        margin: 0 0 24px 0;
    }
    .resumo-velocidade-card {
        background: #f8f9fa;
        border-radius: 18px;
        box-shadow: 0 2px 8px rgba(102,51,153,0.07);
        padding: 18px 36px 14px 36px;
        text-align: center;
        min-width: 160px;
        font-family: Arial, Helvetica, sans-serif;
    }
    .resumo-velocidade-titulo {
        font-size: 1.1em;
        color: #222;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .resumo-velocidade-numero {
        font-size: 2em;
        font-weight: bold;
        color: #764ba2;
        margin-bottom: 2px;
    }
    .resumo-velocidade-numero.red {
        color: #dc3545;
    }
    .resumo-velocidade-legenda {
        font-size: 0.95em;
        color: #888;
    }
    .bloco-velocidade .tabela-velocidade-container {
        background: #fff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        margin-bottom: 30px;
        overflow-x: auto;
        transition: box-shadow 0.3s, transform 0.3s;
    }
    .bloco-velocidade .tabela-velocidade-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    }
    .bloco-velocidade .tabela-velocidade {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 1em;
        margin: 0 auto;
    }
    .bloco-velocidade .tabela-velocidade th, .bloco-velocidade .tabela-velocidade td {
        border: 1px solid #e9ecef;
        padding: 12px 18px;
        text-align: center;
    }
    .bloco-velocidade .tabela-velocidade th {
        background: #f8f9fa;
        color: #495057;
        font-weight: bold;
    }
    .bloco-velocidade .grafico-titulo-container {
        text-align: center;
        margin-bottom: 10px;
    }
    .bloco-velocidade .grafico-titulo {
        text-align: center;
        color: #495057;
        margin: 0;
        font-size: 1.5em;
        padding: 10px 25px;
        background: #f8f9fa;
        border-radius: 20px;
        display: inline-block;  
    }
    .Linha-link {
        color: #764ba2;
        font-weight: bold;
        text-decoration: underline;
        cursor: pointer;
        transition: color 0.2s;
    }
    .Linha-link:hover {
        color: #667eea;
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
    .botoes-graficos-container {
        display: flex;
        justify-content: center;
        gap: 16px;
        margin-bottom: 24px;
    }
    </style>
    """

    # Função para montar resumo
    def resumo_html():
        return f'''
        <div class="resumo-velocidade-container">
            <div class="resumo-velocidade-card">
                <div class="resumo-velocidade-titulo">Velocidades Absurdas</div>
                <div class="resumo-velocidade-numero red">{total_absurda}</div>
                <div class="resumo-velocidade-legenda">> 150 km/h</div>
            </div>
            <div class="resumo-velocidade-card">
                <div class="resumo-velocidade-titulo">Velocidades com Ignição OFF</div>
                <div class="resumo-velocidade-numero">{total_ignicao_off}</div>
                <div class="resumo-velocidade-legenda">Velocidade > 0 com ignição desligada</div>
            </div>
        </div>
        '''

    # Função para montar tabela
    def tabela_html(df_data, titulo, tipo_alerta, max_linhas=5):
        if tipo_alerta == 'absurda':
            col = 'Velocidade absurda'
        else:
            col = 'Velocidade com ignição OFF'
        if df_data.empty or df_data[col].apply(lambda x: pd.to_numeric(x, errors='coerce')).dropna().empty:
            return ''
        
        df_display = df_data.head(max_linhas)
        tem_mais = len(df_data) > max_linhas
        
        html = f'''
        <div class="tabela-velocidade-container">
            <div class="grafico-titulo-container">
                <h3 class="grafico-titulo">{titulo}</h3>
            </div>
            <table class="tabela-velocidade" id="tabela_{tipo_alerta}">
                <thead>
                    <tr>
                        <th>Linha</th>
                        <th>Data</th>
                        <th>Hora</th>
                        <th>Tipo de Mensagem</th>
                        <th>Motion Status</th>
                        <th>Velocidade</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for idx, row in df_display.iterrows():
            linha = row['Linha Original']
            velocidade = row['Velocidade absurda'] if tipo_alerta == 'absurda' else row['Velocidade com ignição OFF']
            if pd.isna(velocidade) or velocidade == '' or str(velocidade).lower() == 'nan':
                velocidade_str = 'N/A'
            else:
                velocidade_str = f"{velocidade} km/h"
            motion_status = row['Motion Status'] if 'Motion Status' in row else ''
            html += f'''
            <tr>
                <td>{linha}</td>
                <td>{row['Data']}</td>
                <td>{row['Hora']}</td>
                <td>{row['Tipo Mensagem']}</td>
                <td>{motion_status}</td>
                <td>{velocidade_str}</td>
            </tr>
            '''
        
        if tem_mais:
            for idx, row in df_data.iloc[max_linhas:].iterrows():
                linha = row['Linha Original']
                velocidade = row['Velocidade absurda'] if tipo_alerta == 'absurda' else row['Velocidade com ignição OFF']
                if pd.isna(velocidade) or velocidade == '' or str(velocidade).lower() == 'nan':
                    velocidade_str = 'N/A'
                else:
                    velocidade_str = f"{velocidade} km/h"
                motion_status = row['Motion Status'] if 'Motion Status' in row else ''
                html += f'''
                <tr class="linha-oculta linha-{tipo_alerta}">
                    <td>{linha}</td>
                    <td>{row['Data']}</td>
                    <td>{row['Hora']}</td>
                    <td>{row['Tipo Mensagem']}</td>
                    <td>{motion_status}</td>
                    <td>{velocidade_str}</td>
                </tr>
                '''
        
        html += '''
                </tbody>
            </table>
        '''
        
        if tem_mais:
            html += f'''
            <div style="text-align: center;">
                <button class="btn-mostrar-todos" onclick="velocidadeToggleLinhas('{tipo_alerta}', {len(df_data)})" id="btn_{tipo_alerta}" data-tabela="tabela_{tipo_alerta}">
                    Ver todos os dados
                </button>
            </div>
            '''
        
        html += '</div>'
        return html

    # Preparar dados para os gráficos
    import json

    x_absurda = df_absurda['Linha Original'].tolist() if not df_absurda.empty else []
    y_absurda = pd.to_numeric(df_absurda['Velocidade absurda'], errors='coerce').tolist() if not df_absurda.empty else []
    x_ignicao = df_ignicao_off['Linha Original'].tolist() if not df_ignicao_off.empty else []
    y_ignicao = pd.to_numeric(df_ignicao_off['Velocidade com ignição OFF'], errors='coerce').tolist() if not df_ignicao_off.empty else []

    # Criar botões baseado na disponibilidade de dados
    botoes_html = '<div style="text-align:center; margin-bottom: 24px;">'
    
    if tem_absurda and tem_ignicao_off:
        # Dois botões se tiver ambos os dados
        botoes_html += '''
            <div class="botoes-graficos-container">
                <button id="btn-grafico-absurda" class="btn-mostrar-todos" onclick="velocidadeMostrarGrafico('absurda')">Ver Gráfico de Velocidades Absurdas</button>
                <button id="btn-grafico-ignicao" class="btn-mostrar-todos" onclick="velocidadeMostrarGrafico('ignicao')">Ver Gráfico de Velocidades com Ignição OFF</button>
            </div>
        '''
    elif tem_absurda:
        # Um botão só para absurda
        botoes_html += '<button id="btn-grafico-absurda" class="btn-mostrar-todos" onclick="velocidadeMostrarGrafico(\'absurda\')">Ver Gráfico de Velocidades Absurdas</button>'
    elif tem_ignicao_off:
        # Um botão só para ignição off
        botoes_html += '<button id="btn-grafico-ignicao" class="btn-mostrar-todos" onclick="velocidadeMostrarGrafico(\'ignicao\')">Ver Gráfico de Velocidades com Ignição OFF</button>'
    
    botoes_html += '</div>'

    # Montar HTML completo
    html = f"""
    {css}
    <div class="bloco-velocidade" id="bloco-velocidade">
        <span class="dashboard-title-velocidade">Análise de Velocidade</span>
        {botoes_html}
        <div id="container-tabelas-velocidade">
            {resumo_html()}
            {tabela_html(df_absurda, "Velocidades Absurdas (>150 km/h)", "absurda")}
            {tabela_html(df_ignicao_off, "Velocidades com Ignição OFF", "ignicao_off")}
        </div>
        <div id="container-grafico-absurda" style="display:none;">
            <div style="text-align:center; margin-bottom:16px;">
                <button class="btn-mostrar-todos" onclick="velocidadeVoltarTabelas()">Voltar para Tabelas</button>
            </div>
            <div class='grafico-container'>
                <button class='btn-maximizar' onclick="velocidadeMaximizeChart('graficoAbsurda')">🔍 Maximizar</button>
                <div class='grafico-titulo-container'>
                    <h3 class='grafico-titulo'>Gráfico de Velocidades Absurdas (>150 km/h)</h3>
                </div>
                <div class='chart-wrapper'>
                    <canvas id="graficoAbsurda"></canvas>
                </div>
                <div class='zoom-controls'>
                    <button onclick="velocidadeResetZoom('graficoAbsurda')">Reset Zoom</button>
                </div>
                <div class='zoom-instruction' style='margin-top:8px; color:#666; font-size:0.8em; font-style:italic;'>
                    Use o scroll do mouse para zoom ou duplo clique para resetar
                </div>
            </div>
        </div>
        <div id="container-grafico-ignicao" style="display:none;">
            <div style="text-align:center; margin-bottom:16px;">
                <button class="btn-mostrar-todos" onclick="velocidadeVoltarTabelas()">Voltar para Tabelas</button>
            </div>
            <div class='grafico-container'>
                <button class='btn-maximizar' onclick="velocidadeMaximizeChart('graficoIgnicao')">🔍 Maximizar</button>
                <div class='grafico-titulo-container'>
                    <h3 class='grafico-titulo'>Gráfico de Velocidades com Ignição OFF</h3>
                </div>
                <div class='chart-wrapper'>
                    <canvas id="graficoIgnicao"></canvas>
                </div>
                <div class='zoom-controls'>
                    <button onclick="velocidadeResetZoom('graficoIgnicao')">Reset Zoom</button>
                </div>
                <div class='zoom-instruction' style='margin-top:8px; color:#666; font-size:0.8em; font-style:italic;'>
                    Use o scroll do mouse para zoom ou duplo clique para resetar
                </div>
            </div>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@1.2.1/dist/chartjs-plugin-zoom.min.js"></script>
    <script>
    function velocidadeToggleLinhas(tipo, total) {{
        const linhas = document.querySelectorAll('.linha-' + tipo);
        const btn = document.getElementById('btn_' + tipo);
        const todasOcultas = Array.from(linhas).every(linha => linha.classList.contains('linha-oculta'));
        linhas.forEach(linha => {{
            if (todasOcultas) {{
                linha.classList.remove('linha-oculta');
            }} else {{
                linha.classList.add('linha-oculta');
            }}
        }});
        if (todasOcultas) {{
            btn.textContent = 'Mostrar apenas 5 registros';
        }} else {{
            btn.textContent = 'Ver todos os dados';
        }}
    }}
    
    function velocidadeVoltarTabelas() {{
        document.getElementById('container-tabelas-velocidade').style.display = '';
        document.getElementById('container-grafico-absurda').style.display = 'none';
        document.getElementById('container-grafico-ignicao').style.display = 'none';
    }}
    
    function velocidadeMostrarGrafico(tipo) {{
        document.getElementById('container-tabelas-velocidade').style.display = 'none';
        
        if (tipo === 'absurda') {{
            document.getElementById('container-grafico-absurda').style.display = '';
            document.getElementById('container-grafico-ignicao').style.display = 'none';
            if (!window.charts || !window.charts['graficoAbsurda']) {{
                velocidadeRenderGraficoAbsurda();
            }}
        }} else {{
            document.getElementById('container-grafico-ignicao').style.display = '';
            document.getElementById('container-grafico-absurda').style.display = 'none';
            if (!window.charts || !window.charts['graficoIgnicao']) {{
                velocidadeRenderGraficoIgnicao();
            }}
        }}
    }}
    
    function velocidadeMaximizeChart(id) {{
        const canvas = document.getElementById(id);
        if (!canvas) return;
        if (!canvas.classList.contains('maximizado')) {{
            canvas.style.position = 'fixed';
            canvas.style.top = '50%';
            canvas.style.left = '50%';
            canvas.style.transform = 'translate(-50%, -50%) scale(1.5)';
            canvas.style.zIndex = 9999;
            canvas.style.background = '#fff';
            canvas.classList.add('maximizado');
            document.body.style.overflow = 'hidden';
            canvas.onclick = function() {{ velocidadeMaximizeChart(id); }};
        }} else {{
            canvas.style = '';
            canvas.classList.remove('maximizado');
            document.body.style.overflow = '';
            canvas.onclick = null;
        }}
    }}
    
    function velocidadeResetZoom(id) {{
        if(window.charts && window.charts[id]) {{ window.charts[id].resetZoom(); }}
    }}
    
    function velocidadeRenderGraficoAbsurda() {{
        if (typeof window.charts === 'undefined') {{ window.charts = {{}}; }}
        if (typeof Chart !== 'undefined' && Chart.register && typeof ChartZoom !== 'undefined') {{ Chart.register(ChartZoom); }}
        const ctx = document.getElementById('graficoAbsurda').getContext('2d');
        if (!window.charts['graficoAbsurda']) {{
            window.charts['graficoAbsurda'] = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(x_absurda if x_absurda else [''])},
                    datasets: [{{
                        label: 'Velocidade Absurda',
                        data: {json.dumps(y_absurda if y_absurda else [None])},
                        borderColor: 'red',
                        backgroundColor: 'rgba(220,53,69,0.08)',
                        borderWidth: 2,
                        pointRadius: 3,
                        fill: false,
                        tension: 0.2
                    }}]
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
                            title: {{ display: true, text: 'VELOCIDADE (km/h)', font: {{ size: 14, weight: 'bold', family: 'Arial' }}, color: '#000' }}
                        }},
                        x: {{
                            title: {{ display: true, text: 'LINHA DA PLANILHA', font: {{ size: 14, weight: 'bold', family: 'Arial' }}, color: '#000' }}
                        }}
                    }}
                }}
            }});
            ctx.canvas.addEventListener('dblclick', function() {{
                if(window.charts['graficoAbsurda']) {{ window.charts['graficoAbsurda'].resetZoom(); }}
            }});
        }}
    }}
    
    function velocidadeRenderGraficoIgnicao() {{
        if (typeof window.charts === 'undefined') {{ window.charts = {{}}; }}
        if (typeof Chart !== 'undefined' && Chart.register && typeof ChartZoom !== 'undefined') {{ Chart.register(ChartZoom); }}
        const ctx = document.getElementById('graficoIgnicao').getContext('2d');
        if (!window.charts['graficoIgnicao']) {{
            window.charts['graficoIgnicao'] = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(x_ignicao if x_ignicao else [''])},
                    datasets: [{{
                        label: 'Velocidade com Ignição OFF',
                        data: {json.dumps(y_ignicao if y_ignicao else [None])},
                        borderColor: 'blue',
                        backgroundColor: 'rgba(30,136,229,0.08)',
                        borderWidth: 2,
                        pointRadius: 3,
                        fill: false,
                        tension: 0.2
                    }}]
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
                            title: {{ display: true, text: 'VELOCIDADE (km/h)', font: {{ size: 14, weight: 'bold', family: 'Arial' }}, color: '#000' }}
                        }},
                        x: {{
                            title: {{ display: true, text: 'LINHA DA PLANILHA', font: {{ size: 14, weight: 'bold', family: 'Arial' }}, color: '#000' }}
                        }}
                    }}
                }}
            }});
            ctx.canvas.addEventListener('dblclick', function() {{
                if(window.charts['graficoIgnicao']) {{ window.charts['graficoIgnicao'].resetZoom(); }}
            }});
        }}
    }}
    </script>
    """

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)