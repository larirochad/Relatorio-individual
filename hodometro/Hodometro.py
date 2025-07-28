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
        start_dia = None  # Inicializa para evitar UnboundLocalError
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
            elif in_viagem and start_dia is not None and (motion.startswith('1') or dia != start_dia):
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
                start_dia = None  # Limpa ao finalizar a viagem
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
    # print(resultado_df)
    return resultado_df


def regressao(df: pd.DataFrame) -> pd.DataFrame:
    """
    Função corrigida para análise de regressão do hodômetro.
    Ordena primeiro os registros normais, depois posiciona os de 2019 baseado na sequência.
    """
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()

    # Coluna de referência para rastrear origem
    if 'linha_arquivo_original' not in df.columns:
        df['linha_arquivo_original'] = df.index + 2

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
    
    # Ordena os dados normais por data/hora e sequência
    df_normais = df_normais.sort_values(['data/hora evento', 'sequência']).reset_index(drop=True)
    
    # Para cada registro problemático, encontra a melhor posição nos dados normais
    for _, row_prob in df_problematicos.iterrows():
        seq_prob = row_prob['sequência']
        melhor_posicao = None
        menor_diff = float('inf')
        
        # Encontra o registro normal com sequência mais próxima
        for i, row_normal in df_normais.iterrows():
            diff = abs(row_normal['sequência'] - seq_prob)
            if diff < menor_diff:
                menor_diff = diff
                melhor_posicao = i
        
        # Insere o registro problemático após a melhor posição encontrada
        if melhor_posicao is not None:
            if seq_prob > df_normais.iloc[melhor_posicao]['sequência']:
                # Insere após a melhor posição
                df_normais = pd.concat([
                    df_normais.iloc[:melhor_posicao+1],
                    pd.DataFrame([row_prob]),
                    df_normais.iloc[melhor_posicao+1:]
                ]).reset_index(drop=True)
            else:
                # Insere antes da melhor posição
                df_normais = pd.concat([
                    df_normais.iloc[:melhor_posicao],
                    pd.DataFrame([row_prob]),
                    df_normais.iloc[melhor_posicao:]
                ]).reset_index(drop=True)
    
    # Agora df_normais contém todos os registros, ordenados corretamente
    df_ordenado = df_normais.copy()
    
    # Remove colunas auxiliares
    df_ordenado = df_ordenado.drop(columns=['data_problematica'])
    
    # Salva debug
    df_ordenado.to_csv('hodometro_ordenado_debug_corrigido.csv', index=False, encoding='utf-8-sig')
    # print(f"✅ Dados ordenados salvos em 'hodometro_ordenado_debug_corrigido.csv' ({len(df_ordenado)} registros)")
    
    # Análise de regressão apenas com registros que têm hodômetro
    df_hod = df_ordenado[df_ordenado['hodômetro total'].notna()].copy()
    
    if len(df_hod) < 2:
        print("⚠️  Dados insuficientes para análise de hodômetro!")
        return pd.DataFrame()
    
    # print(f"📊 Analisando {len(df_hod)} registros com hodômetro válido...")
    
    registros_analise = []
    regressoes = 0
    
    for i in range(1, len(df_hod)):
        anterior = df_hod.iloc[i - 1]
        atual = df_hod.iloc[i]
        
        hod_anterior = anterior['hodômetro total']
        hod_atual = atual['hodômetro total']
        diferenca = hod_atual - hod_anterior
        
        if hod_atual >= hod_anterior:
            status = 'ok'
        else:
            status = 'regressão'
            regressoes += 1
        
        registros_analise.append({
            'linha': atual.get('linha_arquivo_original', atual.name + 2),
            'Hodômetro_anterior': hod_anterior,
            'Hodômetro_atual': hod_atual,
            'data_anterior': anterior['data/hora evento'],
            'data_atual': atual['data/hora evento'],
            'sequencia_anterior': anterior['sequência'],
            'sequencia_atual': atual['sequência'],
            'tipo_mensagem_anterior': anterior.get('tipo mensagem', 'N/D'),
            'tipo_mensagem_atual': atual.get('tipo mensagem', 'N/D'),
            'tipo_problema': status,
            'Diferenca': round(diferenca, 1)
        })
    
    df_resultado = pd.DataFrame(registros_analise)
    
    # print(f"📈 Análise concluída:")
    # print(f"   • Total de comparações: {len(registros_analise)}")
    # print(f"   • Registros OK: {len(registros_analise) - regressoes}")
    # print(f"   • Regressões encontradas: {regressoes}")
    
    return df_resultado


# Exemplo de uso
if __name__ == "__main__":
    # Carrega dados
    df = pd.read_csv('logs/867488061438387_decoded.csv', encoding='latin-1', dtype=str, low_memory=False, on_bad_lines='skip')
    
    # Processa coluna hodômetro se existir
    if 'Hodômetro Total' in df.columns:
        df['Hodômetro Total'] = (
            df['Hodômetro Total']
            .astype(str)
            .str.replace(',', '.')
            .str.replace(r'[^\d\.]', '', regex=True)
        )
        df['Hodômetro Total'] = pd.to_numeric(df['Hodômetro Total'], errors='coerce')
    
    # Executa análise de regressão
    print("🔍 Iniciando análise de regressão do hodômetro...")
    df_reg = regressao(df)
    def_viagens = viagens(df)
    # Salva resultado
    if not df_reg.empty:
        df_reg.to_csv('hod_regressao_corrigido.csv', index=False, encoding='utf-8-sig')
        print(f"✅ Análise salva em 'hod_regressao_corrigido.csv'")
        
        # Mostra primeiras regressões encontradas
        regressoes = df_reg[df_reg['tipo_problema'] == 'regressão']
        if not regressoes.empty:
            print(f"\n⚠️  Primeiras regressões encontradas:")
            print(regressoes.head(10)[['linha', 'Hodômetro_anterior', 'Hodômetro_atual', 'Diferenca', 'sequencia_atual']])
    else:
        print("❌ Nenhum resultado gerado!")