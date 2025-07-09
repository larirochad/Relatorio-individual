import pandas as pd
from pathlib import Path

def gerar_bloco_reboot(
    csv_path='Reboot/reboot_eventos.csv',
    filename='bloco_reboot.html'
):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    # Lê o CSV de reboots
    df = pd.read_csv(csv_path, encoding='iso-8859-1')
    total_reboots = len(df)

    # Formata data e hora
    df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
    df['Data'] = df['Data/Hora Evento'].dt.strftime('%d/%m')
    df['Hora'] = df['Data/Hora Evento'].dt.strftime('%H:%M:%S')

    # CSS isolado
    css = """
    <style>
    .bloco-reboot {
        background: #fff;
        border-radius: 30px;
        box-shadow: 0 8px 25px rgba(102, 51, 153, 0.10);
        padding: 50px 100px 60px 100px;
        max-width: 2000px;
        margin: 0 auto 40px auto;
    }
    .bloco-reboot .dashboard-title-reboot {
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
    .bloco-reboot .faixa-legenda-reboot {
        text-align: center;
        font-size: 14px;
        color: #898989;
        margin-bottom: 25px;
        background: #f8f9fa;
        font-weight: 500;
        border-radius: 10px;
        padding: 10px;
        width: 100%;
        display: block;
        margin-left: 0;
        margin-right: 0;
    }
    .bloco-reboot .resumo-reboot {
        text-align: center;
        font-size: 1.1em;
        font-family: Arial, Helvetica, sans-serif;
        margin-bottom: 25px;
        color: #333;
        background: #f8f9fa;
        border-radius: 12px;
        padding: 18px 0;
        box-shadow: 0 2px 8px rgba(102, 51, 153, 0.07);
        width: 100%;
        display: block;
        margin-left: 0;
        margin-right: 0;
    }
    .bloco-reboot .tabela-reboot-container {
        background: #fff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        margin-bottom: 30px;
        overflow-x: auto;
        transition: box-shadow 0.3s, transform 0.3s;
    }
    .bloco-reboot .tabela-reboot-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    }
    .bloco-reboot .tabela-reboot {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 1em;
        margin: 0 auto;
    }
    .bloco-reboot .tabela-reboot th, .bloco-reboot .tabela-reboot td {
        border: 1px solid #e9ecef;
        padding: 12px 18px;
        text-align: center;
    }
    .bloco-reboot .tabela-reboot th {
        background: #f8f9fa;
        color: #495057;
        font-weight: bold;
    }
    .bloco-reboot .grafico-titulo-container {
        text-align: center;
        margin-bottom: 10px;
    }
    .bloco-reboot .grafico-titulo {
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

    # Monta tabela HTML
    html = f"""
    {css}
    <div class="bloco-reboot">
        <span class="dashboard-title-reboot">Reboots do Equipamento</span>
        <div class="tabela-reboot-container">
            <div class="resumo-reboot">
                Total de reboots encontrados: <b>{total_reboots}</b>
            </div>
            <div class="grafico-titulo-container">
                <h3 class="grafico-titulo">Histórico de Reboots</h3>
            </div>
            <table class="tabela-reboot">
                <thead>
                    <tr>
                        <th>Contagem</th>
                        <th>Data</th>
                        <th>Hora</th>
                        <th>Motivo</th>
                    </tr>
                </thead>
                <tbody>
    """

    for _, row in df.iterrows():
        html += f"""
        <tr>
            <td>{row['Reboot Nº']}</td>
            <td>{row['Data']}</td>
            <td>{row['Hora']}</td>
            <td>{row['Descrição Motivo Power On']}</td>
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

    print(f"✅ Bloco de reboot salvo em: {output_path.resolve()}")

if __name__ == "__main__":
    gerar_bloco_reboot()
