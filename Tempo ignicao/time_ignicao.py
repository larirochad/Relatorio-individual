import pandas as pd

def time_ign_por_viagem(caminho_csv, caminho_saida='Tempo ignicao/tempo_ignicao_viagens.csv'):
    try:
        # Leitura do CSV com fallback de codificações
        codificacoes = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        for enc in codificacoes:
            try:
                df = pd.read_csv(caminho_csv, encoding=enc, low_memory=False)
                break
            except:
                continue
        else:
            print("❌ Erro: Não foi possível ler o arquivo.")
            return

        # Tratamento de datas
        df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
        df = df.dropna(subset=['Data/Hora Evento'])
        df = df.sort_values('Data/Hora Evento')

        # Mapeamento de evento baseado no Motion Status
        def get_evento(row):
            motion_status = str(row.get('Motion Status', '')).strip()
            if motion_status.startswith('1'):
                return 'IGF'  # Ignição desligada
            elif motion_status.startswith('2'):
                return 'IGN'  # Ignição ligada
            else:
                # Fallback para o método anterior se Motion Status não estiver disponível
                tipo = str(row.get('Tipo Mensagem', '')).strip().upper()
                codigo = str(row.get('Event Code', '')).strip()
                if tipo:
                    return tipo
                elif codigo:
                    return {'20': 'GTIGF', '21': 'GTIGN'}.get(codigo, '')
            return ''

        df['Evento'] = df.apply(get_evento, axis=1)

        # Separar IGN/IGF mantendo o índice original
        igns = df[df['Evento'].isin(['GTIGN', 'IGN'])]
        igfs = df[df['Evento'].isin(['GTIGF', 'IGF'])]

        # Montar ciclos completos: IGN -> IGF -> próximo IGN
        ciclos = []
        ign_idx = 0
        igf_idx = 0
        while ign_idx < len(igns) and igf_idx < len(igfs):
            ign_row = igns.iloc[ign_idx]
            ign_time = ign_row['Data/Hora Evento']
            ign_index = igns.index[ign_idx]
            # Procurar o IGF após esse IGN
            igf_possivel = igfs[igfs['Data/Hora Evento'] > ign_time]
            if len(igf_possivel) == 0:
                break
            igf_row = igf_possivel.iloc[0]
            igf_time = igf_row['Data/Hora Evento']
            igf_index = igf_possivel.index[0]
            tempo_on = (igf_time - ign_time).total_seconds()
            # Procurar o próximo IGN após esse IGF
            next_ign_possivel = igns[igns['Data/Hora Evento'] > igf_time]
            if len(next_ign_possivel) == 0:
                tempo_off = None
                next_ign_index = None
                next_ign_time = None
            else:
                next_ign_row = next_ign_possivel.iloc[0]
                next_ign_time = next_ign_row['Data/Hora Evento']
                next_ign_index = next_ign_possivel.index[0]
                tempo_off = (next_ign_time - igf_time).total_seconds()
            ciclos.append({
                'Linha_IGN': int(ign_index) + 2,
                'Dia_IGN': ign_time.strftime('%d/%m/%Y'),
                'ign on (s)': tempo_on,
                'Linha_IGF': int(igf_index) + 2,
                'Dia_IGF': igf_time.strftime('%d/%m/%Y'),
                'ign off (s)': tempo_off if tempo_off is not None else ''
            })
            # Avançar para o próximo ciclo
            # O próximo ciclo começa no próximo IGN após esse IGF
            ign_idx = igns.index.get_loc(next_ign_index) if next_ign_index is not None else len(igns)
            igf_idx = igfs.index.get_loc(igf_index) + 1

        df_final = pd.DataFrame(ciclos)
        df_final.to_csv(caminho_saida, index=False, encoding='utf-8-sig')
        print(f"✅ Arquivo salvo em: {caminho_saida}")
        return df_final

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    time_ign_por_viagem('logs/867488061317839_decoded.csv')
