import pandas as pd
from pathlib import Path
from typing import Union

def gerar_bloco_timefix(df: pd.DataFrame, filename='bloco_timefix.html'):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    # Filtra apenas os valores negativos de Time fix (agora apenas menores que -2)
    df_neg = df[df['Time fix'] < -2].copy()
    total_anomalias = len(df_neg)

    # Formata as datas
    def formatar(dt):
        try:
            return pd.to_datetime(dt).strftime('%d/%m/%Y - %H:%M:%S')
        except:
            return ''
    # Garante que são Series pandas
    df_neg['Data/Hora Evento'] = pd.Series(df_neg['Data/Hora Evento']).apply(formatar)
    df_neg['GNSS UTC Time'] = pd.Series(df_neg['GNSS UTC Time']).apply(formatar)

    # Resumo estilo Satélites
    resumo_html = f'''
    <div class="resumo-anomalias-container">
        <div class="resumo-anomalia-card">
            <div class="resumo-anomalia-titulo">Total de anomalias de Time fix no futuro</div>
            <div class="resumo-anomalia-numero red-timefix">{total_anomalias}</div>
            <div class="resumo-anomalia-legenda">Fix no "futuro" em relação ao evento > 2s </div>
        </div>
    </div>
    '''

    # Parâmetros para linhas extras
    max_linhas = 5
    tem_mais = total_anomalias > max_linhas

    # Monta as linhas da tabela
    linhas_html = ""
    for i, (_, row) in enumerate(df_neg.iterrows()):
        if tem_mais and i >= max_linhas:
            extra_class = "linha-oculta linha-extra-timefix"
        else:
            extra_class = ""
        linhas_html += f"""
        <tr class='linha-extra' data-tabela="tabela_timefix" style="display:none;">
            <td>{int(row['linha_original'])}</td>
            <td>{row['Data/Hora Evento']}</td>
            <td>{row['GNSS UTC Time']}</td>
            <td>{'+' + str(int(abs(row['Time fix'])))} </td>
        </tr>
        """

    # Só mostra o botão se houver linhas extras
    botao_html = ""
    if tem_mais and len(df_neg) > max_linhas:
        botao_html = '''
        <div style="text-align: center;">
            <button class="btn-mostrar-todos" onclick="toggleLinhasTimefix()" id="btn_timefix" data-tabela="tabela_timefix" data-mostrando="false">
                Ver todos os dados
            </button>
        </div>
        '''

    tabela = f'''
    <div class="tabela-temporizadas-container">
        <div class="grafico-titulo-container"><span class="grafico-titulo">Fix "futuro" em relação ao evento</span></div>
        <table class="tabela-temporizadas" id="tabela_timefix">
            <thead>
                <tr>
                    <th>Linha</th>
                    <th>Data/Hora Evento</th>
                    <th>Data/Hora fix</th>
                    <th>Delay (s)</th>
                </tr>
            </thead>
            <tbody>
                {linhas_html}
            </tbody>
        </table>
        {botao_html}
    </div>
    '''

    # CSS extra para botão e linhas ocultas (usa padrão do bloco de velocidade)
    css = '''
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
    .linha-oculta {
        display: none;
    }
    .resumo-anomalia-numero.red-timefix {
        color: #dc3545;
    }
    </style>
    '''

    # JS para expandir/recolher linhas
    js = ''

    html = f'''
    {css}
    <div class="bloco-temporizadas" id="bloco-timefix">
        <span class="dashboard-title-temporizadas">Anomalias com Time fix no futuro </span>
        {resumo_html}
        {tabela}
    </div>
    {js}
    '''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # print(f"✅ Bloco de time fix salvo em: {output_path.resolve()}")

if __name__ == "__main__":
    # This part of the code is now incorrect as gerar_bloco_timefix expects a DataFrame, not a path.
    # It should be removed or replaced with a proper example of how to generate a DataFrame.
    # For now, keeping it as is, but it will likely cause an error.
    # Example usage (assuming df is a pandas DataFrame):
    # df = pd.read_csv('Time_fix/time_fix_resultado.csv', encoding='utf-8')
    # gerar_bloco_timefix(df)
    pass # No example usage provided as per instructions
