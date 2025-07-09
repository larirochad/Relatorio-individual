import pandas as pd
from pathlib import Path

def gerar_bloco_satelites(
    csv_todos='Satelites/estatisticas_gps_todos.csv',
    csv_validos='Satelites/estatisticas_gps_validos.csv',
    csv_resumo='Satelites/estatisticas_gps_resumo.csv',
    filename='bloco_satelites.html'):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    # Lê os CSVs
    df_todos = pd.read_csv(csv_todos)
    df_validos = pd.read_csv(csv_validos)
    df_resumo = pd.read_csv(csv_resumo)


    # CSS isolado
    css = """
    <style>
    .bloco-satelites {
        background: #fff;
        border-radius: 30px;
        box-shadow: 0 8px 25px rgba(102, 51, 153, 0.10);
        padding: 50px 100px 60px 100px;
        max-width: 1000px;
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
    .bloco-satelites .resumo-satelites {
        display: flex;
        justify-content: space-around;
        gap: 20px;
        margin: 20px 0 30px 0;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 1.1em;
    }
    .bloco-satelites .resumo-satelites .resumo-item {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 18px 28px;
        box-shadow: 0 2px 8px rgba(102, 51, 153, 0.07);
        text-align: center;
        min-width: 120px;
        font-weight: bold;
        color: #333;
    }
    .bloco-satelites .resumo-satelites .resumo-item.percent {
        color: #dc3545;
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
    .bloco-satelites .tabela-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    }
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
    def resumo_html(df_resumo):
        total = df_resumo.loc[df_resumo['Métrica'] == 'Total de registros', 'Valor'].values[0]
        validos = df_resumo.loc[df_resumo['Métrica'] == 'Registros válidos', 'Valor'].values[0]
        perc_invalidos = df_resumo.loc[df_resumo['Métrica'] == '% Inválidos', 'Valor'].values[0]
        return f'''
        <div class="resumo-satelites">
            <div class="resumo-item">Total de registros<br><span>{total}</span></div>
            <div class="resumo-item">Registros válidos<br><span>{validos}</span></div>
            <div class="resumo-item percent">% Inválidos<br><span>{perc_invalidos}</span></div>
        </div>
        '''

    # Função para montar tabela
    def tabela(df, titulo, legenda):
        return f'''
        <div class="tabela-container">
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
    <div class="bloco-satelites">
        <span class="dashboard-title-analise">Análise de Satélites</span>
        {resumo_html(df_resumo)}
        {tabela(df_todos, "Estatísticas - Todos os dados", "Considera todos os registros, inclusive inválidos")}
        {tabela(df_validos, "Estatísticas - Apenas válidos", "Considera apenas registros válidos (Satélites > 0 e Hdop > 0)")}
    </div>
    '''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Bloco de satélites salvo em: {output_path.resolve()}")

if __name__ == "__main__":
    gerar_bloco_satelites()