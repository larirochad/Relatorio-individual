import pandas as pd
from pathlib import Path

def gerar_bloco_gap(df_gap: pd.DataFrame, filename='bloco_gap.html'):
    # Garante que gap_s é float
    if df_gap is not None and 'gap_s' in df_gap.columns:
        df_gap['gap_s'] = pd.to_numeric(df_gap['gap_s'], errors='coerce')
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    max_linhas = 5
    # CSS inline (padrão dos outros blocos)
    css = """
    <style>
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
    .bloco-gap {
        background: #fff;
        border-radius: 30px;
        box-shadow: 0 8px 25px rgba(102, 51, 153, 0.10);
        padding: 50px 100px 60px 100px;
        max-width: 2000px;
        margin: 0 auto 40px auto;
    }
    .bloco-gap .dashboard-title-analise {
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
    .gap-legenda {
        background: linear-gradient(90deg, #f8fafc 60%, #e9ecef 100%);
        border-radius: 18px;
        padding: 10px 24px;
        margin: 18px auto 18px auto;
        font-size: 1.08em;
        color: #444;
        font-family: 'Saira', Arial, sans-serif;
        font-weight: 500;
        max-width: 600px;
        box-shadow: 0 2px 8px rgba(102,51,153,0.07);
        text-align: center;
    }
    .bloco-gap .tabela-container {
        background: #fff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        margin-bottom: 30px;
        overflow-x: auto;
        transition: box-shadow 0.3s, transform 0.3s;
    }
    .bloco-gap .tabela-container:hover { transform: translateY(-2px); box-shadow: 0 15px 35px rgba(0,0,0,0.15); transition: box-shadow 0.3s, transform 0.3s;}
    .bloco-gap .tabela-estatisticas {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 1em;
        margin: 0 auto;
    }
    .bloco-gap .tabela-estatisticas th, .bloco-gap .tabela-estatisticas td {
        border: 1px solid #e9ecef;
        padding: 12px 18px;
        text-align: center;
    }
    .bloco-gap .tabela-estatisticas th {
        background: #f8f9fa;
        color: #495057;
        font-weight: bold;
    }
    .mensagem-sem-problemas {
        text-align: center;
        color: #28a745;
        font-size: 1.3em;
        font-weight: bold;
        margin: 30px 0 10px 0;
        font-family: 'Saira', sans-serif;
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
    /* ADICIONADO: CSS para linhas ocultas */
    .linha-oculta {
        display: none;
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

    # Monta tabela HTML com até 5 linhas visíveis e botão para expandir
    table_html = '''
    <div class="tabela-container">
        <div class="grafico-titulo-container">
            <h3 class="grafico-titulo">Gaps Excedidos em Mensagens Temporizadas</h3>
        </div>
        <div class="faixa-legenda">Considera apenas gaps excedidos: <b>Periódicas &gt; 240s</b> | <b>Modo Econômico &gt; 7200s</b></div>
        <table class="tabela-estatisticas" id="tabela_gap_excedido">
            <thead>
                <tr>
                    <th>Linha</th>
                    <th>Data / Hora</th>
                    <th>Tipo</th>
                    <th>GAP (s)</th>
                </tr>
            </thead>
            <tbody>
    '''
    
    linhas_visiveis = []
    linhas_ocultas = []
    mensagem_sem_problemas = ''
    
    if df_gap is not None and not df_gap.empty:
        for i, (_, row) in enumerate(df_gap.iterrows()):
            linha = row.get('linha_atual', '')
            data_hora = row.get('data_atual', '')
            tipo = 'Periódica' if row.get('tipo', '').upper() == 'PERI' else 'Modo Econômico'
            gap = f"{row.get('gap_s', ''):.0f}" if pd.notnull(row.get('gap_s', None)) else ''
            
            linha_html = f'''
                <tr{' class="linha-oculta linha-gap-excedido"' if i >= max_linhas else ''}>
                    <td>{linha}</td>
                    <td>{data_hora}</td>
                    <td>{tipo}</td>
                    <td>{gap}</td>
                </tr>
            '''
            
            if i < max_linhas:
                linhas_visiveis.append(linha_html)
            else:
                linhas_ocultas.append(linha_html)
        
        table_html += "".join(linhas_visiveis + linhas_ocultas)
    else:
        table_html += '''<tr><td colspan="4">Nenhum gap excedido encontrado.</td></tr>'''
        mensagem_sem_problemas = '''<div class="mensagem-sem-problemas">Nenhum problema de gap excedido foi encontrado nos dados analisados.</div>'''
    
    table_html += '''
            </tbody>
        </table>
    '''
    
    # Botão para expandir/contrair se houver mais de 5 linhas - CORRIGIDO
    if df_gap is not None and len(df_gap) > max_linhas:
        table_html += f'''<div style="text-align: center;">
            <button class="btn-mostrar-todos" onclick="toggleLinhasGap('gap-excedido', {len(df_gap)})" id="btn_gap-excedido" data-tabela="tabela_gap_excedido">
                Ver todos os dados
            </button>
        </div>'''
    
    table_html += '</div>'

    # ADICIONADO: JavaScript para a função toggleLinhasGap
    javascript = '''
    <script>
    // Função específica para o bloco gap, compatível com o botão universal
    function toggleLinhasGap(tipo, total) {
        const linhas = document.querySelectorAll('.linha-' + tipo);
        const btn = document.getElementById('btn_' + tipo);
        const todasOcultas = Array.from(linhas).every(linha => linha.classList.contains('linha-oculta'));
        
        linhas.forEach(linha => {
            if (todasOcultas) {
                linha.classList.remove('linha-oculta');
            } else {
                linha.classList.add('linha-oculta');
            }
        });
        
        if (todasOcultas) {
            btn.textContent = 'Mostrar apenas 5 registros';
            // Dispara evento personalizado para o botão universal detectar
            const event = new CustomEvent('tabelaExpandida', { detail: { tabelaId: 'tabela_gap_excedido' } });
            document.dispatchEvent(event);
        } else {
            btn.textContent = 'Ver todos os dados';
            // Dispara evento personalizado para o botão universal detectar
            const event = new CustomEvent('tabelaMinimizada', { detail: { tabelaId: 'tabela_gap_excedido' } });
            document.dispatchEvent(event);
        }
    }
    </script>
    '''

    html = f'''
    {css}
    <div class="bloco-gap bloco-smp-eco" id="bloco-smp-eco" style="display:none;">
        <span class="dashboard-title-analise">Análise de Gaps em Mensagens Temporizadas</span>
        {mensagem_sem_problemas}
        {table_html}
    </div>
    {javascript}
    '''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)