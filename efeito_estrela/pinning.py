import pandas as pd
import os
from haversine import haversine

def analise_pinning(df: pd.DataFrame) -> pd.DataFrame:
    """
    Executa toda a análise de pinning a partir de um DataFrame já carregado.
    Salva os CSVs de blocos e de incremento com nomes fixos.
    """
    # print(df.head(10))
    nome_arquivo = "efeito_estrela/distancia_blocos.csv"
    nome_arquivo_incremento = "efeito_estrela/distancia_blocos_incremento.csv"
    gerar_incremento = True

    # Adiciona coluna 'linha' ao DataFrame original, como no plot_distancia_incremental.py
    df = df.copy()
    if 'linha' not in df.columns:
        df['linha'] = df.index + 2

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
        df_limpo = df_limpo.sort_values(by='Data/Hora Evento').reset_index(drop=True)
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
                linha_atual = ponto['linha'] if 'linha' in ponto else ponto.name + 2
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
                        'linha': linha_atual,
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
        df_saida.to_csv(nome_arquivo, index=False, encoding='utf-8')
        # print(f"✅ Arquivo salvo: {nome_arquivo} ({len(df_saida)} registros)")
        
        if gerar_incremento:
            df_incremento = pd.DataFrame(linhas_incremento)
            df_incremento.to_csv(nome_arquivo_incremento, index=False, encoding='utf-8')
            # print(f"✅ Arquivo de incremento salvo: {nome_arquivo_incremento} ({len(df_incremento)} registros)")

    # Execução principal
    if not validar_colunas(df):
        print("\n❌ Erro: Colunas necessárias não encontradas")
        # Sobrescrever arquivos com DataFrame vazio
        colunas = ['linha','bloco','ordem_no_bloco','latitude','longitude','latitude_anterior','longitude_anterior','Hodômetro Total','Hodômetro anterior','Hodômetro incremental do bloco','Data/Hora Evento','GNSS UTC Time','Tipo Mensagem','Motion Status','Distância incremental (m)']
        pd.DataFrame(columns=colunas).to_csv(nome_arquivo, index=False, encoding='utf-8')
        pd.DataFrame(columns=colunas).to_csv(nome_arquivo_incremento, index=False, encoding='utf-8')
        return None
    
    df_processado = processar_dados(df)
    # print(df_processado.head(10))
    if len(df_processado) == 0:
        print("\n❌ Erro: Nenhum dado válido encontrado")
        # Sobrescrever arquivos com DataFrame vazio
        colunas = ['linha','bloco','ordem_no_bloco','latitude','longitude','latitude_anterior','longitude_anterior','Hodômetro Total','Hodômetro anterior','Hodômetro incremental do bloco','Data/Hora Evento','GNSS UTC Time','Tipo Mensagem','Motion Status','Distância incremental (m)']
        pd.DataFrame(columns=colunas).to_csv(nome_arquivo, index=False, encoding='utf-8')
        pd.DataFrame(columns=colunas).to_csv(nome_arquivo_incremento, index=False, encoding='utf-8')
        return None
    
    blocos_ignicao = identificar_blocos_ignicao(df_processado)
    
    if len(blocos_ignicao) == 0:
        print("\n❌ Erro: Nenhum bloco de ignição encontrado")
        # Sobrescrever arquivos com DataFrame vazio
        colunas = ['linha','bloco','ordem_no_bloco','latitude','longitude','latitude_anterior','longitude_anterior','Hodômetro Total','Hodômetro anterior','Hodômetro incremental do bloco','Data/Hora Evento','GNSS UTC Time','Tipo Mensagem','Motion Status','Distância incremental (m)']
        pd.DataFrame(columns=colunas).to_csv(nome_arquivo, index=False, encoding='utf-8')
        pd.DataFrame(columns=colunas).to_csv(nome_arquivo_incremento, index=False, encoding='utf-8')
        return None
    
    # print(f"📊 Encontrados {len(blocos_ignicao)} blocos de ignição")
    
    gerar_csv_blocos(blocos_ignicao, df_processado)
    
    try:
        df_saida = pd.read_csv(nome_arquivo, encoding='utf-8')
        # print(f"✅ Análise concluída com sucesso!")
        return df_saida
    except Exception as e:
        print(f"❌ Erro ao ler CSV de saída: {e}")
        return None

if __name__ == "__main__":
    # Exemplo de uso
    df = pd.read_csv('logs/teste.csv', encoding='utf-8', dtype=str, low_memory=False)
    resultado = analise_pinning(df)
    print(resultado)