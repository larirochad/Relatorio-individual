import pandas as pd
from pathlib import Path
from typing import Union

def gerar_bloco_satelites(df_todos: pd.DataFrame, df_validos: pd.DataFrame, df_invalidos: pd.DataFrame, df_resumo: pd.DataFrame, filename='bloco_satelites.html'):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    # Calcular resumo para inválidos
    total_registros = df_resumo.loc[df_resumo['Métrica'] == 'Total de registros', 'Valor'].values[0]
    registros_invalidos = total_registros - df_resumo.loc[df_resumo['Métrica'] == 'Registros válidos', 'Valor'].values[0]
    perc_invalidos = 100 - float(str(df_resumo.loc[df_resumo['Métrica'] == '% Válidos', 'Valor'].values[0]).replace('%',''))
    resumo_invalidos = [
        {'Métrica': 'Total de registros', 'Valor': total_registros},
        {'Métrica': 'Registros inválidos', 'Valor': registros_invalidos},
        {'Métrica': '% Inválidos', 'Valor': f"{perc_invalidos:.1f}%"}
    ]

    # CSS isolado
    css = """
    <style>
    .bloco-satelites {
        background: #fff;
        border-radius: 30px;
        box-shadow: 0 8px 25px rgba(102, 51, 153, 0.10);
        padding: 50px 100px 60px 100px;
        max-width: 2000px;
        margin: 0 auto 40px auto;
    }
    .bloco-satelites .dashboard-title-analise {
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
    .satelites-btn-container {
        display: flex;
        justify-content: center;
        gap: 16px;
        margin-bottom: 24px;
    }
    .satelites-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 8px 22px;
        cursor: pointer;
        font-size: 1em;
        font-weight: 500;
        font-family: 'Saira', sans-serif;
        font-weight: 700;
        box-shadow: 0 2px 8px rgba(102,51,153,0.07);
        transition: all 0.3s ease;
    }
    .satelites-btn.active, .satelites-btn:focus {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        outline: none;
    }
    .satelites-btn:hover {
        transform: translateY(-2px);
        opacity: 0.9;
    }
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
        color: #222;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .resumo-anomalia-numero {
        font-size: 2em;
        font-weight: bold;
        color: #764ba2;
        margin-bottom: 2px;
    }
    .resumo-anomalia-numero.red {
        color: #dc3545 !important;
    }
    .resumo-anomalia-legenda {
        font-size: 0.95em;
        color: #888;
    }
    .bloco-satelites .tabela-container {
        background: #fff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        margin-bottom: 30px;
        overflow-x: auto;
        transition: box-shadow 0.3s, transform 0.3s;
    }
    .bloco-satelites .tabela-container:hover { transform: translateY(-2px); box-shadow: 0 15px 35px rgba(0,0,0,0.15); transition: box-shadow 0.3s, transform 0.3s;}
    .bloco-satelites .tabela-estatisticas {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 1em;
        margin: 0 auto;
    }
    .bloco-satelites .tabela-estatisticas th, .bloco-satelites .tabela-estatisticas td {
        border: 1px solid #e9ecef;
        padding: 12px 18px;
        text-align: center;
    }
    .bloco-satelites .tabela-estatisticas th {
        background: #f8f9fa;
        color: #495057;
        font-weight: bold;
    }
    .bloco-satelites .grafico-titulo-container {
        text-align: center;
        margin-bottom: 10px;
    }
    .bloco-satelites .grafico-titulo {
        text-align: center;
        color: #495057;
        margin: 0;
        font-size: 1.5em;
        padding: 10px 25px;
        background: #f8f9fa;
        border-radius: 20px;
        display: inline-block;  
    }
    .bloco-satelites .faixa-legenda {
        text-align: center;
        font-size: 14px;
        color: #898989;
        margin-bottom: 18px;
        background: #f8f9fa;
        font-weight: 500;
        border-radius: 10px;
        padding: 10px;
        margin-top: 8px;
    }
    </style>
    """

    # Resumo
    def resumo_html(df_resumo, tipo='validos'):
        if tipo == 'validos':
            total = df_resumo.loc[df_resumo['Métrica'] == 'Total de registros', 'Valor'].values[0]
            validos = df_resumo.loc[df_resumo['Métrica'] == 'Registros válidos', 'Valor'].values[0]
            perc_validos = df_resumo.loc[df_resumo['Métrica'] == '% Válidos', 'Valor'].values[0]
            return f'''
            <div class="resumo-anomalias-container" id="resumo-validos" style="display:flex;">
                <div class="resumo-anomalia-card">
                    <div class="resumo-anomalia-titulo">Total de registros</div>
                    <div class="resumo-anomalia-numero">{total}</div>
                    <div class="resumo-anomalia-legenda">Total de dados recebidos</div>
                </div>
                <div class="resumo-anomalia-card">
                    <div class="resumo-anomalia-titulo">Registros válidos</div>
                    <div class="resumo-anomalia-numero">{validos}</div>
                    <div class="resumo-anomalia-legenda">Satélites > 0 e Hdop > 0</div>
                </div>
                <div class="resumo-anomalia-card">
                    <div class="resumo-anomalia-titulo">Porcentagem de registros Válidos</div>
                    <div class="resumo-anomalia-numero red" style="color:#38b349 !important;">{perc_validos}</div>
                    <div class="resumo-anomalia-legenda">Proporção de dados válidos</div>
                </div>
            </div>
            '''
        else:
            total = resumo_invalidos[0]['Valor']
            invalidos = resumo_invalidos[1]['Valor']
            perc_inv = resumo_invalidos[2]['Valor']
            return f'''
            <div class="resumo-anomalias-container" id="resumo-invalidos" style="display:none;">
                <div class="resumo-anomalia-card">
                    <div class="resumo-anomalia-titulo">Total de registros</div>
                    <div class="resumo-anomalia-numero">{total}</div>
                    <div class="resumo-anomalia-legenda">Total de dados recebidos</div>
                </div>
                <div class="resumo-anomalia-card">
                    <div class="resumo-anomalia-titulo">Registros inválidos</div>
                    <div class="resumo-anomalia-numero">{invalidos}</div>
                    <div class="resumo-anomalia-legenda"> Hdop = 0</div>
                </div>
                <div class="resumo-anomalia-card">
                    <div class="resumo-anomalia-titulo">Porcentagem de registros Inválidos</div>
                    <div class="resumo-anomalia-numero red">{perc_inv}</div>
                    <div class="resumo-anomalia-legenda">Proporção de dados inválidos</div>
                </div>
            </div>
            '''

    # Função para montar tabela
    def tabela(df, titulo, legenda, id_tabela):
        return f'''
        <div class="tabela-container" id="{id_tabela}" style="display:none;">
            <div class="grafico-titulo-container">
                <h3 class="grafico-titulo">{titulo}</h3>
            </div>
            <div class="faixa-legenda">{legenda}</div>
            <table class="tabela-estatisticas">
                <thead>
                    <tr>
                        <th>Dado</th>
                        <th>Média</th>
                        <th>Moda</th>
                        <th>Desvio Padrão</th>
                        <th>Valor máximo</th>
                        <th>Valor mínimo</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Satélites</td>
                        <td>{df.loc[df['Dado']=='Satélites','Média'].values[0]}</td>
                        <td>{df.loc[df['Dado']=='Satélites','Moda'].values[0]}</td>
                        <td>{df.loc[df['Dado']=='Satélites','Desvio Padrão'].values[0]}</td>
                        <td>{df.loc[df['Dado']=='Satélites','Valor máximo'].values[0]}</td>
                        <td>{df.loc[df['Dado']=='Satélites','Valor mínimo'].values[0]}</td>
                    </tr>
                    <tr>
                        <td>HDOP</td>   
                        <td>{df.loc[df['Dado']=='Hdop','Média'].values[0]}</td>         
                        <td>{df.loc[df['Dado']=='Hdop','Moda'].values[0]}</td>  
                        <td>{df.loc[df['Dado']=='Hdop','Desvio Padrão'].values[0]}</td>
                        <td>{df.loc[df['Dado']=='Hdop','Valor máximo'].values[0]}</td>
                        <td>{df.loc[df['Dado']=='Hdop','Valor mínimo'].values[0]}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        '''

    html = f'''
    {css}
    <div class="bloco-satelites" id="bloco-satelites">
        <span class="dashboard-title-analise">Análise de Satélites</span>
        <div class="satelites-btn-container">
            <button class="satelites-btn active" id="btn-validos" onclick="mostrarTabelaSatelites('validos')">Válidos</button>
            <button class="satelites-btn" id="btn-invalidos" onclick="mostrarTabelaSatelites('invalidos')">Inválidos</button>
        </div>
        {resumo_html(df_resumo, 'validos')}
        {resumo_html(df_resumo, 'invalidos')}
        <div id="tabelas-satelites">
            <div class="tabela-container" id="tabela-todos" style="display:block;">
                <div class="grafico-titulo-container">
                    <h3 class="grafico-titulo">Estatísticas - Todos os dados</h3>
                </div>
                <div class="faixa-legenda">Considera todos os registros, inclusive inválidos</div>
                <table class="tabela-estatisticas">
                    <thead>
                        <tr>
                            <th>Dado</th>
                            <th>Média</th>
                            <th>Moda</th>
                            <th>Desvio Padrão</th>
                            <th>Valor máximo</th>
                            <th>Valor mínimo</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Satélites</td>
                            <td>{df_todos.loc[df_todos['Dado']=='Satélites','Média'].values[0]}</td>
                            <td>{df_todos.loc[df_todos['Dado']=='Satélites','Moda'].values[0]}</td>
                            <td>{df_todos.loc[df_todos['Dado']=='Satélites','Desvio Padrão'].values[0]}</td>
                            <td>{df_todos.loc[df_todos['Dado']=='Satélites','Valor máximo'].values[0]}</td>
                            <td>{df_todos.loc[df_todos['Dado']=='Satélites','Valor mínimo'].values[0]}</td>
                        </tr>
                        <tr>
                            <td>HDOP</td>   
                            <td>{df_todos.loc[df_todos['Dado']=='Hdop','Média'].values[0]}</td>         
                            <td>{df_todos.loc[df_todos['Dado']=='Hdop','Moda'].values[0]}</td>  
                            <td>{df_todos.loc[df_todos['Dado']=='Hdop','Desvio Padrão'].values[0]}</td>
                            <td>{df_todos.loc[df_todos['Dado']=='Hdop','Valor máximo'].values[0]}</td>
                            <td>{df_todos.loc[df_todos['Dado']=='Hdop','Valor mínimo'].values[0]}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            {tabela(df_validos, "Estatísticas - Apenas válidos", "Considera apenas registros válidos (Satélites > 0 e Hdop > 0)", "tabela-validos")}
            {tabela(df_invalidos, "Estatísticas - Apenas inválidos", "Considera apenas registros inválidos (Hdop = 0)", "tabela-invalidos")}
        </div>
    </div>
    <script>
    function mostrarTabelaSatelites(tipo) {{
        document.getElementById('tabela-validos').style.display = (tipo === 'validos') ? 'block' : 'none';
        document.getElementById('tabela-invalidos').style.display = (tipo === 'invalidos') ? 'block' : 'none';
        document.getElementById('btn-validos').classList.toggle('active', tipo === 'validos');
        document.getElementById('btn-invalidos').classList.toggle('active', tipo === 'invalidos');
        document.getElementById('resumo-validos').style.display = (tipo === 'validos') ? 'flex' : 'none';
        document.getElementById('resumo-invalidos').style.display = (tipo === 'invalidos') ? 'flex' : 'none';
    }}
    // Inicialmente mostra válidos
    mostrarTabelaSatelites('validos');
    </script>
    '''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # print(f"✅ Bloco de satélites salvo em: {output_path.resolve()}")

if __name__ == "__main__":
    # Exemplo de uso (substitua com seus DataFrames)
    # df_todos = pd.read_csv('Satelites/estatisticas_gps_todos.csv')
    # df_validos = pd.read_csv('Satelites/estatisticas_gps_validos.csv')
    # df_resumo = pd.read_csv('Satelites/estatisticas_gps_resumo.csv')

    # gerar_bloco_satelites(df_todos, df_validos, df_resumo)
    pass # Removido o exemplo de uso para evitar leitura de arquivos