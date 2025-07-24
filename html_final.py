import os
import re
from pathlib import Path
import pandas as pd
import json
import traceback


def extract_css_from_blocks(blocks):
    inline_css = []
    css_links = set()
    cleaned_blocks = []

    for block in blocks:
        # Extract inline styles
        styles = re.findall(r'<style.*?>(.*?)</style>', block, flags=re.DOTALL)
        inline_css.extend(styles)

        # Extract external stylesheets
        links = re.findall(r'<link.*?rel=["\']stylesheet["\'].*?>', block, flags=re.DOTALL)
        css_links.update(links)

        # Remove CSS from block
        clean_block = re.sub(r'<style.*?>.*?</style>', '', block, flags=re.DOTALL)
        clean_block = re.sub(r'<link.*?rel=["\']stylesheet["\'].*?>', '', clean_block, flags=re.DOTALL)
        cleaned_blocks.append(clean_block)

    return inline_css, css_links, cleaned_blocks

def extract_and_consolidate_scripts(blocks):
    scripts = []
    cleaned_blocks = []
    global_vars_patterns = [
        r'let\s+maximizedChartInstance\s*=\s*null\s*;',
        r'window\.charts\s*=\s*\{\s*\}\s*;',
        r'let\s+charts\s*=\s*window\.charts\s*;',
        r'window\.chartStates\s*=\s*\{\s*\}\s*;',
        r'let\s+chartStates\s*=\s*window\.chartStates\s*;',
    ]

    for block in blocks:
        # Extract all scripts from block
        found_scripts = re.findall(r'<script.*?>(.*?)</script>', block, flags=re.DOTALL)

        for script in found_scripts:
            # Remove duplicate global variables
            clean_script = script
            for pattern in global_vars_patterns:
                clean_script = re.sub(pattern, '', clean_script, flags=re.MULTILINE)
            scripts.append(clean_script.strip())

        # Remove all scripts from original block
        clean_block = re.sub(r'<script.*?>.*?</script>', '', block, flags=re.DOTALL)
        cleaned_blocks.append(clean_block)

    # Combine all remaining scripts into one
    final_script_block = ""
    if scripts:
        final_script_block = "<script>\n" + "\n\n".join(scripts) + "\n</script>\n"

    return final_script_block, cleaned_blocks

def get_device_info(df):
    """
    Extrai informações do dispositivo do DataFrame
    Args:
        df: DataFrame com dados do dispositivo
    Returns:
        dict com informações do dispositivo
    """
    if df is None or df.empty:
        return {
            'tipo_dispositivo': 'N/A',
            'imei': 'N/A',
            'versao_firmware': 'N/A'
        }
    # Mapeamento de tipos de dispositivo
    tipo_mapping = {
        '802003': 'TM-10',
        '385349': 'TM-08',
        '83': 'TM-07'
    }
    # Extrair tipo de dispositivo
    tipo_dispositivo = 'N/A'
    if 'Tipo Dispositivo' in df.columns:
        tipos_unicos = df['Tipo Dispositivo'].dropna().unique()
        if len(tipos_unicos) > 0:
            try:
                tipo_int = int(float(tipos_unicos[0])) 
                tipo_raw = str(tipo_int)
            except:
                tipo_raw = str(tipos_unicos[0])  # fallback
            tipo_dispositivo = tipo_mapping.get(tipo_raw, f"Desconhecido ({tipo_raw})")
    # Extrair IMEI
    imei = 'N/A'
    if 'IMEI' in df.columns:
        imeis_unicos = df['IMEI'].dropna().unique()
        if len(imeis_unicos) > 0:
            imei = ', '.join([
                str(int(float(i))) if isinstance(i, (str, float, int)) and str(i).replace('.', '', 1).isdigit()
                else str(i)
                for i in imeis_unicos
            ])
    # Extrair Versão Firmware
    versao_firmware = 'N/A'
    if 'Versão Firmware' in df.columns:
        versoes_unicas = df['Versão Firmware'].dropna().unique()
        if len(versoes_unicas) > 0:
            hex_str = str(versoes_unicas[0]).lower().replace('0x', '')
            hex_str = hex_str.zfill(4)
            major_hex = hex_str[:2]
            minor_hex = hex_str[2:4]
            # Converte cada parte para decimal
            versao_firmware_1 = int(major_hex, 16)
            versao_firmware_2 = int(minor_hex, 16)
            versao_firmware = f"{versao_firmware_1}.{versao_firmware_2}"
    return {
        'tipo_dispositivo': tipo_dispositivo,
        'imei': imei,
        'versao_firmware': versao_firmware
    }

def create_device_summary_html(df_raw):
    device = get_device_info(df_raw)
    num_registros = len(df_raw) if df_raw is not None else 0
    html = f"""
    <div class="tabela-resumo-tecnico">
    <div class="grafico-container">
        <div class='grafico-titulo-container'>
            <h2 class='grafico-titulo'>Resumo Técnico do Equipamento</h2>
        </div>
        <table style='width: 100%; border-collapse: collapse; margin: 20px auto; font-size: 14px;'>
            <thead>
                <tr style='background-color: #f8f9fa; border-bottom: 2px solid #dee2e6;'>
                    <th style='padding: 22px;  border: 1px solid #dee2e6; font-weight: bold; color: #495057;'>Nome Comercial</th>
                    <th style='padding: 22px;  border: 1px solid #dee2e6; font-weight: bold; color: #495057;'>IMEI</th>
                    <th style='padding: 22px;  border: 1px solid #dee2e6; font-weight: bold; color: #495057;'>Versão Firmware</th>
                    <th style='padding: 22px;  border: 1px solid #dee2e6; font-weight: bold; color: #495057;'>Quantidade de dados analisados</th>
                </tr>
            </thead>
            <tbody>
                <tr style='border-bottom: 1px solid #dee2e6;'>
                    <td style='padding: 22px; border: 1px solid #dee2e6; font-weight: bold; font-size: 16px;'>{device['tipo_dispositivo']}</td>
                    <td style='padding: 22px; border: 1px solid #dee2e6; font-weight: bold; font-size: 16px; font-family: monospace;'>{device['imei']}</td>
                    <td style='padding: 22px; border: 1px solid #dee2e6; font-weight: bold; font-size: 16px; font-family: monospace;'>{device['versao_firmware']}</td>
                    <td style='padding: 22px; border: 1px solid #dee2e6; font-weight: bold; font-size: 16px; font-family: monospace;'>{num_registros}</td>
                </tr>
            </tbody>
        </table>
    </div>
    </div>
    """
    return html



def unir_blocos(df_raw):
    blocks_dir = Path(__file__).parent / "temp_blocos"
    output_file = Path(__file__).parent / "dashboard_final.html"
    
    if not os.path.exists(blocks_dir):
        # print(f"Error: Directory '{blocks_dir}' not found!")
        return
    
    #Define manual order of files
    html_files = [
        str(blocks_dir / "bloco_hodometro.html"),
        str(blocks_dir / "bloco_eventos_diarios.html"),
        str(blocks_dir / "bloco_ignicao.html"),
        str(blocks_dir / "bloco_log.html"),
        str(blocks_dir / "bloco_reboot.html"),
        str(blocks_dir / "bloco_satelites.html"),
        str(blocks_dir / "bloco_sequenceNumber.html"),
        str(blocks_dir / "bloco_temporizadas.html"),
        str(blocks_dir / "bloco_pinning.html"),
        str(blocks_dir / "bloco_timefix.html"),
        str(blocks_dir / "bloco_velocidade.html"),  
        str(blocks_dir / "bloco_smp_eco.html"),
        str(blocks_dir / "bloco_gap.html"),
    ]
    
    # html_files = sorted([str(f) for f in blocks_dir.glob('*.html')])

    if not html_files:
        # print(f"Error: No HTML files found in '{blocks_dir}'!")
        return

    # Global CSS - Adicionei os novos estilos para a logo e título
    global_css =  """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #f8f9fa;
        min-height: 100vh;
        padding: 20px;
    }
    
    .dashboard-container { 
        max-width: 1200px;
        margin: 0 auto;
    }
    .logo-container {
        text-align: center; 
        margin-bottom: 40px; 
    }

    .logo-wrapper {
        background-color: #e6e6fa;
        border-radius: 50px;
        box-shadow: 0 4px 20px rgba(102, 51, 153, 0.2);
        padding: 30px 100px;
        margin: 0 auto;
        
        display: block;
        max-width: 90%;    
        width: 90%;
    }
        
    .logo-image {
        max-width: 350px;
        height: auto;
    }
    
    .dashboard-title {
        font-family: 'Saira', sans-serif;
        background: linear-gradient(135deg, #e6e6fa 0%, #d8bfd8 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        font-size: 2.5em;
        font-weight: 800;
        text-shadow: 2px 2px 4px rgba(102, 51, 153, 0.2);
        display: inline-block;
        padding: 15px 30px;

        
        border-radius: 20px;
        box-shadow: 0 6px 20px rgba(102, 51, 153, 0.15);
        margin: 0 0 30px 0;
        text-align: center;
    }
    
    .grafico-container { 
        width: 100%; 
        max-width: 900px;   
        background: white; 
        padding: 25px; 
        border-radius: 20px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1); 
        position: relative; 
        text-align: center;
        border: 1px solid #e9ecef;
        transition: transform 0.3s ease;
        margin: 0 auto 40px auto;
    }
    
    .grafico-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        transition: box-shadow 0.3s, transform 0.3s;
    }



    .grafico-titulo-container {
        display: flex;
        justify-content: center;
        width: 100%;
        margin-bottom: 15px;
    }
    
    .grafico-titulo {
        text-align: center;
        color: #495057;
        margin: 0;
        font-size: 1.8em; 
        padding: 10px 25px;
        background: #f8f9fa;
        border-radius: 20px;
        display: inline-block;
    }
    
    .chart-wrapper {
        position: relative;
        height: 600px;
        width: 100%;
        margin-bottom: 15px;
    }
    
    canvas { 
        width: 100% !important; 
        height: 100% !important; 
    }
    
    .zoom-controls {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin: 15px 0;
    }
    
    .zoom-controls button {
        padding: 6px 15px;
        border: none;
        border-radius: 15px;
        font-size: 12px;
        cursor: pointer;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .zoom-controls button:hover {
        transform: translateY(-2px);
        opacity: 0.9;
    }
    
    .btn-maximizar {
        position: relative;
        top: 15px;
        right: 15px;
        padding: 8px 15px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 20px;
        cursor: pointer;
        font-size: 12px;
        font-weight: 500;
        z-index: 10;
        transition: all 0.3s ease;
    }
    
    .btn-maximizar:hover {
        transform: scale(1.05);
    }

    /* Modal para gráfico maximizado */
    .modal {
        display: none;
        position: fixed;
        z-index: 1000;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.8);
        backdrop-filter: blur(5px);
    }

    .modal-content {
        background: white;
        margin: 2% auto;
        padding: 30px;
        border-radius: 20px;
        width: 90%;
        max-width: 95vw;
        max-height: 90vh;
        overflow: auto;
    }

    .close-modal {
        color: #aaa;
        font-size: 28px;
        font-weight: bold;
        cursor: pointer;
        float: right;
    }

    .modal-chart-container {
        width: 100%;
        height: 70vh;
        position: relative;
        margin-top: 20px;
    }

    .modal-titulo {
        margin: 0 0 20px 0;
        font-size: 1.5em;
        color: #333;
        text-align: center;
    }
    
    .legend-controls {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin-top: 10px;
    }
    .grafico-container h4 {
        margin-bottom: 8px;
    }

    .grafico-container div {
        margin-top: 4px;
    }

    .tabela-resumo-tecnico {
        background: #fff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        overflow-x: auto;
    }
    .tabela-resumo-tecnico:hover {
        will-change: box-shadow;
        transform: none !important;
    }

    .grafico-hodometro:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
        transition: box-shadow 0.3s, transform 0.3s;
    }


    """

    # Global JavaScript
    global_js = """
        // Global variables
        window.charts = window.charts || {};
        let charts = window.charts;
        let maximizedChartInstance = null;

        // Function to maximize charts
        function maximizeChart(chartId) {
            const originalChart = charts[chartId];
            if (!originalChart) return console.error('Chart not found:', chartId);
            
            const modal = document.getElementById('maximizedModal');
            const modalTitle = document.getElementById('modalTitle');
            
            // Update modal title
            modalTitle.textContent = document.querySelector('#' + chartId).closest('.grafico-container').querySelector('.grafico-titulo').textContent;
            
            modal.style.display = 'block';
            
            const ctx = document.getElementById('maximizedChart').getContext('2d');
            if (maximizedChartInstance) maximizedChartInstance.destroy();
            
            // Create copy of data maintaining current visibility
            const chartData = JSON.parse(JSON.stringify(originalChart.data));
            
            maximizedChartInstance = new Chart(ctx, {
                type: originalChart.config.type,
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'nearest', intersect: false },
                    plugins: {
                        legend: { display: true, position: 'top' },
                        zoom: {
                            pan: {
                                enabled: true,
                                mode: 'xy'
                            },
                            zoom: {
                                wheel: {
                                    enabled: true,
                                    speed: 0.1
                                },
                                pinch: {
                                    enabled: true
                                },
                                drag: {
                                    enabled: true,
                                    backgroundColor: 'rgba(225,225,225,0.3)',
                                    borderWidth: 2
                                },
                                mode: 'xy'
                            }
                        }
                    },
                    scales: originalChart.options.scales
                }
            });

            // Sync dataset visibility
            originalChart.data.datasets.forEach((dataset, index) => {
                const isVisible = originalChart.getDatasetMeta(index).visible !== false;
                maximizedChartInstance.setDatasetVisibility(index, isVisible);
            });
            maximizedChartInstance.update();
            
            // Add double click event to reset zoom
            const maximizedCanvas = document.getElementById('maximizedChart');
            maximizedCanvas.addEventListener('dblclick', function() {
                if (maximizedChartInstance) {
                    maximizedChartInstance.resetZoom();
                }
            });
        }

        // Function to close modal
        function closeModal() {
            const modal = document.getElementById('maximizedModal');
            if (modal) {
                modal.style.display = 'none';
            }
            
            if (maximizedChartInstance) {
                maximizedChartInstance.destroy();
                maximizedChartInstance = null;
            }
        }
        
        // Function to reset zoom
        function resetZoom(chartId) {
            const chart = charts[chartId];
            if (chart && chart.resetZoom) {
                chart.resetZoom();
            }
        }
        """

    # HTML footer with modal and global JS
    html_footer = f"""
        </div>

        <div id="maximizedModal" class="modal">
            <div class="modal-content">
                <span class="close-modal" onclick="closeModal()">&times;</span>
                <h2 class="modal-titulo" id="modalTitle">Maximized Chart</h2>
                    <div class="modal-chart-container">
                        <canvas id="maximizedChart"></canvas>
                        <div class="zoom-controls">
                            <button onclick="if (maximizedChartInstance) maximizedChartInstance.resetZoom();">Reset Zoom</button>
                        </div>
                    </div>
            </div>
        </div>

        <button id="fabMinimizar" class="btn-mostrar-todos" style="display:none; position: fixed; bottom: 40px; right: 40px; z-index: 9999;">Mostrar menos</button>
        <script>
        // Botão flutuante global
        const fabMinimizar = document.getElementById('fabMinimizar');
        let tabelaExpandida = null;
        // Função para mostrar o botão flutuante quando uma tabela é expandida
        function mostrarFabMinimizar(tabelaId) {{
          tabelaExpandida = tabelaId;
          fabMinimizar.style.display = 'block';
        }}
        // Função para esconder o botão flutuante
        function esconderFabMinimizar() {{
          tabelaExpandida = null;
          fabMinimizar.style.display = 'none';
        }}
        // Ao clicar no botão flutuante, minimiza a tabela expandida
        fabMinimizar.onclick = function() {{
          if (!tabelaExpandida) return;
          // Procura o botão de "Ver todos os dados" correspondente e clica nele para minimizar
          const btn = document.querySelector(`[data-tabela="${{tabelaExpandida}}"]`);
          if (btn) btn.click();
          esconderFabMinimizar();
          // Scroll para o topo da tabela minimizada
          const tabela = document.getElementById(tabelaExpandida);
          if (tabela) {{
            const y = tabela.getBoundingClientRect().top + window.scrollY - 80;
            window.scrollTo({{ top: y, behavior: 'smooth' }});
          }}
        }};
        // Observa cliques nos botões "Ver todos os dados" para mostrar/esconder o botão flutuante
        document.addEventListener('click', function(e) {{
          if (e.target.classList.contains('btn-mostrar-todos')) {{
            const tabelaId = e.target.getAttribute('data-tabela');
            if (e.target.textContent.includes('Mostrar apenas') || e.target.textContent.includes('menos')) {{
              mostrarFabMinimizar(tabelaId);
              // --- NOVO: Scroll para o topo do bloco ao minimizar ---
              setTimeout(function() {{
                const tabela = document.getElementById(tabelaId);
                if (tabela) {{
                  const y = tabela.getBoundingClientRect().top + window.scrollY - 80;
                  window.scrollTo({{ top: y, behavior: 'smooth' }});
                }}
              }}, 200);
            }} else {{
              esconderFabMinimizar();
            }}
          }}
        }});
        </script>
        <script>{global_js}</script>
        
        <script>
        // Initialize events when DOM is loaded
        document.addEventListener('DOMContentLoaded', function() {{
            // Close modal when clicking outside
            window.onclick = function(event) {{
                const modal = document.getElementById('maximizedModal');
                if (event.target === modal) {{
                    closeModal();
                }}
            }};
            
            // Close modal with ESC key
            document.addEventListener('keydown', function(event) {{
                if (event.key === 'Escape') {{
                    closeModal();
                }}
            }});
        }});
        </script>
    </body>
    </html>"""

    # Read and include blocks
    blocks = []
    for file in html_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    blocks.append(f"<!-- Block: {os.path.basename(file)} -->\n{content}\n")
        except FileNotFoundError:
            # print(f"Warning: File '{file}' not found. Skipping...")
            pass

    # Process blocks
    inline_css, css_links, blocks_without_css = extract_css_from_blocks(blocks)
    global_scripts, clean_blocks = extract_and_consolidate_scripts(blocks_without_css)

    # Adicionar ids nos principais blocos
    def add_id_to_block(block, block_id):
        # Adiciona id na primeira div com classe correspondente
        import re
        return re.sub(r'<div class=(["\"])' + block_id + r'(["\"])', r'<div class=\1' + block_id + r'\2 id=\"' + block_id + '\"', block, count=1)

    block_id_map = {
        'bloco_hodometro': 'bloco-hodometro',
        'bloco_pinning': 'bloco-pinning',
        'bloco_reboot': 'bloco-reboot',
        'bloco_velocidade': 'bloco-velocidade',
        'bloco_sequenceNumber': 'bloco-sequenceNumber',
        'bloco_timefix': 'bloco-timefix',
        'bloco_ignicao': 'bloco-ignicao',
        'bloco_smp_eco': 'bloco-smp-eco',
        'bloco_gap': 'bloco-gap',
                
    }
    clean_blocks_with_ids = []
    for block in clean_blocks:
        for class_name, block_id in block_id_map.items():
            if f'class="{class_name}"' in block:
                block = add_id_to_block(block, class_name)
                block = block.replace(f'class="{class_name}"', f'class="{class_name}" id="{block_id}"')
        clean_blocks_with_ids.append(block)

    PNG_FILE = Path(__file__).parent / "logo-golfleet-cor.png"

        
    # HTML header
    html_header = f"""<!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard Individual</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.1/dist/chartjs-plugin-zoom.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Saira:wght@600;700;800&display=swap" rel="stylesheet">

        <!-- Global CSS -->
        <style>{global_css}</style>

        <!-- Inline CSS from blocks -->
        <style>
        {"\n".join(inline_css)}
        </style>
        <style>
        /* Floating navigation menu lateral retraído */
        #floating-nav-wrapper {{
            position: fixed;
            top: 30px;
            left: 0;
            z-index: 9999;
            /* Ajuste para cobrir toda a área do menu lateral */
            min-height: 600px; /* ajuste conforme necessário para cobrir o menu todo */
            width: 260px;      /* igual ou maior que o menu + botão */
            background: transparent; /* permite que o mouse "pegue" o wrapper */
        }}
        #floating-nav-toggle {{
            background: #fff;
            border-radius: 0 18px 18px 0;
            box-shadow: 0 4px 16px rgba(102,51,153,0.13);
            width: 36px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: background 0.2s;
            position: absolute;
            left: 0;
            top: 0;
        }}
        #floating-nav-toggle:hover {{
            background: #e6e6fa;
        }}
        #floating-nav {{
            position: absolute;
            left: -220px; /* Escondido por padrão */
            top: 0;
            min-width: 180px;
            background: #fff;
            border-radius: 0 18px 18px 0;
            box-shadow: 0 4px 16px rgba(102,51,153,0.13);
            padding: 12px 18px;
            font-family: 'Saira', sans-serif;
            transition: left 0.3s;
            opacity: 0.98;
            /* Removido pointer-events: none; para permitir interação no espaço branco */
        }}
        #floating-nav-wrapper:hover #floating-nav,
        #floating-nav-wrapper.open #floating-nav {{
            left: 36px; /* Mostra o menu */
            /* pointer-events: auto; removido pois não é mais necessário */
        }}
        #floating-nav .nav-title {{
            font-weight: bold;
            color: #764ba2;
            margin-bottom: 8px;
            font-size: 1.1em;
        }}
        #floating-nav button {{
            display: block;
            width: 100%;
            margin: 6px 0;
            padding: 8px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            border: none;
            border-radius: 10px;
            font-size: 1em;
            font-family: 'Saira', sans-serif;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s, transform 0.2s;
        }}
        #floating-nav button:hover {{        
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
            transform: translateY(-2px) scale(1.03);
        }}
        @media (max-width: 700px) {{
            #floating-nav-wrapper {{ left: 0; top: 5px; min-height: 0; width: 140px; }}
            #floating-nav {{ min-width: 120px; padding: 6px 6px; }}
            #floating-nav button {{font-size: 0.9em; padding: 6px 0; }}
        }}
        /* Botão flutuante Análises L2 */
        .btn-flutuante-l2 {{
            position: fixed;
            top: 30px;
            right: 40px;
            z-index: 99999;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            font-weight: 600;
            border: none;
            border-radius: 12px;
            padding: 10px 24px;
            font-size: 1em;
            box-shadow: 0 2px 8px rgba(102,51,153,0.07);
            cursor: pointer;
            transition: background 0.2s, transform 0.2s;
            font-family: Arial, Helvetica, sans-serif;
        }}
        .btn-flutuante-l2:hover {{
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
            color: #fff;
            transform: translateY(-2px) scale(1.03);
        }}
        </style>
    </head>
    <body>
        <button id="btn-analises-l2" class="btn-flutuante-l2" onclick="showAnalisesL2()">Análises L2</button>
        <button id="btn-analises-gerais" class="btn-flutuante-l2" style="display:none;" onclick="showAnalisesGerais()">Análises gerais</button>
        <div id="floating-nav-wrapper">
            <div id="floating-nav-toggle">
                <!-- Seta SVG roxa -->
                <svg width="36" height="36" viewBox="0 0 36 36">
                    <polyline points="12,8 24,18 12,28" fill="none" stroke="#764ba2" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div id="floating-nav">
                <div class="nav-title">Ir para bloco:</div>
                <button onclick="scrollToBloco('bloco-resumo-tecnico')">Resumo Técnico</button>
                <button onclick="scrollToBloco('bloco-hodometro')">Hodômetro</button>
                <button onclick="scrollToBloco('bloco-eventos')">Eventos</button>
                <button onclick="scrollToBloco('bloco-ignicao')">Tempo de Ignição</button>
                <button onclick="scrollToBloco('bloco-log')">Log</button>
                <button onclick="scrollToBloco('bloco-reboot')">Reboot</button>
                <button onclick="scrollToBloco('bloco-satelites')">Satélites</button>
                <button onclick="scrollToBloco('bloco-sequenceNumber')">Sequence Number</button>
                <button onclick="scrollToBloco('bloco-temporizadas')">Temporizadas</button>
                <button onclick="scrollToBloco('bloco-pinning')">Pinning</button>
                <button onclick="scrollToBloco('bloco-timefix')">Time Fix</button>
                <button onclick="scrollToBloco('bloco-velocidade')">Velocidade</button>
            </div>
        </div>
        <div class='dashboard-container'>
            <!-- Logo com fundo roxo -->
            <div class="logo-container">
                <div class="logo-wrapper">
                        <img src="https://conteudo.golfleet.com.br/wp-content/uploads/2022/03/Logo-principal-2.png" alt="" class="logo-image">
                </div>
            </div>
            <!-- Título preto com emoji colorido -->
            <div style="text-align: center; width: 100%;">
                <h1 class="dashboard-title" style="color: #222; font-family: 'Saira', sans-serif; font-weight: 800; font-size: 2.2em; background: none; text-shadow: none; display: inline-block;">📊 Dashboard de análise Individual</h1>
            </div>
            
        """

    # Criar HTML do resumo técnico do equipamento
    device_summary_html = create_device_summary_html(df_raw)
    # Adicionar id ao bloco de resumo técnico
    device_summary_html = device_summary_html.replace(
        "<div class=\"tabela-resumo-tecnico\"", "<div class=\"tabela-resumo-tecnico\" id=\"bloco-resumo-tecnico\""
    )

    # Combine all parts
    final_html = html_header
    final_html += device_summary_html        # Tabela de resumo técnico
    final_html += "\n".join(clean_blocks_with_ids)    # HTML blocks with ids
    final_html += "\n"
    final_html += global_scripts             # Consolidated scripts
    final_html += "\n"
    # Embutir o DataFrame principal como JSON
    df = df_raw.reset_index()  # 'index' vira coluna
    df['linha'] = df['index'] + 2  # Agora bate com a linha do CSV original

    # CONVERSÃO PARA STRING PARA JSON SERIALIZABLE
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')

    # --- BLOCO JSON COMENTADO TEMPORARIAMENTE ---
    # data_json = json.dumps(df.to_dict(orient='records'), ensure_ascii=False)
    # Modal global + script
    # modal_html = f'''
    # <div class="modal-bg" id="modalBg">
    #     <div class="modal-content" id="modalContent">
    #         <button class="close-modal" onclick="fecharModal()">&times;</button>
    #         <h3>Detalhes do Registro</h3>
    #         <table id="modalTable"></table>
    #     </div>
    # </div>
    # <script>
    # const eventosData = {data_json};
    # function mostrarModal(idx) {{
    #     // Busca o registro pelo valor da coluna 'linha'
    #     const registro = eventosData.find(r => r.linha == idx);
    #     let html = '';
    #     const cols = ['linha', 'Tipo Mensagem', 'Data/Hora Evento', 'Latitude', 'Longitude'];
    #     const labels = ['Linha do CSV', 'Tipo Mensagem', 'Data/Hora Evento', 'Latitude', 'Longitude'];
    #     for (let i = 0; i < cols.length; i++) {{           
    #         html += `<tr><th>` + labels[i] + `</th><td>` + (registro && registro[cols[i]] !== undefined ? registro[cols[i]] : '') + `</td></tr>`;
    #     }}
    #     document.getElementById('modalTable').innerHTML = html;
    #     document.getElementById('modalBg').classList.add('active');
    # }}
    # function fecharModal() {{
    #     document.getElementById('modalBg').classList.remove('active');
    # }}
    # document.getElementById('modalBg').addEventListener('click', function(e) {{
    #     if (e.target === this) fecharModal();
    # }});
    # document.addEventListener('keydown', function(e) {{
    #     if (e.key === 'Escape') fecharModal();
    # }});
    # </script>
    # <style>
    # .modal-bg {{
    #     display: none;
    #     position: fixed;
    #     z-index: 1000;
    #     left: 0; top: 0; width: 100vw; height: 100vh;
    #     background: rgba(0,0,0,0.4);
    #     align-items: center;
    #     justify-content: center;
    # }}
    # .modal-bg.active {{
    #     display: flex;
    # }}
    # .modal-content {{
    #     background: #fff;
    #     border-radius: 18px;
    #     padding: 32px 32px 24px 32px;
    #     min-width: 320px;
    #     max-width: 90vw;
    #     box-shadow: 0 8px 32px rgba(0,0,0,0.18);
    #     position: relative;
    #     animation: fadeIn 0.2s;
    # }}
    # @keyframes fadeIn {{
    #     from {{ opacity: 0; transform: scale(0.95); }}
    #     to {{ opacity: 1; transform: scale(1); }}
    # }}
    # .modal-content h3 {{
    #     margin-top: 0;
    #     font-size: 1.3em;
    #     color: #764ba2;
    #     font-family: 'Saira', sans-serif;
    # }}
    # .modal-content table {{
    #     width: 100%;
    #     border-collapse: collapse;
    #     margin-top: 10px;
    # }}
    # .modal-content th, .modal-content td {{
    #     text-align: left;
    #     padding: 8px 12px;
    # }}
    # .modal-content th {{
    #     color: #495057;
    #     font-weight: bold;
    #     background: #f8f9fa;
    # }}
    # .close-modal {{
    #     position: absolute;
    #     top: 12px; right: 18px;
    #     font-size: 1.5em;
    #     color: #888;
    #     cursor: pointer;
    #     font-weight: bold;
    #     background: none;
    #     border: none;
    # }}
    # @media (max-width: 600px) {{
    #     .modal-content {{ padding: 18px 6px 12px 6px; }}
    # }}
    # </style>
    # '''
    # final_html += modal_html

    final_html += html_footer                # Close HTML with global JS + modal
    # Adicionar JS para scroll suave
    final_html = final_html.replace(
        '</body>',
        '''<script>
        function scrollToBloco(id) {
            // Se for o bloco de análises L2, use showAnalisesL2()
            if (id === 'bloco-smp-eco') {
                showAnalisesL2();
                return;
            }
            // Mostra todos os blocos normais e esconde o bloco de análises L2
            document.querySelectorAll('.bloco-smp-eco').forEach(function(el) { el.style.display = 'none'; });
            document.querySelectorAll('.dashboard-bloco-analise, .bloco-hodometro, .bloco-eventos, .bloco-ignicao, .bloco-log, .bloco-reboot, .bloco-satelites, .bloco-sequenceNumber, .bloco-temporizadas, .bloco-pinning, .bloco-timefix, .bloco-velocidade').forEach(function(el) { el.style.display = ''; });
            // Mostra o menu lateral
            document.getElementById('floating-nav-wrapper').style.display = '';
            // Mostra/oculta botões flutuantes
            document.getElementById('btn-analises-l2').style.display = '';
            document.getElementById('btn-analises-gerais').style.display = 'none';
            // Scroll para o bloco desejado
            const bloco = document.getElementById(id);
            if (bloco) {
                bloco.scrollIntoView({ behavior: 'smooth', block: 'start' });
                bloco.style.boxShadow = '0 0 0 4px #764ba2';
                setTimeout(() => bloco.style.boxShadow = '', 1200);
            }
        }
        function showAnalisesL2() {
            // Esconde todos os blocos normais
            document.querySelectorAll('.dashboard-bloco-analise, .bloco-hodometro, .bloco-eventos, .bloco-ignicao, .bloco-log, .bloco-reboot, .bloco-satelites, .bloco-sequenceNumber, .bloco-temporizadas, .bloco-pinning, .bloco-timefix, .bloco-velocidade, #bloco-resumo-tecnico').forEach(function(el) { el.style.display = 'none'; });
            // Mostra o bloco de análises L2
            document.querySelectorAll('.bloco-smp-eco').forEach(function(el) { el.style.display = ''; });
            // Mostra o botão de voltar
            document.getElementById('btn-analises-l2').style.display = 'none';
            document.getElementById('btn-analises-gerais').style.display = '';
            // Esconde o menu lateral
            document.getElementById('floating-nav-wrapper').style.display = 'none';
            // Scroll para o bloco de análises L2
            const bloco = document.getElementById('bloco-smp-eco');
            if (bloco) {
                bloco.scrollIntoView({ behavior: 'smooth', block: 'start' });
                bloco.style.boxShadow = '0 0 0 4px #764ba2';
                setTimeout(() => bloco.style.boxShadow = '', 1200);
            }
        }
        function showAnalisesGerais() {
            // Mostra todos os blocos normais e esconde o bloco de análises L2
            document.querySelectorAll('.bloco-smp-eco').forEach(function(el) { el.style.display = 'none'; });
            document.querySelectorAll('.dashboard-bloco-analise, .bloco-hodometro, .bloco-eventos, .bloco-ignicao, .bloco-log, .bloco-reboot, .bloco-satelites, .bloco-sequenceNumber, .bloco-temporizadas, .bloco-pinning, .bloco-timefix, .bloco-velocidade, #bloco-resumo-tecnico').forEach(function(el) { el.style.display = ''; });
            // Mostra o botão de análises L2
            document.getElementById('btn-analises-l2').style.display = '';
            document.getElementById('btn-analises-gerais').style.display = 'none';
            // Mostra o menu lateral
            document.getElementById('floating-nav-wrapper').style.display = '';
            // Scroll para o topo
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
        // Abrir/fechar menu ao clicar na seta
        document.getElementById('floating-nav-toggle').onclick = function() {
            document.getElementById('floating-nav-wrapper').classList.toggle('open');
        };
        </script>\n</body>'''
    )

    # Write final file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_html)

    # print(f"Success: Dashboard '{output_file}' generated successfully!")

# if __name__ == "__main__":
#     # Exemplo de uso: você deve carregar o DataFrame df_raw antes de chamar unir_blocos
#     try:
#         df = None
#         # Tenta ler o arquivo com diferentes codificações
#         for enc in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
#             try:
#                 df = pd.read_csv('logs/867488061317839_decoded.csv', encoding=enc, low_memory=False)
#                 break
#             except Exception:
#                 continue
#         if df is None:
#             print("❌ Não foi possível ler o arquivo.")
#             pass
#         unir_blocos(df)
#     except Exception as e:
#         print(f"Erro ao processar o arquivo: {e}")
#         pass    