import pandas as pd
import os
from collections import Counter

def ordenar_robusto_sequence_number(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ordena o DataFrame considerando datas problemáticas (2019) e insere esses registros na posição correta baseada na sequência.
    """
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()

    # Coluna de referência para rastrear origem
    if 'linha_arquivo' not in df.columns:
        df['linha_arquivo'] = df.index + 2

    # Conversões básicas
    df['data/hora evento'] = pd.to_datetime(df['data/hora evento'], errors='coerce')
    df['sequência'] = pd.to_numeric(df['sequência'], errors='coerce')

    # Remove linhas sem data/hora ou sequência válidas
    df = df.dropna(subset=['data/hora evento', 'sequência']).copy()

    # Identifica registros com datas problemáticas (2019)
    df['data_problematica'] = df['data/hora evento'].dt.year == 2019
    
    # Separa os dados normais e problemáticos
    df_normais = df[~df['data_problematica']].copy()
    df_problematicos = df[df['data_problematica']].copy()
    
    if len(df_normais) == 0:
        print("⚠️  Todos os registros têm datas problemáticas!")
        return df.drop(columns=['data_problematica'])
    
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
    
    # Remove coluna auxiliar
    df_ordenado = df_ordenado.drop(columns=['data_problematica'])
    return df_ordenado


def verificar_sequencia(df: pd.DataFrame, caminho_saida = 'sequence_number/problemas_ordenando_sequencia.csv') -> pd.DataFrame:
    try:
        df = df.copy()

        # Adiciona coluna com o número da linha original do arquivo (começando em 2, pois 1 é o cabeçalho)
        if 'linha_arquivo' not in df.columns:
            df['linha_arquivo'] = df.index + 2  # Salva a linha original ANTES de ordenar

        df.columns = df.columns.str.strip().str.lower()

        if 'data/hora evento' not in df.columns or 'sequência' not in df.columns:
            print("❌ As colunas obrigatórias 'Data/Hora Evento' e 'Sequência' não foram encontradas.")
            return None

        #conversões
        df['data/hora evento'] = pd.to_datetime(df['data/hora evento'], errors='coerce')
        df['sequência'] = pd.to_numeric(df['sequência'], errors='coerce')

        df['sequência'] = df['sequência'].astype('Int64')
        df = df.dropna(subset=['data/hora evento', 'sequência']).copy()
        # ORDENAR DE FORMA ROBUSTA
        df = ordenar_robusto_sequence_number(df)
        # (mantém a ordenação, mas a coluna linha_arquivo já está correta)
        df = df.reset_index(drop=True)

        problemas = []
        for i in range(len(df) - 1):
            atual = df.iloc[i]
            s1 = atual['sequência']
            t1 = atual['data/hora evento']
            tipo1 = atual.get('tipo mensagem', 'N/D')
            linha_atual = int(atual['linha_arquivo'])

            # Detecta problemas de sequência padrão (apenas próxima linha)
            proximo = df.iloc[i + 1]
            s2 = proximo['sequência']
            t2 = proximo['data/hora evento']
            tipo2 = proximo.get('tipo mensagem', 'N/D')
            diferenca = s2 - s1

            if s2 < s1 and abs(s2 - s1) > 60000:
                tipo = 'reset_de_contagem'
                problemas.append({
                    'linha': linha_atual,
                    'sequencia_anterior': s1,
                    'sequencia_atual': s2,
                    'data_anterior': t1,
                    'data_atual': t2,
                    'tipo_mensagem_anterior': tipo1,
                    'tipo_mensagem_atual': tipo2,
                    'tipo_problema': tipo,
                    'Diferenca': diferenca
                })
            elif s2 < s1:
                tipo = 'regressao_de_contagem'
                problemas.append({
                    'linha': linha_atual,
                    'sequencia_anterior': s1,
                    'sequencia_atual': s2,
                    'data_anterior': t1,
                    'data_atual': t2,
                    'tipo_mensagem_anterior': tipo1,
                    'tipo_mensagem_atual': tipo2,
                    'tipo_problema': tipo,
                    'Diferenca': diferenca
                })
            elif s2 > s1 + 1:
                tipo = 'salto_na_sequencia'
                problemas.append({
                    'linha': linha_atual,
                    'sequencia_anterior': s1,
                    'sequencia_atual': s2,
                    'data_anterior': t1,
                    'data_atual': t2,
                    'tipo_mensagem_anterior': tipo1,
                    'tipo_mensagem_atual': tipo2,
                    'tipo_problema': tipo,
                    'Diferenca': diferenca
                })

            # Nova lógica: verifica repetição nas próximas 3 linhas
            for j in range(1, 15):
                if i + j >= len(df):
                    break
                prox = df.iloc[i + j]
                s_rep = prox['sequência']
                tipo_rep = prox.get('tipo mensagem', 'N/D')
                t_rep = prox['data/hora evento']
                linha_rep = int(prox['linha_arquivo'])
                if s1 == s_rep:
                    if tipo1 == tipo_rep:
                        tipo_repeticao = 'valor_repetido_igual'
                    else:
                        tipo_repeticao = 'valor_repetido_diferente'
                    problemas.append({
                        'linha': linha_atual,
                        'linha_repetida': linha_rep,
                        'valor_anterior': s1,
                        'valor_repetido': s_rep,
                        'mensagem_atual': tipo1,
                        'mensagem_repetida': tipo_rep,
                        'data_anterior': t1,
                        'data_repetida': t_rep,
                        'tipo_problema': tipo_repeticao,
                        'Diferenca': 0
                    })

        if problemas:
            dfp = pd.DataFrame(problemas)
            if caminho_saida:
                dfp.to_csv(caminho_saida, index=False, encoding='utf-8-sig')
            # print(f"⚠️ Problemas detectados e salvos em: {out}")

            # Contagem por tipo
            tipos = [p['tipo_problema'] for p in problemas]
            contagem = Counter(tipos)
            # print("\n📊 Resumo dos problemas encontrados:")
            for tipo, qtd in contagem.items():
                #print(f"  - {tipo}: {qtd}")
                return dfp  # Retorna o DataFrame com os problemas
        else:
            # print("✅ Nenhum problema encontrado após ordenação por sequência.")
            
            return None

    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return None

if __name__ == "__main__":
    df = pd.read_csv('logs/teste.csv', encoding='utf-8')
    verificar_sequencia(df)   
