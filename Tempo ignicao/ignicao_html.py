import pandas as pd
from pathlib import Path

def gerar_bloco_ignicao(
    csv_path='Tempo ignicao/tempo_ignicao_viagens.csv',
    filename='bloco_ignicao.html'
):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    # Lê o CSV de tempos de ignição
    df = pd.read_csv(csv_path, encoding='utf-8-sig')

    # Encontrar maior e menor tempo ON
    df_on = df[df['ign on (s)'].notnull() & (df['ign on (s)'] != '')]
    max_on = df_on.loc[df_on['ign on (s)'].idxmax()]
    min_on = df_on.loc[df_on['ign on (s)'].idxmin()]

    # Encontrar maior e menor tempo OFF
    df_off = df[df['ign off (s)'].notnull() & (df['ign off (s)'] != '')]
    if not df_off.empty:
        max_off = df_off.loc[df_off['ign off (s)'].idxmax()]
        min_off = df_off.loc[df_off['ign off (s)'].idxmin()]
    else:
        max_off = min_off = None

    # Montar linhas da tabela
    linhas = []
    # ON
    linhas.append({
        'linha': int(max_on['Linha_IGN']),
        'tipo': 'on',
        'tempo': int(max_on['ign on (s)']),
        'data': max_on['Dia_IGN'],
        'desc': 'Maior tempo ON'
    })
    # linhas.append({
    #     'linha': int(min_on['Linha_IGN']),
    #     'tipo': 'on',
    #     'tempo': int(min_on['ign on (s)']),
    #     'data': min_on['Dia_IGN'],
    #     'desc': 'Menor tempo ON'
    # })
    # OFF (se existir)
    if max_off is not None and min_off is not None:
        linhas.append({
            'linha': int(max_off['Linha_IGF']),
            'tipo': 'off',
            'tempo': int(max_off['ign off (s)']),
            'data': max_off['Dia_IGF'],
            'desc': 'Maior tempo OFF'
        })
        # linhas.append({
        #     'linha': int(min_off['Linha_IGF']),
        #     'tipo': 'off',
        #     'tempo': int(min_off['ign off (s)']),
        #     'data': min_off['Dia_IGF'],
        #     'desc': 'Menor tempo OFF'
        # })

    # CSS isolado
    css = """
    <style>
    .bloco-ignicao {
        background: #fff;
        border-radius: 30px;
        box-shadow: 0 8px 25px rgba(102, 51, 153, 0.10);
        padding: 50px 100px 60px 100px;
        max-width: 2000px;
        margin: 0 auto 40px auto;
    }
    .bloco-ignicao .dashboard-title-ignicao {
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
    .bloco-ignicao .tabela-ignicao-container {
        background: #fff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        margin-bottom: 30px;
        overflow-x: auto;
        transition: box-shadow 0.3s, transform 0.3s;
    }
    .bloco-ignicao .tabela-ignicao-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    }
    .bloco-ignicao .tabela-ignicao {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 1em;
        margin: 0 auto;
    }
    .bloco-ignicao .tabela-ignicao th, .bloco-ignicao .tabela-ignicao td {
        border: 1px solid #e9ecef;
        padding: 12px 18px;
        text-align: center;
    }
    .bloco-ignicao .tabela-ignicao th {
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
    </style>
    """

    # Montar HTML
    html = f"""
    {css}
    <div class="bloco-ignicao">
        <span class="dashboard-title-ignicao">Tempos de Ignição (ON/OFF)</span>
        <div class="tabela-ignicao-container">
            <table class="tabela-ignicao">
                <thead>
                    <tr>
                        <th>Linha</th>
                        <th>Ignição</th>
                        <th>Tempo (s)</th>
                        <th>Data</th>
                        <th>Resumo</th>
                    </tr>
                </thead>
                <tbody>
    """

    for l in linhas:
        html += f"""
        <tr>
            <td><a href="#" class="Linha-link" onclick="mostrarModal({l['linha']}); return false;">{l['linha']}</a></td>
            <td>{l['tipo']}</td>
            <td>{l['tempo']}</td>
            <td>{l['data']}</td>
            <td>{l['desc']}</td>
        </tr>
        """

    html += """
                </tbody>
            </table>
        </div>
    </div>
    """

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Bloco de ignição salvo em: {output_path.resolve()}")

if __name__ == "__main__":
    gerar_bloco_ignicao()
