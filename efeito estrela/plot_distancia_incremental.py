import pandas as pd
import os
from haversine import haversine


def ler_csv_com_encoding(caminho_csv: str):
    if not os.path.exists(caminho_csv):
        # print(f"❌ Arquivo não encontrado: {caminho_csv}")
        return None
    codificacoes = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    for encoding in codificacoes:
        try:
            # print(f"🔄 Tentando ler com encoding: {encoding}")
            df = pd.read_csv(caminho_csv, encoding=encoding, low_memory=False)
            # Adiciona coluna 'linha' com o número da linha original (começando em 2)
            df['linha'] = df.index + 2
            # print(f"✅ Arquivo lido com sucesso usando encoding: {encoding}")
            return df
        except Exception as e:
            # print(f"❌ Falha com {encoding}: {str(e)}")
            continue
    print("❌ Não foi possível ler o arquivo com nenhuma codificação testada")
    return None

def validar_colunas(df: pd.DataFrame) -> bool:
    colunas_necessarias = ['Data/Hora Evento', 'Latitude', 'Longitude', 'Motion Status']
    for coluna in colunas_necessarias:
        if coluna not in df.columns:
            print(f"❌ Coluna '{coluna}' não encontrada no CSV")
            print(f"Colunas disponíveis: {list(df.columns)}")
            return False
    # print("✅ Todas as colunas necessárias foram encontradas")
    return True

def processar_dados(df: pd.DataFrame) -> pd.DataFrame:
    # print("🔄 Processando dados...")
    df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
    df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
    df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
    df_limpo = df.dropna(subset=['Data/Hora Evento', 'Latitude', 'Longitude', 'Motion Status'])
    df_limpo = df_limpo[(df_limpo['Latitude'].abs() <= 90) & (df_limpo['Longitude'].abs() <= 180)]
    df_limpo = df_limpo.sort_values('Data/Hora Evento').reset_index(drop=True)
    # print(f"📊 Dados processados: {len(df_limpo)} registros válidos de {len(df)} originais")
    return df_limpo

def identificar_blocos_ignicao(df: pd.DataFrame):
    # print("🔄 Identificando blocos de ignição...")
    blocos = []
    bloco_atual = []
    ignicao_ligada = False
    for idx, row in df.iterrows():
        motion_status = str(row['Motion Status'])
        motion_prefix = motion_status[0] if len(motion_status) > 0 else None
        if motion_prefix == '2':
            if not ignicao_ligada:
                ignicao_ligada = True
                bloco_atual = [row]
            else:
                bloco_atual.append(row)
        elif motion_prefix == '1':
            if ignicao_ligada:
                ignicao_ligada = False
                if bloco_atual:
                    blocos.append(pd.DataFrame(bloco_atual))
                    bloco_atual = []
    if bloco_atual:
        blocos.append(pd.DataFrame(bloco_atual))
    # print(f"✅ Identificados {len(blocos)} blocos de ignição")
    return blocos

def gerar_csv_blocos(blocos, df_original, nome_arquivo="efeito estrela/distancia_blocos-todos.csv"):
    # print(f"💾 Salvando CSV como '{nome_arquivo}'...")
    linhas = []
    for i, bloco in enumerate(blocos):
        bloco = bloco.reset_index(drop=True)
        hodo_inicial = None
        hodo_incremental = 0.0
        for j, (_, ponto) in enumerate(bloco.iterrows()):
            lat = float(ponto['Latitude'])
            lon = float(ponto['Longitude'])
            hodo_total = ponto.get('Hodômetro Total', None)
            # Tenta converter o hodômetro total para float, se possível
            try:
                hodo_total_f = float(hodo_total)
            except (TypeError, ValueError):
                hodo_total_f = None
            linha_atual = ponto['linha']
            linha_anterior = linha_atual - 1
            ponto_anterior = df_original[df_original['linha'] == linha_anterior]
            if not ponto_anterior.empty:
                lat_ant = ponto_anterior.iloc[0]['Latitude']
                lon_ant = ponto_anterior.iloc[0]['Longitude']
                hodo_ant = ponto_anterior.iloc[0].get('Hodômetro Total', None)
                try:
                    hodo_ant_f = float(hodo_ant)
                except (TypeError, ValueError):
                    hodo_ant_f = ''
            else:
                lat_ant = ''
                lon_ant = ''
                hodo_ant_f = ''
            if j == 0:
                dist_incr = 0.0
                hodo_inicial = hodo_total_f
                hodo_incremental = 0.0
            else:
                dist_incr = haversine((lat_ant, lon_ant), (lat, lon)) * 1000
                # Incremento do hodômetro dentro do bloco
                if hodo_total_f is not None and hodo_inicial is not None:
                    hodo_incremental = hodo_total_f - hodo_inicial
                else:
                    hodo_incremental = ''
            linha_saida = {
                'linha': ponto['linha'],
                'bloco': i+1,
                'ordem_no_bloco': j+1,                
                'latitude': lat,
                'longitude': lon,
                'latitude_anterior': lat_ant,
                'longitude_anterior': lon_ant,
                'Hodômetro Total': hodo_total,
                'Hodômetro anterior': hodo_ant_f,
                'Hodômetro incremental do bloco': hodo_incremental,
                'Data/Hora Evento': ponto['Data/Hora Evento'],
                'GNSS UTC Time': ponto.get('GNSS UTC Time', ''),
                'Tipo Mensagem': ponto.get('Tipo Mensagem', ''),
                'Motion Status': ponto['Motion Status'],
                'Distância incremental (m)': dist_incr
            }
            linhas.append(linha_saida)
    df_saida = pd.DataFrame(linhas)
    df_saida.to_csv(nome_arquivo, index=False, encoding='utf-8')
    print(f"✅ CSV salvo com sucesso: {nome_arquivo}")

def main(caminho_csv):
    # print("🚗 Calculadora de Distâncias Incrementais por Bloco de Ignição")
    # print("=" * 50)
    df = ler_csv_com_encoding(caminho_csv)
    if df is None:
        print("\n❌ Erro: Não foi possível ler o arquivo CSV")
        return
    if not validar_colunas(df):
        print("\n❌ Erro: Colunas necessárias não encontradas")
        return
    df_processado = processar_dados(df)
    if len(df_processado) == 0:
        print("\n❌ Erro: Nenhum dado válido encontrado")
        return
    blocos_ignicao = identificar_blocos_ignicao(df_processado)
    if len(blocos_ignicao) == 0:
        print("\n⚠️  Nenhum bloco de ignição encontrado")
        return
    gerar_csv_blocos(blocos_ignicao, df)
#   print(f"\n📈 {sum(len(b) for b in blocos_ignicao)} linhas processadas. FIM.")

if __name__ == "__main__":
    main("logs/867488065171646_novo.csv")

    # --- Plotar e salvar o gráfico da distância incremental ---
    import matplotlib.pyplot as plt
    import pandas as pd

    csv_path = "efeito estrela/distancia_blocos.csv"
    output_img = "efeito estrela/distancia_incremental_plot.png"

    df_plot = pd.read_csv(csv_path)
    y = df_plot['Distância incremental (m)'].to_numpy()
    x = range(1, len(y) + 1)

    # --- Estatísticas solicitadas (antes do gráfico) ---
    media_dist = y.mean()
    # Seleciona apenas valores >= 45 e <= 500000
    pontos_filtrados = [(i+1, val) for i, val in enumerate(y) if 40 <= val <= 500000]
    print('O total de pontos é: ', len(pontos_filtrados))
    # Considera apenas valores únicos
    valores_unicos = {}
    for idx, val in pontos_filtrados:
        if round(val, 4) not in valores_unicos:
            valores_unicos[round(val, 4)] = idx
    soma_maior_45 = sum(val for val in valores_unicos.keys())
    print(f"Média de todas as distâncias incrementais: {media_dist:.2f} m")
    print(f"Soma das distâncias incrementais únicas >= 45 m e <= 500000 m: {soma_maior_45:.4f} m")
    print("Pontos (primeira ocorrência) com distância >= 45 m e <= 500000 m:")
    for val, idx in valores_unicos.items():
        print(f"  Ponto {idx}: {val:.2f} m")

    # --- Plotar e salvar o gráfico da distância incremental ---
    # Filtrar para o gráfico: apenas valores entre 0 (exclusivo) e 500000 (inclusivo)
    y_plot = [val for val in y if 0 < val <= 500000]
    x_plot = list(range(1, len(y_plot) + 1))

    plt.figure(figsize=(12, 5))
    plt.plot(x_plot, y_plot, marker='o', linestyle='-', color='blue', alpha=0.7)
    plt.axhline(40, color='red', linestyle='--', linewidth=2, label='Limite 40m')
    plt.title('Distância incremental entre pontos')
    plt.xlabel('Índice sequencial do ponto válido')
    plt.ylabel('Distância incremental (m)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_img, dpi=200)
    print(f'Gráfico salvo como {output_img}')
    plt.show()