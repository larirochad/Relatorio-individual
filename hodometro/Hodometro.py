import pandas as pd

def viagens(caminho_csv, caminho_saida='hodometro/resultado_viagens.csv'):
    try:
        codificacoes = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        for encoding in codificacoes:
            try:
                df = pd.read_csv(caminho_csv, encoding=encoding, low_memory=False)
                break
            except UnicodeDecodeError:
                continue
        else:
            print("❌ Erro: Não foi possível ler o arquivo com as codificações testadas.")
            return

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
            df.columns = [col.strip() for col in df.columns]
            df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
            df = df.dropna(subset=['Data/Hora Evento'])
            df = df.sort_values('Data/Hora Evento')
            df['Dia'] = df['Data/Hora Evento'].dt.strftime('%d/%m/%Y')

            ignicoes = df[df.apply(lambda row: get_evento(row) == 'GTIGN', axis=1)].reset_index(drop=True)
            desligamentos = df[df.apply(lambda row: get_evento(row) == 'GTIGF', axis=1)].reset_index(drop=True)

            viagens = []

            for i, ign in ignicoes.iterrows():
                ign_time = ign['Data/Hora Evento']
                ign_odometro = pd.to_numeric(ign.get('Hodômetro Total', 0), errors='coerce')
                dia_formatado = ign_time.strftime('%d/%m/%Y')

                next_ign_time = ignicoes.iloc[i + 1]['Data/Hora Evento'] if i + 1 < len(ignicoes) else pd.Timestamp.max

                igfs_possiveis = desligamentos[
                    (desligamentos['Data/Hora Evento'] > ign_time) &
                    (desligamentos['Data/Hora Evento'] < next_ign_time)
                ]

                if not igfs_possiveis.empty:
                    igf = igfs_possiveis.iloc[0]
                    igf_time = igf['Data/Hora Evento']
                    igf_odometro = pd.to_numeric(igf.get('Hodômetro Total', 0), errors='coerce')

                    # Verificar se ambos os valores são válidos (não NaN)
                    ign_valid = bool(pd.notna(ign_odometro)) and ign_odometro is not None
                    igf_valid = bool(pd.notna(igf_odometro)) and igf_odometro is not None
                    
                    if ign_valid and igf_valid:
                        # Converter para float para garantir operação válida
                        try:
                            # Usar conversão direta com verificação de tipo
                            ign_odometro_float = float(ign_odometro) if isinstance(ign_odometro, (int, float)) else 0.0
                            igf_odometro_float = float(igf_odometro) if isinstance(igf_odometro, (int, float)) else 0.0
                            
                            km = igf_odometro_float - ign_odometro_float
                            viagens.append({
                                'Dia': dia_formatado,
                                'IGN': ign_time,
                                'IGF': igf_time,
                                'Distancia_km': km
                            })
                        except (ValueError, TypeError):
                            # Pular esta viagem se não conseguir converter os valores
                            continue

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
        viagens_teste['Categoria'] = viagens_teste['Distancia_km'].apply(classificar)

        dias_todos = sorted(
            viagens_teste['Dia'].unique(),
            key=lambda x: pd.to_datetime(x, dayfirst=True)
        )

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
        resultado_df['Dia'] = pd.to_datetime(resultado_df['Dia'], format='%d/%m/%Y')
        resultado_df = resultado_df.sort_values(by='Dia')
        resultado_df['Dia'] = resultado_df['Dia'].dt.strftime('%d/%m/%Y')

        # Salvando em CSV
        resultado_df.to_csv(caminho_saida, index=False, encoding='utf-8-sig')
        print(f"✅ Planilha salva em: {caminho_saida}")

        return resultado_df

    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")

if __name__ == "__main__":
    viagens('logs/analise_par09.csv')
