import pandas as pd
from pathlib import Path

def gerar_bloco_temporizadas(
    csv_path='Tempo de posicoes/temporizadas_final.csv',
    filename='bloco_temporizadas.html'
):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    # GTERI com ignição ligada: Motion Status começa com '2', tempo diferente de 180s
    df_on = df[(df['Tipo Mensagem'] == 'GTERI') & df['Motion Status'].astype(str).str.startswith('2') & (df['Diferença entre GTERI (IGN)'] != '')].copy()
    df_on['tempo'] = pd.to_numeric(df_on['Diferença entre GTERI (IGN)'], errors='coerce')
    anomalias_on = df_on[df_on['tempo'] != 180]

    # GTERI com ignição desligada: Motion Status começa com '1', tempo diferente de 3600s
    df_off = df[(df['Tipo Mensagem'] == 'GTERI') & df['Motion Status'].astype(str).str.startswith('1') & (df['Diferença entre GTERI (IGF)'] != '')].copy()
    df_off['tempo'] = pd.to_numeric(df_off['Diferença entre GTERI (IGF)'], errors='coerce')
    anomalias_off = df_off[df_off['tempo'] != 3600]

    # CSS isolado
    css = """
    .bloco-temporizadas {
        background: #fff;
        border-radius: 30px;
        box-shadow: 0 8px 25px rgba(102, 51, 153, 0.10);
        padding: 50px 100px 60px 100px;
        max-width: 2000px;
        margin: 0 auto 40px auto;
    }
    .bloco-temporizadas .dashboard-title-temporizadas {
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
    .bloco-temporizadas .grafico-titulo-container {
        text-align: center;
        color: #495057;
        margin: 0;
        font-size: 1.5em;
        padding: 10px 25px;
        background: #f8f9fa;
        border-radius: 20px;
        display: inline-block;
    }
    .bloco-temporizadas .tabela-temporizadas-container {
        background: #fff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        margin-bottom: 30px;
        overflow-x: auto;
        transition: box-shadow 0.3s, transform 0.3s;
    }
    .bloco-temporizadas .tabela-temporizadas-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    }
    .bloco-temporizadas .tabela-temporizadas {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 1em;
        margin: 0 auto;
    }
    .bloco-temporizadas .tabela-temporizadas th, .bloco-temporizadas .tabela-temporizadas td {
        border: 1px solid #e9ecef;
        padding: 12px 18px;
        text-align: center;
    }
    .bloco-temporizadas .tabela-temporizadas th {
        background: #f8f9fa;
        color: #495057;
        font-weight: bold;
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
    /* Adiciona o fundo arredondado e fonte padrão para os títulos das tabelas */
    .bloco-temporizadas .grafico-titulo-container {
        text-align: center;
        margin-bottom: 10px;
    }
    .bloco-temporizadas .grafico-titulo {
        display: inline-block;
        background: #f8f9fa;
        border-radius: 20px;
        padding: 10px 32px;
        font-size: 20px;
        font-weight: bold;
        color: #495057;
        font-family: Arial, Helvetica, sans-serif;
        text-align: center;
        font-style: normal;
        text-shadow: none;
        margin: 0;
    }
    .ver-todos-btn {
        margin-bottom: 10px;
        background: linear-gradient(90deg,#764ba2,#667eea);
        color: #fff;
        border: none;
        border-radius: 12px;
        padding: 8px 22px;
        font-size: 1em;
        font-family: 'Saira', Arial, Helvetica, sans-serif;
        font-weight: 700;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(102,51,153,0.07);
        transition: background 0.2s, color 0.2s;
    }
    .ver-todos-btn:hover {
        background: linear-gradient(90deg,#667eea,#764ba2);
        color: #fff;
    }
    .extra-row { display: none; }
    .expanded .extra-row { display: table-row; }
    
    """
    css_resumo = """
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
        color: #495057;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .resumo-anomalia-numero {
        font-size: 2em;
        font-weight: bold;
        color: #764ba2;
        margin-bottom: 2px;
    }
    .resumo-anomalia-legenda {
        font-size: 0.95em;
        color: #888;
    }
    """

    def tabela_html(df, titulo, table_id):
        html = f"""
        <div class=\"tabela-temporizadas-container\">
            <div class=\"grafico-titulo-container\"><span class=\"grafico-titulo\">{titulo}</span></div>
            <table class=\"tabela-temporizadas\" id="{table_id}">
                <thead>
                    <tr>
                        <th>Linha</th>
                        <th>Data</th>
                        <th>Hora</th>
                        <th>Tempo (s)</th>
                    </tr>
                </thead>
                <tbody>
        """
        for i, (_, row) in enumerate(df.iterrows()):
            datahora = pd.to_datetime(row['Data/Hora Evento'])
            data = datahora.strftime('%d/%m/%Y') if not pd.isnull(datahora) else ''
            hora = datahora.strftime('%H:%M:%S') if not pd.isnull(datahora) else ''
            extra_class = ''
            if i >= 5:
                extra_class = 'extra-row'
            html += f"""
            <tr class='{extra_class}'>
                <td><a href=\"#\" class=\"Linha-link\" onclick=\"mostrarModal({int(row['linha'])}); return false;\">{int(row['linha'])}</a></td>
                <td>{data}</td>
                <td>{hora}</td>
                <td>{int(row['tempo']) if not pd.isnull(row['tempo']) else ''}</td>
            </tr>
            """
        html += f"""
                </tbody>
            </table>
            <div style='text-align:center; margin-top: 12px;'>
                <button class='ver-todos-btn' onclick=\"toggleExpand('{table_id}')\" id=\"btn-{table_id}\">Ver todos os dados</button>
            </div>
        </div>
        """
        return html

    # Resumos de anomalias
    total_on = len(df_on)
    total_anomalias_on = len(anomalias_on)
    total_off = len(df_off)
    total_anomalias_off = len(anomalias_off)

    resumo_html = f'''
    <div class="resumo-anomalias-container">
        <div class="resumo-anomalia-card">
            <div class="resumo-anomalia-titulo">Analomalias por tempo em movimento</div>
            <div class="resumo-anomalia-numero">{total_anomalias_on}</div>
            <div class="resumo-anomalia-legenda">de {total_on} eventos de temporização</div>
        </div>
        <div class="resumo-anomalia-card">
            <div class="resumo-anomalia-titulo">Anomalias por modo econômico</div>
            <div class="resumo-anomalia-numero">{total_anomalias_off}</div>
            <div class="resumo-anomalia-legenda">de {total_off} eventos de temporização</div>
        </div>
    </div>
    '''

    # JavaScript para expandir/recolher as tabelas
    js = '''
    <script>
    function toggleExpand(tableId) {
        var table = document.getElementById(tableId);
        var btn = document.getElementById('btn-' + tableId);
        if (table.classList.contains('expanded')) {
            table.classList.remove('expanded');
            btn.textContent = 'Ver todos os dados';
        } else {
            table.classList.add('expanded');
            btn.textContent = 'Ver menos';
        }
    }
    </script>
    '''

    html = f"""
    <style>
    {css}
    {css_resumo}
    </style>
    <div class="bloco-temporizadas">
        <span class="dashboard-title-temporizadas">Anomalias de Intervalo entre mensagens temporizadas</span>
        {resumo_html}
        {tabela_html(anomalias_on, 'Anomalias por tempo em movimento', 'tabela-on')}
        {tabela_html(anomalias_off, 'Anomalias por modo econômico', 'tabela-off')}
    </div>
    {js}
    """

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Bloco de temporizadas salvo em: {output_path.resolve()}")

if __name__ == "__main__":
    gerar_bloco_temporizadas()
