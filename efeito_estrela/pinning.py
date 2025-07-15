import pandas as pd
import os
from haversine import haversine

def analise_pinning(df: pd.DataFrame) -> pd.DataFrame:
    """
    Executa toda a análise de pinning a partir de um DataFrame já carregado.
    Salva os CSVs de blocos e de incremento com nomes fixos.
    """
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
        linhas = []
        linhas_incremento = []
        
        for i, bloco in enumerate(blocos):
            bloco = bloco.reset_index(drop=True)
            # Filtrar apenas Motion Status 21 E que não sejam HBD
            bloco_21 = bloco[bloco['Motion Status'].astype(float).astype(int) == 21].reset_index(drop=True)
            # FILTRO ADICIONAL: Remover HBD também nos blocos
            if 'Tipo Mensagem' in bloco_21.columns:
                bloco_21 = bloco_21[~bloco_21['Tipo Mensagem'].astype(str).str.upper().str.contains('HBD', na=False)].reset_index(drop=True)
            # Remover linhas sem Hodômetro Total válido
            if 'Hodômetro Total' in bloco_21.columns:
                bloco_21 = bloco_21[bloco_21['Hodômetro Total'].notna() & (bloco_21['Hodômetro Total'] != '')].reset_index(drop=True)
            if bloco_21.empty:
                continue
            
            hodo_inicial = None
            hodo_incremental = 0.0
            
            # Filtrar pontos com hodômetro válido
            pontos_validos = []
            for idx, (_, ponto) in enumerate(bloco_21.iterrows()):
                hodo_total = ponto.get('Hodômetro Total', None)
                
                # Verificar se hodômetro é válido
                try:
                    hodo_total_f = float(hodo_total)
                    # Se chegou aqui, hodômetro é válido
                    if not pd.isna(hodo_total_f):
                        pontos_validos.append((idx, ponto, hodo_total_f))
                except (TypeError, ValueError):
                    # Ignorar pontos sem hodômetro válido
                    # print(f"⚠️  Ignorando ponto na linha {ponto.get('linha', 'N/A')} - Hodômetro inválido: {hodo_total}")
                    continue
            
            # print(f"📊 Bloco {i+1}: {len(pontos_validos)} pontos válidos de {len(bloco_21)} totais")
            
            # Processar apenas pontos com hodômetro válido
            for j, (idx_original, ponto, hodo_total_f) in enumerate(pontos_validos):
                lat = float(ponto['Latitude'])
                lon = float(ponto['Longitude'])
                linha_atual = ponto['linha'] if 'linha' in ponto else ponto.name + 2

                # Definir ponto anterior (do array de pontos válidos)
                if j > 0:
                    _, ponto_anterior, hodo_ant_f = pontos_validos[j - 1]
                    lat_ant = float(ponto_anterior['Latitude'])
                    lon_ant = float(ponto_anterior['Longitude'])
                else:
                    lat_ant = None
                    lon_ant = None
                    hodo_ant_f = None

                # Calcular distância incremental
                if j == 0:
                    dist_incr = 0.0
                    hodo_inicial = hodo_total_f
                    hodo_incremental = 0.0
                    hodo_ant_f = hodo_total_f  # Ajuste: hodômetro anterior igual ao total no primeiro ponto
                else:
                    if lat_ant is not None and lon_ant is not None:
                        dist_incr = haversine((lat_ant, lon_ant), (lat, lon)) * 1000
                    else:
                        dist_incr = 0.0
                    
                    if hodo_total_f is not None and hodo_inicial is not None:
                        hodo_incremental = hodo_total_f - hodo_inicial
                    else:
                        hodo_incremental = None

                linha_saida = {
                    'linha': linha_atual,
                    'bloco': i+1,
                    'ordem_no_bloco': j+1,
                    'latitude': lat,
                    'longitude': lon,
                    'latitude_anterior': lat_ant,
                    'longitude_anterior': lon_ant,
                    'Hodômetro Total': hodo_total_f,
                    'Hodômetro anterior': hodo_ant_f,
                    'Hodômetro incremental do bloco': hodo_incremental,
                    'Data/Hora Evento': ponto['Data/Hora Evento'],
                    'GNSS UTC Time': ponto.get('GNSS UTC Time', ''),
                    'Tipo Mensagem': ponto.get('Tipo Mensagem', ''),
                    'Motion Status': ponto['Motion Status'],
                    'Distância incremental (m)': dist_incr
                }
                
                linhas.append(linha_saida)
                
                if gerar_incremento:
                    # Filtro para arquivo de incremento: apenas se hodômetro atual > anterior
                    if (isinstance(hodo_total_f, float) and isinstance(hodo_ant_f, float)
                        and not pd.isna(hodo_total_f) and not pd.isna(hodo_ant_f)
                        and hodo_total_f > hodo_ant_f):
                        linhas_incremento.append(linha_saida)
        
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
        return None
    
    df_processado = processar_dados(df)
    
    if len(df_processado) == 0:
        print("\n❌ Erro: Nenhum dado válido encontrado")
        return None
    
    blocos_ignicao = identificar_blocos_ignicao(df_processado)
    
    if len(blocos_ignicao) == 0:
        print("\n❌ Erro: Nenhum bloco de ignição encontrado")
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
    df = pd.read_csv('logs/867488065171646_decoded.csv', encoding='iso-8859-1', dtype=str, low_memory=False)
    resultado = analise_pinning(df)