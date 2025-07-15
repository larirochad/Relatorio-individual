import pandas as pd
from pathlib import Path
from typing import Union

def gerar_bloco_sequenceNumber(df: pd.DataFrame, filename='bloco_sequenceNumber.html'):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    tipos = ['salto_na_sequencia', 'valor_repetido', 'reset_de_contagem', 'regressao_de_contagem', 'ordem_incorreta_temporal']
    nomes = {
        'salto_na_sequencia': 'Saltos na Sequência',
        'valor_repetido': 'Valores Repetidos',
        'reset_de_contagem': 'Reset de Contagem',
        'regressao_de_contagem': 'Regressão de contagem',
        'ordem_incorreta_temporal': 'Ordem incorreta temporal'
    }
    resumos = {}
    tabelas = {}
    max_linhas = 5
    for tipo in tipos:
        df_tipo = df[df['tipo_problema'] == tipo]
        resumos[tipo] = len(df_tipo)
        if len(df_tipo) == 0:
            continue
        linhas_html = ""
        for i, (_, row) in enumerate(df_tipo.iterrows()):
            extra_class = "linha-oculta linha-extra-seq" if i >= max_linhas else ""
            if tipo == 'valor_repetido':
                linhas_html += f"""
                <tr class='{extra_class}'>
                    <td>{int(row['linha'])}</td>
                    <td>{row['sequencia_anterior']}</td>
                    <td>{row['sequencia_atual']}</td>
                    <td>{row['tipo_mensagem_atual']}</td>
                </tr>
                """
            else:
                linhas_html += f"""
                <tr class='{extra_class}'>
                    <td>{int(row['linha'])}</td>
                    <td>{row['sequencia_anterior']}</td>
                    <td>{row['sequencia_atual']}</td>
                    <td>{row['tipo_mensagem_atual']}</td>
                    <td>{row['Diferenca']}</td>
                </tr>
                """
        botao_html = ""
        if len(df_tipo) > max_linhas:
            botao_html = f'''
            <div style="text-align: center;">
                <button class="btn-mostrar-todos" onclick="toggleLinhasSeq('{tipo}')" id="btn_seq_{tipo}">
                    Ver todos os dados
                </button>
            </div>
            '''
        if tipo == 'valor_repetido':
            tabelas[tipo] = f'''
            <div class="tabela-temporizadas-container">
                <div class="grafico-titulo-container"><span class="grafico-titulo">{nomes[tipo]}</span></div>
                <table class="tabela-temporizadas" id="tabela_seq_{tipo}">
                    <thead>
                        <tr>
                            <th>Linha</th>
                            <th>Valor anterior</th>
                            <th>Valor atual</th>
                            <th>Mensagem atual</th>
                        </tr>
                    </thead>
                    <tbody>
                        {linhas_html}
                    </tbody>
                </table>
                {botao_html}
            </div>
            '''
        else:
            tabelas[tipo] = f'''
            <div class="tabela-temporizadas-container">
                <div class="grafico-titulo-container"><span class="grafico-titulo">{nomes[tipo]}</span></div>
                <table class="tabela-temporizadas" id="tabela_seq_{tipo}">
                    <thead>
                        <tr>
                            <th>Linha</th>
                            <th>Valor anterior</th>
                            <th>Valor atual</th>
                            <th>Mensagem atual</th>
                            <th>Diferença</th>
                        </tr>
                    </thead>
                    <tbody>
                        {linhas_html}
                    </tbody>
                </table>
                {botao_html}
            </div>
            '''
    # Resumo
    resumo_html = f'''
    <div class="resumo-anomalias-container">
        <div class="resumo-anomalia-card">
            <div class="resumo-anomalia-titulo">Saltos na sequência</div>
            <div class="resumo-anomalia-numero">{resumos.get('salto_na_sequencia', 0)}</div>
            <div class="resumo-anomalia-legenda">Eventos com salto</div>
        </div>
        <div class="resumo-anomalia-card">
            <div class="resumo-anomalia-titulo">Valores repetidos</div>
            <div class="resumo-anomalia-numero">{resumos.get('valor_repetido', 0)}</div>
            <div class="resumo-anomalia-legenda">Eventos com repetição</div>
        </div>
        <div class="resumo-anomalia-card">
            <div class="resumo-anomalia-titulo">Reset de contagem</div>
            <div class="resumo-anomalia-numero">{resumos.get('reset_de_contagem', 0)}</div>
            <div class="resumo-anomalia-legenda">Eventos com reset</div>
        </div>
        <div class="resumo-anomalia-card">
            <div class="resumo-anomalia-titulo">Regressão de contagem</div>
            <div class="resumo-anomalia-numero">{resumos.get('regressao_de_contagem', 0)}</div>
            <div class="resumo-anomalia-legenda">Eventos de regressão</div>
        </div>
        <div class="resumo-anomalia-card">
            <div class="resumo-anomalia-titulo">Ordem incorreta temporal</div>
            <div class="resumo-anomalia-numero">{resumos.get('ordem_incorreta_temporal', 0)}</div>
            <div class="resumo-anomalia-legenda">Eventos fora de ordem temporal</div>
        </div>
    </div>
    '''
    # Indicativo visual se não houver problemas de regressão de contagem
    regressao_html = ""
    if resumos.get('regressao_de_contagem', 0) == 0:
        regressao_html = '''
        <div style="text-align:center; margin: 20px 0;">
            <span style="color: #28a745; font-weight: bold; font-size: 1.2em;">Nenhum problema de regressão de contagem encontrado.</span>
        </div>
        '''
    # CSS e JS
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
    .resumo-anomalia-numero {
        color: #764ba2;
    }
    </style>
    '''
    js = '''
    <script>
    function toggleLinhasSeq(tipo) {
        const linhas = document.querySelectorAll(`#tabela_seq_${tipo} .linha-extra-seq, #tabela_seq_${tipo} .linha-oculta`);
        const btn = document.getElementById(`btn_seq_${tipo}`);
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
        } else {
            btn.textContent = 'Ver todos os dados';
        }
    }
    </script>
    '''
    html = f'''
    {css}
    <div class="bloco-temporizadas">
        <span class="dashboard-title-temporizadas">Anomalias na Sequência de Mensagens</span>
        {resumo_html}
        {tabelas.get('salto_na_sequencia', '')}
        {tabelas.get('valor_repetido', '')}
        {tabelas.get('reset_de_contagem', '')}
        {tabelas.get('regressao_de_contagem', '')}
        {tabelas.get('ordem_incorreta_temporal', '')}
        {regressao_html}
    </div>
    {js}
    '''
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    # print(f"✅ Bloco de sequence number salvo em: {output_path.resolve()}")

if __name__ == "__main__":
    # This part of the code is now redundant as the function expects a DataFrame.
    # If you want to test, you'd need to load a DataFrame first.
    # For example:
    # df = pd.read_csv('sequence_number/problemas_ordenando_sequencia.csv', encoding='utf-8-sig')
    # gerar_bloco_sequenceNumber(df)
    pass 