import pandas as pd
import numpy as np

def viagens(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [col.strip() for col in df.columns]
    df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
    df = df.dropna(subset=['Data/Hora Evento'])
    df = df.sort_values('Data/Hora Evento')
    df['Dia'] = df['Data/Hora Evento'].dt.strftime('%d/%m/%Y')
    # Padronizar coluna Hodômetro Total para float, se existir
    if 'Hodômetro Total' in df.columns:
        df['Hodômetro Total'] = pd.to_numeric(df['Hodômetro Total'], errors='coerce')

    def get_evento(row):
        tipo = str(row.get('Tipo Mensagem', '')).strip().upper()
        codigo = str(row.get('Event Code', '')).strip()
        if tipo:
            return tipo
        elif codigo:
            mapa = {'20': 'GTIGF', '21': 'GTIGN'}
            return mapa.get(codigo, '')
        return ''

    def extrair_viagens(df):
        df = df.copy()
        # print(df.columns)
        df.columns = [col.strip() for col in df.columns]
        df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
        df = df.dropna(subset=['Data/Hora Evento'])
        df = df.sort_values('Data/Hora Evento')
        df['Dia'] = df['Data/Hora Evento'].dt.strftime('%d/%m/%Y')
        # Padronizar coluna Hodômetro Total para float, se existir
        if 'Hodômetro Total' in df.columns:
            df['Hodômetro Total'] = pd.to_numeric(df['Hodômetro Total'], errors='coerce')

        ignicoes = df[df.apply(lambda row: get_evento(row) == 'GTIGN', axis=1)].reset_index(drop=True)
        desligamentos = df[df.apply(lambda row: get_evento(row) == 'GTIGF', axis=1)].reset_index(drop=True)

        viagens = []

        # --- Viagens por eventos GTIGN/GTIGF (como já está) ---
        viagens_gtign = set()
        for i, ign in ignicoes.iterrows():
            ign_time = ign['Data/Hora Evento']
            ign_odometro = pd.to_numeric(ign.get('Hodômetro Total', 0), errors='coerce')
            dia_formatado = ign_time.strftime('%d/%m/%Y')
            next_ign_time = ignicoes.iloc[i + 1]['Data/Hora Evento'] if i + 1 < len(ignicoes) else pd.Timestamp.max
            igfs_possiveis = desligamentos[
                (desligamentos['Data/Hora Evento'] > ign_time) &
                (desligamentos['Data/Hora Evento'] < next_ign_time)
            ]
            if not bool(pd.notna(ign_odometro)):
                continue
            if not pd.api.types.is_scalar(ign_odometro):
                continue
            if not (isinstance(ign_odometro, (int, float))):
                continue
            if not igfs_possiveis.empty:
                igf = igfs_possiveis.iloc[0]
                igf_time = igf['Data/Hora Evento']
                igf_odometro = pd.to_numeric(igf.get('Hodômetro Total', 0), errors='coerce')
                if not bool(pd.notna(igf_odometro)):
                    continue
                if not pd.api.types.is_scalar(igf_odometro):
                    continue
                if not (isinstance(igf_odometro, (int, float))):
                    continue
                try:
                    ign_odometro_float = float(ign_odometro)
                    igf_odometro_float = float(igf_odometro)
                    km = igf_odometro_float - ign_odometro_float
                    viagens.append({
                        'Dia': dia_formatado,
                        'IGN': ign_time,
                        'IGF': igf_time,
                        'Distancia_km': km
                    })
                    viagens_gtign.add((ign_time, igf_time))
                except (ValueError, TypeError):
                    continue

        # --- Viagens por Motion Status e variação do hodômetro ---
        # Considera apenas trechos não cobertos acima
        df = df.sort_values('Data/Hora Evento')
        in_viagem = False
        start_idx = None
        for idx, row in df.iterrows():
            motion = str(row.get('Motion Status', '')).strip()
            hodometro = pd.to_numeric(row.get('Hodômetro Total', 0), errors='coerce')
            datahora = row['Data/Hora Evento']
            dia = datahora.strftime('%d/%m/%Y')
            if not bool(pd.notna(hodometro)) or not pd.api.types.is_scalar(hodometro) or not isinstance(hodometro, (int, float)):
                continue
            if motion.startswith('2') and not in_viagem:
                # Início de viagem
                in_viagem = True
                start_idx = idx
                start_time = datahora
                start_hodo = hodometro
                start_dia = dia
            elif (motion.startswith('1') or dia != start_dia) and in_viagem:
                # Fim de viagem
                end_time = datahora
                end_hodo = hodometro
                # Não sobrepor viagens já detectadas
                if start_time != end_time and (start_time, end_time) not in viagens_gtign:
                    km = end_hodo - start_hodo
                    viagens.append({
                        'Dia': start_dia,
                        'IGN': start_time,
                        'IGF': end_time,
                        'Distancia_km': km
                    })
                in_viagem = False
                start_idx = None
        # Se acabar o arquivo e ainda estiver em viagem, ignora o bloco incompleto
                            
        return pd.DataFrame(viagens)

    def classificar(dist):
        if dist < 0:
            return 'Ignorar'
        elif dist <= 2:
            return 'Curta'
        elif dist <= 50:
            return 'Media'
        else:
            return 'Longa'

    viagens_teste = extrair_viagens(df)
    if not viagens_teste.empty and 'Distancia_km' in viagens_teste.columns:
        viagens_teste['Categoria'] = viagens_teste['Distancia_km'].apply(classificar)
    else:
        viagens_teste['Categoria'] = []

    if not viagens_teste.empty and 'Dia' in viagens_teste.columns:
        dias_todos = sorted(
            viagens_teste['Dia'].unique(),
            key=lambda x: pd.to_datetime(x, dayfirst=True)
        )
    else:
        dias_todos = []

    resultados = []
    for dia in dias_todos:
        linha = {'Dia': dia}
        for categoria in ['Curta', 'Media', 'Longa']:
            soma_teste = viagens_teste[
                (viagens_teste['Dia'] == dia) & (viagens_teste['Categoria'] == categoria)
            ]['Distancia_km'].sum()
            linha[categoria] = round(soma_teste, 2)
        resultados.append(linha)

    resultado_df = pd.DataFrame(resultados)
    if not resultado_df.empty and 'Dia' in resultado_df.columns:
        resultado_df['Dia'] = pd.to_datetime(resultado_df['Dia'], format='%d/%m/%Y')
        resultado_df = resultado_df.sort_values(by='Dia')
        resultado_df['Dia'] = resultado_df['Dia'].dt.strftime('%d/%m/%Y')

    # Salvando em CSV
    # resultado_df.to_csv(caminho_saida, index=False, encoding='utf-8-sig') # This line was removed as per the edit hint
    # print(f"✅ Planilha salva em: {caminho_saida}") # This line was removed as per the edit hint
    # print(resultado_df)
    return resultado_df

if __name__ == "__main__":
    df = pd.read_csv('logs/867488061434766_decoded.csv', encoding='iso-8859-1', dtype=str, low_memory=False)

    if 'Hodômetro Total' in df.columns:
        df['Hodômetro Total'] = (
            df['Hodômetro Total']
            .astype(str)
            .str.replace(',', '.')
            .str.replace(r'[^\d\.]', '', regex=True)
        )
        df['Hodômetro Total'] = pd.to_numeric(df['Hodômetro Total'], errors='coerce')
    viagens(df) 
