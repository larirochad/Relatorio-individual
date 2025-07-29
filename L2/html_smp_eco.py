import pandas as pd
from pathlib import Path

def gerar_bloco_smp_eco(irregularidades, filename='bloco_smp_eco.html', tipo_veiculo=None):
    """
    Gera um bloco HTML com as irregularidades operacionais para ser exibido em uma página separada (Análises L2).
    Parâmetro:
        irregularidades: lista de códigos numéricos (ex: [1, 2, 3]) ou lista de dicionários (compatibilidade).
        tipo_veiculo: string ('leve', 'pesado' ou 'desconhecido') para exibir no título.
    """
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    # Se a lista de irregularidades for vazia ou None, substitui por [0]
    if not irregularidades:
        irregularidades = [0]

    # Dicionário de mapeamento código -> descrição
    irregularidade_map = {
        1: {
            'irregularidade': 'Sempre em modo econômico com T30 ok',
            'indicios': (
                'Modo econômico > 0; Ignições: pouca ou nenhuma; '
                'Posicionamento = 0; Modo econômico + velocidade; '
                'Sem evento de desconexão da bateria externa.'
            ),
            'tratativa': 'Ignição virtual caso não tenha acessório'
        },
        2: {
            'irregularidade': 'Sempre em modo econômico com T15 e T30 em possíveis lugares errados',
            'indicios': (
                'Modo econômico > 0; Ignições: nenhuma; '
                'Posicionamento = 0; Modo econômico + velocidade; '
                'Com eventos de desconexão da bateria externa.'
            ),
            'tratativa': 'Manutenção'
        },
        3: {
            'irregularidade': 'Ligação invertida',
            'indicios': (
                'Modo econômico = 0; Ignições: uma ou nenhuma; '
                'Posicionamento > 0; Com eventos de desconexão da bateria externa.'
            ),
            'tratativa': 'Manutenção'
        },
        4: {
            'irregularidade': 'Falha de alimentação<br>Possível intervenção <br> Poderia haver problema de instalação, T30 no T15',
            'indicios': (
                'Foram detectados 4 ou mais eventos de desconexão da bateria externa; '
                'Isso pode indicar problema de alimentação elétrica ou manipulação frequente.'
            ),
            'tratativa': 'Validar o uso do cliente.'
        },
        5: {
            'irregularidade': 'Velocidade em modo econômico - Possível TOW',
            'indicios': (
                'Velocidade em modo econômico; '
                'Tensão da bateria externa menor que 13V, possivelmente TOW;'
                'Possível caso de reboque (TOW);'
            ),
            'tratativa': 'Verificar se o veículo está sendo rebocado'
        },
        6: {
            'irregularidade': 'Velocidade em modo econômico',
            'indicios': (
                'Velocidade em modo econômico; '
                'Tensão da bateria externa maior que 13V, então não é TOW; '
                'Possível conexão errada no T15;'
            ),
            'tratativa': 'Verificar instalação do T15'
        },
        0: {
            'irregularidade': 'Nenhuma irregularidade operacional detectada.',
            'indicios': '',
            'tratativa': 'Nada a fazer'
        }
    }

    # Se for veículo pesado, altera a mensagem do código 4
    if tipo_veiculo == 'pesado':
        irregularidade_map[4]['irregularidade'] = 'Veículo pesado, possivelmente condutor possa estar desligando chave geral'

    # CSS inline (padrão dos outros blocos)
    css = """
    <style>
    .bloco-smp-eco {
        background: #fff;
        border-radius: 30px;
        box-shadow: 0 8px 25px rgba(102, 51, 153, 0.10);
        padding: 50px 100px 60px 100px;
        max-width: 2000px;
        margin: 0 auto 40px auto;
    }
    .bloco-smp-eco .dashboard-title-analise {
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
    .bloco-smp-eco .tabela-container {
        background: #fff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        margin-bottom: 30px;
        overflow-x: auto;
        transition: box-shadow 0.3s, transform 0.3s;
    }
    .bloco-smp-eco .tabela-container:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 15px 35px rgba(0,0,0,0.15); 
        transition: box-shadow 0.3s, transform 0.3s;
    }
    .bloco-smp-eco .tabela-estatisticas {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 1em;
        margin: 0 auto;
    }
    .bloco-smp-eco .tabela-estatisticas th, .bloco-smp-eco .tabela-estatisticas td {
        border: 1px solid #e9ecef;
        padding: 12px 18px;
        text-align: center;
    }
    .bloco-smp-eco .tabela-estatisticas th {
        background: #f8f9fa;
        color: #495057;
        font-weight: bold;
    }
    .tipo-veiculo-info {
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
    </style>
    """

    # Adiciona linha de tipo de veículo destacado
    if tipo_veiculo == 'pesado':
        titulo_tipo = 'Veículo pesado (Tensão > 22V)'
    elif tipo_veiculo == 'leve':
        titulo_tipo = 'Veículo leve (Tensão < 22V)'
    else:
        titulo_tipo = 'Tipo de veículo desconhecido'

    html = f"""
    {css}
    <div class="bloco-smp-eco" id="bloco-smp-eco" style="display:none;">
        <span class="dashboard-title-analise">Análises L2 - Irregularidades Operacionais</span>
        <div class="tipo-veiculo-info">
            {titulo_tipo}
        </div>
        <div class="tabela-container">
            <table class="tabela-estatisticas">
                <thead>
                    <tr>
                        <th>Indícios de Mau Funcionamento</th>
                        <th>Possíveis irregularidades</th>
                        <th>Tratativa</th>
                    </tr>
                </thead>
                <tbody>
    """

    # Suporta tanto lista de códigos quanto lista de dicionários
    for irr in irregularidades:
        if isinstance(irr, dict):
            row = irr
        else:
            row = irregularidade_map.get(irr, irregularidade_map[0])
        # Adiciona quebra de linha após cada ';' nos indícios
        indicios_html = row['indicios'].replace(';', ';<br>') if row['indicios'] else ''
        html += f"""
                    <tr>
                        <td>{indicios_html}</td>
                        <td>{row['irregularidade']}</td>
                        <td>{row['tratativa']}</td>
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

# Exemplo de uso:
if __name__ == "__main__":
    # Exemplo de lista de códigos
    irregularidades = [1, 2, 3, 0]
    gerar_bloco_smp_eco(irregularidades)
