import pandas as pd
import math


def gap(df: pd.DataFrame) -> pd.DataFrame:
    try:

        df = df.copy()
 
        # Coluna de referência para rastrear origem
        if 'linha_arquivo_original' not in df.columns:
            df['linha_arquivo_original'] = df.index + 2

        # Conversões básicas
        df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
        df['Sequência'] = pd.to_numeric(df['Sequência'], errors='coerce')
        df['Hodômetro Total'] = pd.to_numeric(df['Hodômetro Total'], errors='coerce')

        # Remove linhas sem data/hora ou sequência válidas
        df = df.dropna(subset=['Data/Hora Evento', 'Sequência']).copy()

        # Identifica registros com datas problemáticas (2019)
        df['data_problematica'] = df['Data/Hora Evento'].dt.year == 2019
        
        # Separa os dados normais e problemáticos
        df_normais = df[~df['data_problematica']].copy()
        df_problematicos = df[df['data_problematica']].copy()
        
        if len(df_normais) == 0:
            print("⚠️  Todos os registros têm datas problemáticas!")
            return pd.DataFrame()
        
        # Ordena os dados normais por data/hora e sequência
        df_normais = df_normais.sort_values(['Data/Hora Evento', 'Sequência']).reset_index(drop=True)
        
        # Para cada registro problemático, encontra a melhor posição nos dados normais
        for _, row_prob in df_problematicos.iterrows():
            seq_prob = row_prob['Sequência']
            melhor_posicao = None
            menor_diff = float('inf')
            
            # Encontra o registro normal com sequência mais próxima
            for i, row_normal in df_normais.iterrows():
                diff = abs(row_normal['Sequência'] - seq_prob)
                if diff < menor_diff:
                    menor_diff = diff
                    melhor_posicao = i
            
            # Insere o registro problemático após a melhor posição encontrada
            if melhor_posicao is not None:
                if seq_prob > df_normais.iloc[melhor_posicao]['Sequência']:
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

        # --- NOVA LÓGICA DE ANÁLISE DE GAPS ---
        gaps_excedidos = []
        last_peri_time = None
        last_eco_time = None
        last_peri_idx = None
        last_eco_idx = None
        last_peri_row = None
        last_eco_row = None

        for idx, row in df_ordenado.iterrows():
            # Usa apenas os códigos numéricos em 'Tipo Mensagem'
            valor = row.get('Tipo Mensagem', '')
            try:
                evento = int(float(valor)) if not pd.isna(valor) and str(valor).strip() != '' else None
            except Exception:
                evento = None
            data = row['Data/Hora Evento']

            # Reinicia a contagem ao encontrar evento de ignição
            if evento in [667, 668]:
                last_peri_time = None
                last_eco_time = None
                last_peri_idx = None
                last_eco_idx = None
                last_peri_row = None
                last_eco_row = None
                continue

            # Periódico
            if evento == 761:
                if last_peri_time is not None:
                    gap = (data - last_peri_time).total_seconds()
                    if gap > 240: # 240s = 4 minutos
                        linha_anterior = last_peri_row['linha_arquivo_original'] if last_peri_row is not None and 'linha_arquivo_original' in last_peri_row else None
                        linha_atual = row['linha_arquivo_original'] if 'linha_arquivo_original' in row else None
                        gaps_excedidos.append({
                            'tipo': 'PERI',
                            'idx_anterior': last_peri_idx,
                            'idx_atual': idx,
                            'linha_anterior': linha_anterior,
                            'linha_atual': linha_atual,
                            'data_anterior': last_peri_time,
                            'data_atual': data,
                            'gap_s': gap
                        })
                last_peri_time = data
                last_peri_idx = idx
                last_peri_row = row
            # Econômico
            elif evento == 760:
                if last_eco_time is not None:
                    gap = (data - last_eco_time).total_seconds()
                    if gap > 7200: # 7200s = 2 horas
                        linha_anterior = last_eco_row['linha_arquivo_original'] if last_eco_row is not None and 'linha_arquivo_original' in last_eco_row else None
                        linha_atual = row['linha_arquivo_original'] if 'linha_arquivo_original' in row else None
                        gaps_excedidos.append({
                            'tipo': 'ECO',
                            'idx_anterior': last_eco_idx,
                            'idx_atual': idx,
                            'linha_anterior': linha_anterior,
                            'linha_atual': linha_atual,
                            'data_anterior': last_eco_time,
                            'data_atual': data,
                            'gap_s': gap
                        })
                last_eco_time = data
                last_eco_idx = idx
                last_eco_row = row
        # --- FIM DA NOVA LÓGICA ---

        # Se quiser retornar só os gaps excedidos:
        if len(gaps_excedidos) > 0:
            return pd.DataFrame(gaps_excedidos)
        else:
            # print('Nenhum gap excedido encontrado.')
            return pd.DataFrame()

  
    except Exception as e:
        print(f"❌ Erro inesperado gap: {str(e)}")
        return None


if __name__ == "__main__":
    df_exemplo = pd.read_csv('logs/teste.csv', encoding='utf-8', low_memory=False)
    resultado = gap(df_exemplo)
    print(resultado)
