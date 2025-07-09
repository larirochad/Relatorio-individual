import pandas as pd
import json
from pathlib import Path

def gerar_bloco_hodometro_from_csv(csv_path, meta_km=12000, filename='bloco_hodometro.html'):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    # Lê o CSV e soma todas as distâncias
    df = pd.read_csv(csv_path)
    total_km = 0.0
    for col in ['Curta', 'Media', 'Longa']:
        if col in df.columns:
            total_km += df[col].fillna(0).sum()

    # Cores
    cor_teste = '#17becf'  # Azul forte
    cor_fundo = '#f5f5f5'

    # Cálculo do percentual atingido
    alcance = min((total_km / meta_km) * 100, 100)

    # Formatação do valor
    valor_km_str = f"{total_km:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # HTML/CSS/JS
    html = f"""
<div class="dashboard-bloco-analise" style="background: #fff; border-radius: 30px; box-shadow: 0 8px 25px rgba(102, 51, 153, 0.10); padding: 60px 200px 70px 200px; max-width: 900px; margin: 0 auto 40px auto;">
    <span class="dashboard-title-analise" style="
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
    ">Hodômetro</span>
    <div class="grafico-container" style="background: #fff; border-radius: 15px; padding: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); margin-bottom: 0;">
        <h4 style="text-align:center; font-family: Arial, Helvetica, sans-serif; font-weight: 700; margin-bottom: 10px; color: #111;">Teste</h4>
        <div class="canvas-wrapper" style="position: relative; width: 350px; height: 180px; margin: 0 auto;">
            <canvas id="hodometro_teste" width="350" height="180" style="display: block; box-sizing: border-box; border:0;"></canvas>
            <div style="position: absolute; left: 10px;  font-size: 15px; color: #888; font-family: Arial, Helvetica, sans-serif;">0 km</div>
            <div style="position: absolute; right: 0px; font-size: 15px; color: #888; font-family: Arial, Helvetica, sans-serif;">{meta_km:,.0f} km</div>
        </div>
        <div style="text-align:center; font-size: 1.3em; font-weight: bold; margin-top: 20px; color: #222; font-family: Arial, Helvetica, sans-serif;">
            {valor_km_str} km
        </div>
    </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
(function() {{
    const ctx = document.getElementById('hodometro_teste').getContext('2d');
    new Chart(ctx, {{
        type: 'doughnut',
        data: {{
            labels: ['Concluído', 'Restante'],
            datasets: [{{
                data: [{alcance:.2f}, {100 - alcance:.2f}],
                backgroundColor: ['{cor_teste}', '{cor_fundo}'],
                borderWidth: 0
            }}]
        }},
        options: {{
            responsive: false,
            cutout: '70%',
            circumference: 180,
            rotation: -90,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            if(context.dataIndex === 0) {{
                                return 'Concluído: {valor_km_str} km';
                            }} else {{
                                return 'Restante: ' + ({meta_km} - {total_km}).toLocaleString('pt-BR', {{minimumFractionDigits: 2, maximumFractionDigits: 2}}) + ' km';
                            }}
                        }}
                    }}
                }}
            }},
            animation: {{
                animateRotate: true,
                animateScale: true
            }}
        }}
    }});
}})();
</script>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Bloco de hodômetro salvo em: {output_path.resolve()}")

if __name__ == "__main__":
    gerar_bloco_hodometro_from_csv('hodometro/resultado_viagens.csv')
