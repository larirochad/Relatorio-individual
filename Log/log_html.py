import pandas as pd
from pathlib import Path

def gerar_bloco_log(
    csv_path='Log/logs.csv',
    filename='bloco_log.html'
):
    base_dir = Path(__file__).parent.parent / 'temp_blocos'
    base_dir.mkdir(parents=True, exist_ok=True)
    output_path = base_dir / filename

    # Lê o CSV e pega a linha de estatísticas
    df = pd.read_csv(csv_path, encoding='utf-8')
    stats_row = df[df.iloc[:,0] == 'ESTATÍSTICAS']
    if stats_row.empty:
        print('❌ Linha de estatísticas não encontrada no CSV.')
        return
    stats = stats_row.iloc[0]
    percentual_logs = stats['Percentual_Logs_Total'] if 'Percentual_Logs_Total' in stats else stats[5]
    media_delay = stats['Media_Delay_Logs'] if 'Media_Delay_Logs' in stats else stats[6]
    tipo_maior_delay = stats['Mensagem_Maior_Delay'] if 'Mensagem_Maior_Delay' in stats else stats[7]
    maior_delay = stats['Maior_Delay_Encontrado'] if 'Maior_Delay_Encontrado' in stats else stats[8]

    # Bloco HTML
    html = f'''
    <div class="bloco-temporizadas">
        <span class="dashboard-title-temporizadas">Resumo dos Logs de Mensagens</span>
        <div class="resumo-anomalias-container">
            <div class="resumo-anomalia-card">
                <div class="resumo-anomalia-titulo">Percentual de logs totais</div>
                <div class="resumo-anomalia-numero">{percentual_logs}</div>
                <div class="resumo-anomalia-legenda">em relação ao total de mensagens</div>
            </div>
            <div class="resumo-anomalia-card">
                <div class="resumo-anomalia-titulo">Média do tempo em delay</div>
                <div class="resumo-anomalia-numero">{media_delay}</div>
                <div class="resumo-anomalia-legenda">tempo médio de atraso</div>
            </div>
            <div class="resumo-anomalia-card">
                <div class="resumo-anomalia-titulo">Maior delay encontrado</div>
                <div class="resumo-anomalia-numero">{maior_delay}</div>
                <div class="resumo-anomalia-legenda">maior atraso registrado</div>
            </div>
            <div class="resumo-anomalia-card">
                <div class="resumo-anomalia-titulo">Tipo de mensagem com maior delay</div>
                <div class="resumo-anomalia-numero">{tipo_maior_delay}</div>
                <div class="resumo-anomalia-legenda">mensagem mais crítica</div>
            </div>
        </div>
    </div>
    '''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Bloco de log salvo em: {output_path.resolve()}")

if __name__ == "__main__":
    gerar_bloco_log()
