import pandas as pd
import json
from pathlib import Path

def gerar_tabela_regressao(df_reg):
    # Filtra apenas as linhas de regressão
    if df_reg is None or df_reg.empty:
        return """
<div style='text-align:center;'>
  <div style='
      display: inline-block;
      background: #f5f6f8;
      color: #218838;
      font-weight: bold;
      font-size: 1.25em;
      border-radius: 20px;
      padding: 12px 32px;
      margin: 20px auto 30px auto;
      text-align: center;
      font-family: \"Saira\", Arial, sans-serif;
      box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  '>
      Nenhuma regressão detectada.
  </div>
</div>
"""
    df_reg = df_reg[df_reg['tipo_problema'] == 'regressão']
    if df_reg.empty:
        return """
<div style='text-align:center;'>
  <div style='
      display: inline-block;
      background: #f5f6f8;
      color: #218838;
      font-weight: bold;
      font-size: 1.25em;
      border-radius: 20px;
      padding: 12px 32px;
      margin: 20px auto 30px auto;
      text-align: center;
      font-family: \"Saira\", Arial, sans-serif;
      box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  '>
      Nenhuma regressão detectada.
  </div>
</div>
"""
    table_html = '''
    <div class="tabela-container">
        <div class="grafico-titulo-container">
            <h3 class="grafico-titulo">Regressões do Hodômetro</h3>
        </div>
        <table class="tabela-estatisticas">
            <thead>
                <tr>
                    <th>Linha</th>
                    <th>Hodômetro anterior</th>
                    <th>Hodômetro da regressão</th>
                    <th>Tipo de mensagem</th>
                    <th>Diferença</th>
                </tr>
            </thead>
            <tbody>
    '''
    for _, row in df_reg.iterrows():
        table_html += f'''
                <tr>
                    <td>{row.get('linha','')}</td>
                    <td>{row.get('Hodômetro_anterior','')}</td>
                    <td>{row.get('Hodômetro_atual','')}</td>
                    <td>{row.get('tipo_mensagem_atual','')}</td>
                    <td>{row.get('Diferenca','')}</td>
                </tr>
        '''
    table_html += '''
            </tbody>
        </table>
    </div>
    '''
    return table_html

def gerar_bloco_hodometro_from_csv(df: pd.DataFrame, df_reg: pd.DataFrame, filename='bloco_hodometro.html'):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    # Lê o CSV e soma todas as distâncias
    total_km = 0.0
    for col in ['Curta', 'Media', 'Longa']:
        if col in df.columns:
            total_km += df[col].fillna(0).sum()

    # Cores
    cor_teste = '#17becf'  # Azul forte
    cor_fundo = '#f5f5f5'

    # Cálculo do percentual atingido
    alcance = min((total_km / 12000) * 100, 100) # Assuming meta_km is 12000 for now, as it's not passed as an argument

    # Formatação do valor
    valor_km_str = f"{total_km:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    alcance_val = f"{alcance:.2f}"
    restante_val = f"{100 - alcance:.2f}"
    # HTML/CSS/JS
    html = f"""
<style>
.grafico-container:hover {{
    transform: translateY(-2px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
    transition: box-shadow 0.3s, transform 0.3s;
}}
</style>
<div class="dashboard-bloco-analise" id="bloco-hodometro" style="background: #fff; border-radius: 30px; box-shadow:0 5px 15px rgba(0,0,0,0.08); padding: 60px 200px 70px 200px; max-width: 2000px; margin: 0 auto 40px auto; transition: box-shadow 0.3s, transform 0.3s;">
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
    <div class="grafico-container grafico-hodometro" style="background: #fff; border-radius: 15px; padding: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.08);  transition: box-shadow 0.3s, transform 0.3s;">
        <h4 style="text-align:center; font-family: Arial, Helvetica, sans-serif; font-weight: 700; margin-bottom: 10px; color: #111;">Total km percorrido</h4>
        <div class="canvas-wrapper" style="position: relative; width: 350px; height: 180px; margin: 0 auto;">
            <canvas id="hodometro_teste" width="350" height="180" style="display: block; box-sizing: border-box; border:0;"></canvas>
            <div style="position: absolute; left: 10px;  font-size: 15px; color: #888; font-family: Arial, Helvetica, sans-serif;">0 km</div>
            <div style="position: absolute; right: 0px; font-size: 15px; color: #888; font-family: Arial, Helvetica, sans-serif;">12000 km</div>
        </div>
        <div style="text-align:center; font-size: 1.3em; font-weight: bold; margin-top: 20px; color: #222; font-family: Arial, Helvetica, sans-serif;">
            {valor_km_str} km
        </div>
    </div>
"""
    # Adiciona a tabela de regressão abaixo do gráfico
    html += gerar_tabela_regressao(df_reg)
    html += f"""
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
                data: [{alcance_val}, {restante_val}],
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
                                return 'Restante: ' + (12000 - {total_km}).toLocaleString('pt-BR', {{minimumFractionDigits: 2, maximumFractionDigits: 2}}) + ' km';
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

    # print(f"✅ Bloco de hodômetro salvo em: {output_path.resolve()}")

if __name__ == "__main__":
    # Exemplo de uso:
    # df_viagens = pd.read_csv('hodometro/resultado_viagens.csv')
    # df_reg = pd.read_csv('hod_regressao.csv')
    # gerar_bloco_hodometro_from_csv(df_viagens, df_reg)
    pass # Placeholder for future DataFrame generation
