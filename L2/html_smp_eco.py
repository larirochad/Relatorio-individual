import pandas as pd
from pathlib import Path

def gerar_bloco_smp_eco(irregularidades, filename='bloco_smp_eco.html', tipo_veiculo=None):
    """
    Gera um bloco HTML com as irregularidades operacionais para ser exibido em uma página separada (Análises L2).
    Parâmetro:
        irregularidades: lista de códigos numéricos (ex: [1, 2, 3]) ou lista de dicionários (compatibilidade).
        tipo_veiculo: string ('leve', 'pesado' ou 'desconhecido') para exibir no título.
    """
    # print(irregularidades)
    # print(tipo_veiculo)
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
            'irregularidade': 'Velocidade em modo econômico',
            'indicios': (
                'Velocidade em modo econômico; '
                'Isso pode indicar problema de instalação no T15'
            ),
            'tratativa': 'Ignição virtual caso não tenha acessório'
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

    html = """
    <div class="bloco-smp-eco" id="bloco-smp-eco" style="display:none; background: #fff; border-radius: 30px; box-shadow:0 5px 15px rgba(0,0,0,0.08); padding: 60px 80px 70px 80px; max-width: 2000px; margin: 0 auto 40px auto;">
        <span class="dashboard-title-analise" style="font-family: 'Saira', sans-serif; background: linear-gradient(to right, #764ba2, #667eea); -webkit-background-clip: text; background-clip: text; color: transparent; font-size: 2.1em; font-weight: 800; text-shadow: 2px 2px 4px rgba(102, 51, 153, 0.2); display: block; margin: 0 0 30px 0; text-align: center;">Análises L2 - Irregularidades Operacionais</span>
"""
    # Adiciona linha de tipo de veículo destacado
    if tipo_veiculo == 'pesado':
        titulo_tipo = 'Veículo pesado (Tensão > 22V)'
    elif tipo_veiculo == 'leve':
        titulo_tipo = 'Veículo leve (Tensão < 22V)'
    else:
        titulo_tipo = 'Tipo de veículo desconhecido'
    html += f"""
        <div style='background: #f5f6fa; border-radius: 12px; padding: 8px 0 8px 0; margin-bottom:18px; text-align:center;'>
            <span style='font-size:1.2em; font-weight:600; color:#737373;'>
                {titulo_tipo}
            </span>
        </div>
    """
    html += """
        <table class="tabela-estatisticas" style="width:100%; margin-top:20px;">
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
    """

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

# Exemplo de uso:
if __name__ == "__main__":
    # Exemplo de lista de códigos
    irregularidades = [1, 2, 3, 0]
    gerar_bloco_smp_eco(irregularidades)
