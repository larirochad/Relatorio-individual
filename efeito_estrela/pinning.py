import pandas as pd
import os
from haversine import haversine

def organizar_dados_por_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Organiza os dados tratando o problema de datas de 2019, mantendo a linha original
    """
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()

    # Garantir que temos a linha original
    if 'linha_original' not in df.columns:
        df['linha_original'] = df.index + 2

    # Conversões básicas
    df['data/hora evento'] = pd.to_datetime(df['data/hora evento'], errors='coerce')
    df['sequência'] = pd.to_numeric(df['sequência'], errors='coerce')
    df['hodômetro total'] = pd.to_numeric(df['hodômetro total'], errors='coerce')

    # Remove linhas sem data/hora ou sequência válidas
    df = df.dropna(subset=['data/hora evento', 'sequência']).copy()

    # Identifica registros com datas problemáticas (2019)
    df['data_problematica'] = df['data/hora evento'].dt.year == 2019
    
    # Separa os dados normais e problemáticos
    df_normais = df[~df['data_problematica']].copy()
    df_problematicos = df[df['data_problematica']].copy()
    
    if len(df_normais) == 0:
        print("⚠️  Todos os registros têm datas problemáticas!")
        return pd.DataFrame()
    
    # Ordena os dados normais por data/hora e sequência e reseta o índice
    df_normais = df_normais.sort_values(['data/hora evento', 'sequência']).reset_index(drop=True)
    
    # Lista para armazenar todos os registros na ordem correta
    registros_ordenados = []
    registros_ordenados.extend(df_normais.to_dict('records'))
    
    # Para cada registro problemático, encontra a melhor posição
    for _, row_prob in df_problematicos.iterrows():
        seq_prob = row_prob['sequência']
        melhor_posicao = 0
        menor_diff = float('inf')
        
        # Encontra a melhor posição comparando com os registros já ordenados
        for i, reg in enumerate(registros_ordenados):
            diff = abs(reg['sequência'] - seq_prob)
            if diff < menor_diff:
                menor_diff = diff
                melhor_posicao = i
        
        # Insere o registro problemático na posição correta
        if seq_prob > registros_ordenados[melhor_posicao]['sequência']:
            melhor_posicao += 1
        registros_ordenados.insert(melhor_posicao, row_prob.to_dict())
    
    # Converte a lista de registros de volta para DataFrame
    df_ordenado = pd.DataFrame(registros_ordenados)
    
    # Remove colunas auxiliares mas mantém linha_original
    df_ordenado = df_ordenado.drop(columns=['data_problematica'])
    
    # Restaura nomes das colunas para o padrão original
    df_ordenado.columns = df_ordenado.columns.str.title().str.replace('_', ' ')
    df_ordenado = df_ordenado.rename(columns={
        'Data/Hora Evento': 'Data/Hora Evento',
        'Hodometro Total': 'Hodômetro Total',
        'Sequencia': 'Sequência',
        'Linha Original': 'linha_original'  # Mantém o nome em minúsculo para identificação
    })
    
    # Salva o DataFrame ordenado para debug
    # df_ordenado.to_csv('efeito_estrela/debug_dados_ordenados.csv', index=False, encoding='utf-8')
    # print(f"✅ Dados ordenados salvos em 'efeito_estrela/debug_dados_ordenados.csv' para análise")
    
    return df_ordenado

def analise_pinning(df: pd.DataFrame) -> pd.DataFrame:
    """
    Executa toda a análise de pinning a partir de um DataFrame já carregado.
    Salva os CSVs de blocos e de incremento com nomes fixos.
    """
    nome_arquivo = "efeito_estrela/distancia_blocos.csv"
    nome_arquivo_incremento = "efeito_estrela/distancia_blocos_incremento.csv"
    gerar_incremento = True

    # Adiciona coluna linha_original ao DataFrame original
    df = df.copy()
    if 'linha_original' not in df.columns:
        df['linha_original'] = df.index + 2

    # Organiza os dados tratando o problema de datas de 2019
    df = organizar_dados_por_data(df)
    if df.empty:
        print("\n❌ Erro: Falha na organização dos dados")
        colunas = ['linha','bloco','ordem_no_bloco','latitude','longitude','latitude_anterior','longitude_anterior','Hodômetro Total','Hodômetro anterior','Hodômetro incremental do bloco','Data/Hora Evento','GNSS UTC Time','Tipo Mensagem','Motion Status','Distância incremental (m)']
        # pd.DataFrame(columns=colunas).to_csv(nome_arquivo, index=False, encoding='utf-8')
        # pd.DataFrame(columns=colunas).to_csv(nome_arquivo_incremento, index=False, encoding='utf-8')
        return None

    # # Após processar os dados, salva para debug
    # df.to_csv('efeito_estrela/debug_dados_processados.csv', index=False, encoding='utf-8')
    # print(f"✅ Dados processados salvos em 'efeito_estrela/debug_dados_processados.csv' para análise")

    def validar_colunas(df: pd.DataFrame) -> bool:
        colunas_necessarias = ['Data/Hora Evento', 'Latitude', 'Longitude', 'Motion Status']
        for coluna in colunas_necessarias:
            if coluna not in df.columns:
                print(f"❌ Coluna '{coluna}' não encontrada no DataFrame")
                return False
        return True

    def processar_dados(df: pd.DataFrame) -> pd.DataFrame:
        df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
        df_limpo = df.dropna(subset=['Data/Hora Evento', 'Latitude', 'Longitude', 'Motion Status'])
        
        df_limpo = df_limpo[df_limpo['Latitude'].astype(float).abs() <= 90].copy()
        df_limpo = df_limpo[df_limpo['Longitude'].astype(float).abs() <= 180].copy()
        # Não reordenar aqui, manter a ordem definida pela organização de datas
        # Remover linhas sem Hodômetro Total válido
        if 'Hodômetro Total' in df_limpo.columns:
            df_limpo = df_limpo[df_limpo['Hodômetro Total'].notna() & (df_limpo['Hodômetro Total'] != '')].copy()
        return df_limpo

    def identificar_blocos_ignicao(df: pd.DataFrame):
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
        
        return blocos

    def gerar_csv_blocos(blocos, df_original):
        def is_zero_latlon(val):
            val_str = str(val).replace('.', '').replace(' ', '').replace('-', '').lstrip('0')
            return val_str == ''
        linhas = []
        linhas_incremento = []
        
        for i, bloco in enumerate(blocos):
            bloco = bloco.reset_index(drop=True)
            # Remover HBD do bloco inteiro (para evitar problemas de hodômetro)
            if 'Tipo Mensagem' in bloco.columns:
                bloco = bloco[~bloco['Tipo Mensagem'].astype(str).str.upper().str.contains('HBD', na=False)].reset_index(drop=True)
            # Remover linhas sem Hodômetro Total válido
            if 'Hodômetro Total' in bloco.columns:
                bloco = bloco[bloco['Hodômetro Total'].notna() & (bloco['Hodômetro Total'] != '')].reset_index(drop=True)
            if bloco.empty:
                continue

            hodo_inicial = None
            hodo_incremental = 0.0
            ultimo_ponto_valido = None  # (lat, lon, hodo, linha, data, motion, tipo_msg, gnss_utc)
            hodo_ant_f = None

            for idx, ponto in bloco.iterrows():
                try:
                    hodo_total_f = float(ponto['Hodômetro Total'])
                    if pd.isna(hodo_total_f):
                        continue
                except (TypeError, ValueError):
                    continue

                lat = ponto['Latitude']
                lon = ponto['Longitude']

                if is_zero_latlon(lat) or is_zero_latlon(lon):
                    # Zera último ponto válido pois não queremos transição de/para zero
                    ultimo_ponto_valido = None
                    continue  # pula esse ponto

                lat = float(lat)
                lon = float(lon)
                # Usar linha_original em vez de linha
                linha_atual = ponto['linha_original']
                motion_status = int(float(ponto['Motion Status']))
                tipo_msg = ponto.get('Tipo Mensagem', '')
                gnss_utc = ponto.get('GNSS UTC Time', '')
                data_evento = ponto['Data/Hora Evento']

                if ultimo_ponto_valido is not None:
                    lat_ant, lon_ant, hodo_ant_f, linha_ant, data_ant, motion_ant, tipo_ant, gnss_ant = ultimo_ponto_valido
                    dist_incr = haversine((lat_ant, lon_ant), (lat, lon)) * 1000
                    if hodo_inicial is not None:
                        hodo_incremental = hodo_total_f - hodo_inicial
                    else:
                        hodo_incremental = 0.0
                else:
                    dist_incr = 0.0
                    hodo_incremental = 0.0
                    hodo_inicial = hodo_total_f
                    hodo_ant_f = hodo_total_f

                if motion_status == 21 and ultimo_ponto_valido is not None and hodo_ant_f is not None and not pd.isna(hodo_ant_f):
                    linha_saida = {
                        'linha': linha_atual,  # Agora usando linha_original
                        'bloco': i+1,
                        'ordem_no_bloco': idx+1,
                        'latitude': lat,
                        'longitude': lon,
                        'latitude_anterior': lat_ant,
                        'longitude_anterior': lon_ant,
                        'Hodômetro Total': hodo_total_f,
                        'Hodômetro anterior': hodo_ant_f,
                        'Hodômetro incremental do bloco': hodo_incremental,
                        'Data/Hora Evento': data_evento,
                        'GNSS UTC Time': gnss_utc,
                        'Tipo Mensagem': tipo_msg,
                        'Motion Status': motion_status,
                        'Distância incremental (m)': dist_incr
                    }
                    linhas.append(linha_saida)

                    if (hodo_total_f > hodo_ant_f and dist_incr > 40):
                        linhas_incremento.append(linha_saida)

                # Atualiza apenas se o ponto atual for válido
                ultimo_ponto_valido = (lat, lon, hodo_total_f, linha_atual, data_evento, motion_status, tipo_msg, gnss_utc)
                hodo_ant_f = hodo_total_f

        # Criar diretório se não existir
        os.makedirs(os.path.dirname(nome_arquivo), exist_ok=True)
        
        df_saida = pd.DataFrame(linhas)
        # df_saida.to_csv(nome_arquivo, index=False, encoding='utf-8')
        
        if gerar_incremento:
            df_incremento = pd.DataFrame(linhas_incremento)
            # df_incremento.to_csv(nome_arquivo_incremento, index=False, encoding='utf-8')

    # Execução principal
    if not validar_colunas(df):
        print("\n❌ Erro: Colunas necessárias não encontradas")
        colunas = ['linha','bloco','ordem_no_bloco','latitude','longitude','latitude_anterior','longitude_anterior','Hodômetro Total','Hodômetro anterior','Hodômetro incremental do bloco','Data/Hora Evento','GNSS UTC Time','Tipo Mensagem','Motion Status','Distância incremental (m)']
        # pd.DataFrame(columns=colunas).to_csv(nome_arquivo, index=False, encoding='utf-8')
        # pd.DataFrame(columns=colunas).to_csv(nome_arquivo_incremento, index=False, encoding='utf-8')
        return None
    
    df_processado = processar_dados(df)
    if len(df_processado) == 0:
        print("\n❌ Erro: Nenhum dado válido encontrado")
        # colunas = ['linha','bloco','ordem_no_bloco','latitude','longitude','latitude_anterior','longitude_anterior','Hodômetro Total','Hodômetro anterior','Hodômetro incremental do bloco','Data/Hora Evento','GNSS UTC Time','Tipo Mensagem','Motion Status','Distância incremental (m)']
        # pd.DataFrame(columns=colunas).to_csv(nome_arquivo, index=False, encoding='utf-8')
        # pd.DataFrame(columns=colunas).to_csv(nome_arquivo_incremento, index=False, encoding='utf-8')
        return None
    
    blocos_ignicao = identificar_blocos_ignicao(df_processado)
    
    if len(blocos_ignicao) == 0:
        print("\n❌ Erro: Nenhum bloco de ignição encontrado")
        colunas = ['linha','bloco','ordem_no_bloco','latitude','longitude','latitude_anterior','longitude_anterior','Hodômetro Total','Hodômetro anterior','Hodômetro incremental do bloco','Data/Hora Evento','GNSS UTC Time','Tipo Mensagem','Motion Status','Distância incremental (m)']
        # pd.DataFrame(columns=colunas).to_csv(nome_arquivo, index=False, encoding='utf-8')
        # pd.DataFrame(columns=colunas).to_csv(nome_arquivo_incremento, index=False, encoding='utf-8')
        return None
    
    gerar_csv_blocos(blocos_ignicao, df_processado)
    
    try:
        df_saida = pd.read_csv(nome_arquivo, encoding='utf-8')
        return df_saida
    except Exception as e:
        print(f"❌ Erro ao ler CSV de saída: {e}")
        return None

if __name__ == "__main__":
    # Exemplo de uso
    df = pd.read_csv('logs/867488061438387_decoded.csv', encoding='latin-1', dtype=str, low_memory=False)
    resultado = analise_pinning(df)
    print(resultado)