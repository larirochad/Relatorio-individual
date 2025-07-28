import pandas as pd
import os
from collections import Counter

def ordenar_robusto_sequence_number(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ordena o DataFrame considerando datas problemáticas (2019) e insere esses registros na posição correta baseada na sequência.
    PRESERVA a coluna linha_original durante todo o processo.
    """
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()

    # IMPORTANTE: Verifica se a coluna linha_original existe
    if 'linha_original' not in df.columns:
        df['linha_original'] = df.index + 2

    # Conversões básicas
    df['data/hora evento'] = pd.to_datetime(df['data/hora evento'], errors='coerce')
    df['sequência'] = pd.to_numeric(df['sequência'], errors='coerce')

    # Remove linhas sem data/hora ou sequência válidas
    # IMPORTANTE: A coluna linha_original é preservada durante o dropna
    df = df.dropna(subset=['data/hora evento', 'sequência']).copy()

    # Identifica registros com datas problemáticas (2019)
    df['data_problematica'] = df['data/hora evento'].dt.year == 2019
    
    # Separa os dados normais e problemáticos
    df_normais = df[~df['data_problematica']].copy()
    df_problematicos = df[df['data_problematica']].copy()
    
    if len(df_normais) == 0:
        return df.drop(columns=['data_problematica'])
    
    # Ordena os dados normais por data/hora e sequência
    df_normais = df_normais.sort_values(['data/hora evento', 'sequência']).reset_index(drop=True)
    
    # Para cada registro problemático, encontra a melhor posição nos dados normais
    for _, row_prob in df_problematicos.iterrows():
        seq_prob = row_prob['sequência']
        linha_original_prob = row_prob['linha_original']
        melhor_posicao = None
        menor_diff = float('inf')
        
        # Encontra o registro normal com sequência mais próxima
        for i, row_normal in df_normais.iterrows():
            diff = abs(row_normal['sequência'] - seq_prob)
            if diff < menor_diff:
                menor_diff = diff
                melhor_posicao = i
        
        # Insere o registro problemático na posição correta
        if melhor_posicao is not None:
            # Converte a Series em DataFrame mantendo TODAS as colunas, incluindo linha_original
            row_prob_df = pd.DataFrame([row_prob])
            
            if seq_prob > df_normais.iloc[melhor_posicao]['sequência']:
                # Insere após a melhor posição
                df_normais = pd.concat([
                    df_normais.iloc[:melhor_posicao+1],
                    row_prob_df,
                    df_normais.iloc[melhor_posicao+1:]
                ], ignore_index=True)
            else:
                # Insere antes da melhor posição
                df_normais = pd.concat([
                    df_normais.iloc[:melhor_posicao],
                    row_prob_df,
                    df_normais.iloc[melhor_posicao:]
                ], ignore_index=True)
    
    # A coluna 'linha_original' foi preservada durante todo o processo
    df_ordenado = df_normais.copy()
    
    # Remove coluna auxiliar
    df_ordenado = df_ordenado.drop(columns=['data_problematica'])
    
    return df_ordenado


def verificar_sequencia(df: pd.DataFrame, caminho_saida = 'sequence_number/problemas_ordenando_sequencia.csv', caminho_saida_ordenado = 'sequence_number/ordenado_para_analise.csv') -> pd.DataFrame:
    try:
        df = df.copy()

        # 1. PRIMEIRO: Adiciona coluna com o número da linha original do arquivo ANTES de qualquer manipulação
        df['linha_original'] = df.index + 2  # Salva a linha original ANTES de qualquer manipulação

        # 2. Salva o DataFrame COMPLETAMENTE original para análise
        if caminho_saida_ordenado:
            try:
                df.to_csv('sequence_number/original_para_analise.csv', index=False, encoding='utf-8-sig')
            except Exception as e:
                pass

        # 3. Padroniza as colunas
        df.columns = df.columns.str.strip().str.lower()

        if 'data/hora evento' not in df.columns or 'sequência' not in df.columns:
            return None

        # 4. Conversões
        df['data/hora evento'] = pd.to_datetime(df['data/hora evento'], errors='coerce')
        df['sequência'] = pd.to_numeric(df['sequência'], errors='coerce')
        df['sequência'] = df['sequência'].astype('Int64')
        
        # 5. Remove registros inválidos MAS preserva a linha_original
        df_original = df.copy()  # Guarda uma cópia do DataFrame original com as linhas originais
        df = df.dropna(subset=['data/hora evento', 'sequência']).copy()
        
        # 6. ORDENAR DE FORMA ROBUSTA (preservando linha_original)
        df = ordenar_robusto_sequence_number(df)

        # 7. Verifica se a linha_original foi preservada
        if 'linha_original' not in df.columns:
            return None

        # 8. ANÁLISE DE PROBLEMAS (usando linha_original do arquivo original)
        problemas = []
        
        for i in range(len(df) - 1):
            atual = df.iloc[i]
            s1 = atual['sequência']
            t1 = atual['data/hora evento']
            tipo1 = atual.get('tipo mensagem', 'N/D')
            linha_atual = int(atual['linha_original'])  # LINHA ORIGINAL DO ARQUIVO

            # Detecta problemas de sequência padrão (apenas próxima linha)
            proximo = df.iloc[i + 1]
            s2 = proximo['sequência']
            t2 = proximo['data/hora evento']
            tipo2 = proximo.get('tipo mensagem', 'N/D')
            linha_proxima = int(proximo['linha_original'])  # LINHA ORIGINAL DO ARQUIVO
            diferenca = s2 - s1

            if s2 < s1 and abs(s2 - s1) > 60000:
                tipo = 'reset_de_contagem'
                problemas.append({
                    'linha_original': linha_atual,
                    'linha_proxima_original': linha_proxima,
                    'sequencia_anterior': s1,
                    'sequencia_atual': s2,
                    'data_anterior': t1,
                    'data_atual': t2,
                    'tipo_mensagem_anterior': tipo1,
                    'tipo_mensagem_atual': tipo2,
                    'tipo_problema': tipo,
                    'diferenca': diferenca,
                    'posicao_no_ordenado': i
                })
            elif s2 < s1:
                tipo = 'regressao_de_contagem'
                problemas.append({
                    'linha_original': linha_atual,
                    'linha_proxima_original': linha_proxima,
                    'sequencia_anterior': s1,
                    'sequencia_atual': s2,
                    'data_anterior': t1,
                    'data_atual': t2,
                    'tipo_mensagem_anterior': tipo1,
                    'tipo_mensagem_atual': tipo2,
                    'tipo_problema': tipo,
                    'diferenca': diferenca,
                    'posicao_no_ordenado': i
                })
            elif s2 > s1 + 1:
                tipo = 'salto_na_sequencia'
                problemas.append({
                    'linha_original': linha_atual,
                    'linha_proxima_original': linha_proxima,
                    'sequencia_anterior': s1,
                    'sequencia_atual': s2,
                    'data_anterior': t1,
                    'data_atual': t2,
                    'tipo_mensagem_anterior': tipo1,
                    'tipo_mensagem_atual': tipo2,
                    'tipo_problema': tipo,
                    'diferenca': diferenca,
                    'posicao_no_ordenado': i
                })

            # Nova lógica: verifica repetição nas próximas 30 linhas
            for j in range(1, 30):
                if i + j >= len(df):
                    break
                prox = df.iloc[i + j]
                s_rep = prox['sequência']
                tipo_rep = prox.get('tipo mensagem', 'N/D')
                t_rep = prox['data/hora evento']
                linha_rep = int(prox['linha_original'])  # LINHA ORIGINAL DO ARQUIVO
                
                # Para mensagens repetidas, também captura as datas de inclusão se existirem
                t1_inclusao = atual.get('data/hora inclusão', t1)  # Usa evento se inclusão não existir
                t_rep_inclusao = prox.get('data/hora inclusão', t_rep)  # Usa evento se inclusão não existir
                
                if s1 == s_rep:
                    if tipo1 == tipo_rep:
                        tipo_repeticao = 'valor_repetido_igual'
                    else:
                        tipo_repeticao = 'valor_repetido_diferente'
                    problemas.append({
                        'linha_original': linha_atual,
                        'linha_repetida_original': linha_rep,
                        'valor_anterior': s1,
                        'valor_repetido': s_rep,
                        'mensagem_atual': tipo1,
                        'mensagem_repetida': tipo_rep,
                        'data_anterior': t1,
                        'data_repetida': t_rep,
                        'data_anterior_inclusao': t1_inclusao,
                        'data_repetida_inclusao': t_rep_inclusao,
                        'tipo_problema': tipo_repeticao,
                        'diferenca': 0,
                        'posicao_no_ordenado': i,
                        'posicao_repetida_no_ordenado': i + j
                    })

        if problemas:
            dfp = pd.DataFrame(problemas)
            if caminho_saida:
                try:
                    dfp.to_csv(caminho_saida, index=False, encoding='utf-8-sig')
                except Exception as e:
                    pass
            return dfp  # Retorna o DataFrame com os problemas
        else:
            return None

    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    df = pd.read_csv('logs/867488061438387_decoded.csv', encoding='latin-1')
    resultado = verificar_sequencia(df)