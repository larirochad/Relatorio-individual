import pandas as pd
from pathlib import Path
from typing import Union

# Adiciona função utilitária para formatar datas

def format_datetime(val):
    try:
        return pd.to_datetime(val).strftime('%d/%m/%y - %H:%M:%S') if pd.notnull(val) and val else ''
    except Exception:
        return val or ''

def gerar_bloco_sequenceNumber(df: pd.DataFrame, filename='bloco_sequenceNumber.html'):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    tipos = ['salto_na_sequencia', 'valor_repetido_igual', 'valor_repetido_diferente', 'reset_de_contagem', 'regressao_de_contagem']
    nomes = {
        'salto_na_sequencia': 'Saltos na Sequência',
        'valor_repetido_igual': 'Valores Repetidos para mensagens iguais',
        'valor_repetido_diferente': 'Valores Repetidos para mensagens diferentes',
        'reset_de_contagem': 'Reset de Contagem',
        'regressao_de_contagem': 'Regressão de contagem'
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
            extra_class = "linha-extra" if i >= max_linhas else ""
            if tipo in ['valor_repetido_igual', 'valor_repetido_diferente']:
                linha_val = row['linha_original']  # Usa APENAS linha_original
                linha_rep_val = row['linha_repetida_original']  # Usa APENAS linha_repetida_original
                valor_anterior = row.get('valor_anterior', '')
                valor_repetido = row.get('valor_repetido', '')
                def format_int(val):
                    return int(val) if (isinstance(val, (int, float)) and pd.notnull(val)) else ''
                valor_anterior_fmt = format_int(valor_anterior)
                valor_repetido_fmt = format_int(valor_repetido)
                linha_val_fmt = format_int(linha_val)
                linha_rep_val_fmt = format_int(linha_rep_val)
                data_tabela = f' data-tabela="tabela_seq_{tipo}"' if i >= max_linhas else ''
                style = ' style="display:none;"' if i >= max_linhas else ''
                linhas_html += f"""
                <tr class='{extra_class}'{data_tabela}{style}>
                    <td>{linha_val_fmt}</td>
                    <td>{linha_rep_val_fmt}</td>
                    <td>{valor_anterior_fmt}</td>
                    <td>{valor_repetido_fmt}</td>
                    <td>{row.get('mensagem_atual', '')}</td>
                    <td>{row.get('mensagem_repetida', '')}</td>
                    <td>{format_datetime(row.get('data_anterior_inclusao', row.get('data_anterior', '')))}</td>
                    <td>{format_datetime(row.get('data_repetida_inclusao', row.get('data_repetida', '')))}</td>
                </tr>
                """
            elif tipo == 'salto_na_sequencia':
                sequencia_anterior = row['sequencia_anterior']
                sequencia_atual = row['sequencia_atual']
                diferenca = row['diferenca']
                def format_int(val):
                    return int(val) if (isinstance(val, (int, float)) and pd.notnull(val)) else ''
                data_tabela = f' data-tabela="tabela_seq_{tipo}"' if i >= max_linhas else ''
                style = ' style="display:none;"' if i >= max_linhas else ''
                linhas_html += f"""
                <tr class='{extra_class}'{data_tabela}{style}>
                    <td>{format_int(row['linha_original'])}</td>
                    <td>{format_int(sequencia_anterior)}</td>
                    <td>{format_int(sequencia_atual)}</td>
                    <td>{row['tipo_mensagem_atual']}</td>
                    <td>{format_int(diferenca)}</td>
                </tr>
                """
            else:  # reset_de_contagem e regressao_de_contagem
                sequencia_anterior = row['sequencia_anterior']
                sequencia_atual = row['sequencia_atual']
                diferenca = row['diferenca']
                def format_int(val):
                    return int(val) if (isinstance(val, (int, float)) and pd.notnull(val)) else ''
                data_tabela = f' data-tabela="tabela_seq_{tipo}"' if i >= max_linhas else ''
                style = ' style="display:none;"' if i >= max_linhas else ''
                linhas_html += f"""
                <tr class='{extra_class}'{data_tabela}{style}>
                    <td>{format_int(row['linha_original'])}</td>
                    <td>{format_int(sequencia_anterior)}</td>
                    <td>{format_int(sequencia_atual)}</td>
                    <td>{row['tipo_mensagem_atual']}</td>
                    <td>{format_int(diferenca)}</td>
                </tr>
                """
        botao_html = ""
        if len(df_tipo) > max_linhas:
            botao_html = f'''
            <div style="text-align: center;">
                <button class="btn-mostrar-todos" data-tabela="tabela_seq_{tipo}" data-mostrando="false">Ver todos os dados</button>
            </div>
            '''
        if tipo in ['valor_repetido_igual', 'valor_repetido_diferente']:
            # Título descritivo
            tabela_titulo = f"Valores Repetidos ({'mensagem igual' if tipo == 'valor_repetido_igual' else 'mensagem diferente'})"
            tabelas[tipo] = f'''
            <div class="tabela-temporizadas-container">
                <div class="grafico-titulo-container"><span class="grafico-titulo">{tabela_titulo}</span></div>
                <table class="tabela-temporizadas" id="tabela_seq_{tipo}">
                    <thead>
                        <tr>
                            <th>Linha da primeira ocorrência</th>
                            <th>Linha da repetição detectada</th>
                            <th>Valor da primeira ocorrência</th>
                            <th>Valor da repetição detectada</th>
                            <th>Tipo de mensagem da primeira ocorrência</th>
                            <th>Tipo de mensagem da repetição detectada</th>
                            <th>Data/Hora Inclusão da primeira ocorrência</th>
                            <th>Data/Hora Inclusão da repetição detectada</th>
                        </tr>
                    </thead>
                    <tbody>
                        {linhas_html}
                    </tbody>
                </table>
                {botao_html}
            </div>
            '''
        elif tipo == 'salto_na_sequencia':
            tabela_titulo = "Saltos na Sequência"
            tabelas[tipo] = f'''
            <div class="tabela-temporizadas-container">
                <div class="grafico-titulo-container"><span class="grafico-titulo">{tabela_titulo}</span></div>
                <table class="tabela-temporizadas" id="tabela_seq_{tipo}">
                    <thead>
                        <tr>
                            <th>Linha</th>
                            <th>Valor anterior na sequência</th>
                            <th>Valor após salto</th>
                            <th>Tipo de mensagem</th>
                            <th>Tamanho do salto</th>
                        </tr>
                    </thead>
                    <tbody>
                        {linhas_html}
                    </tbody>
                </table>
                {botao_html}
            </div>
            '''
        elif tipo == 'reset_de_contagem':
            tabela_titulo = "Reset de Contagem"
            tabelas[tipo] = f'''
            <div class="tabela-temporizadas-container">
                <div class="grafico-titulo-container"><span class="grafico-titulo">{tabela_titulo}</span></div>
                <table class="tabela-temporizadas" id="tabela_seq_{tipo}">
                    <thead>
                        <tr>
                            <th>Linha</th>
                            <th>Valor antes do reset</th>
                            <th>Valor após o reset</th>
                            <th>Mensagem</th>
                            <th>Reset detectado</th>
                        </tr>
                    </thead>
                    <tbody>
                        {linhas_html}
                    </tbody>
                </table>
                {botao_html}
            </div>
            '''
        elif tipo == 'regressao_de_contagem':
            tabela_titulo = "Regressão de Contagem"
            tabelas[tipo] = f'''
            <div class="tabela-temporizadas-container">
                <div class="grafico-titulo-container"><span class="grafico-titulo">{tabela_titulo}</span></div>
                <table class="tabela-temporizadas" id="tabela_seq_{tipo}">
                    <thead>
                        <tr>
                            <th>Linha</th>
                            <th>Valor antes</th>
                            <th>Valor depois (regressão)</th>
                            <th>Mensagem</th>
                            <th>Regressão detectada</th>
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
            <div class="resumo-anomalia-titulo">Valores repetidos para mensagens iguais</div>
            <div class="resumo-anomalia-numero">{resumos.get('valor_repetido_igual', 0)}</div>
            <div class="resumo-anomalia-legenda">Repetidos com mesma mensagem</div>
        </div>
        <div class="resumo-anomalia-card">
            <div class="resumo-anomalia-titulo">Valores repetidos para mensagens diferentes</div>
            <div class="resumo-anomalia-numero">{resumos.get('valor_repetido_diferente', 0)}</div>
            <div class="resumo-anomalia-legenda">Repetidos com mensagem diferente</div>
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
    .linha-extra {
        display: none;
    }
    .resumo-anomalia-numero {
        color: #764ba2;
    }
    </style>
    '''
    js = ''
    html = f'''
    {css}
    <div class="bloco-temporizadas" id="bloco-sequenceNumber">
        <span class="dashboard-title-temporizadas">Anomalias na Sequência de Mensagens</span>
        {resumo_html}
        {tabelas.get('salto_na_sequencia', '')}
        {tabelas.get('valor_repetido_igual', '')}
        {tabelas.get('valor_repetido_diferente', '')}
        {tabelas.get('reset_de_contagem', '')}
        {tabelas.get('regressao_de_contagem', '')}
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