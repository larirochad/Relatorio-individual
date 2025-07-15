import pandas as pd
import os
from collections import Counter

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

        df['data/hora evento'] = pd.to_datetime(df['data/hora evento'], errors='coerce')
        df['sequência'] = pd.to_numeric(df['sequência'], errors='coerce')
        df['sequência'] = df['sequência'].astype('Int64')
        df = df.dropna(subset=['data/hora evento', 'sequência']).copy()
        # (mantém a ordenação, mas a coluna linha_arquivo já está correta)
        df = df.sort_values(by=['data/hora evento', 'sequência']).reset_index(drop=True)

        problemas = []
        for i in range(len(df) - 1):
            atual = df.iloc[i]
            proximo = df.iloc[i + 1]

            s1 = atual['sequência']
            s2 = proximo['sequência']
            t1 = atual['data/hora evento']
            t2 = proximo['data/hora evento']
            tipo1 = atual.get('tipo mensagem', 'N/D')
            tipo2 = proximo.get('tipo mensagem', 'N/D')

            diferenca = s2 - s1

            # Detecta reset de contagem
            if s2 < s1 and abs(s2 - s1) > 60000:
                tipo = 'reset_de_contagem'
            elif s2 < s1:
                tipo = 'regressao_de_contagem'
            elif s1 == s2:
                tipo = 'valor_repetido'
            elif s2 > s1 + 1:
                tipo = 'salto_na_sequencia'
            elif t2 < t1:
                tipo = 'ordem_incorreta_temporal'
            else:
                continue

            problemas.append({
                'linha': int(atual['linha_arquivo']),
                'sequencia_anterior': s1,
                'sequencia_atual': s2,
                'data_anterior': t1,
                'data_atual': t2,
                'tipo_mensagem_anterior': tipo1,
                'tipo_mensagem_atual': tipo2,
                'tipo_problema': tipo,
                'Diferenca': diferenca
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
            print("✅ Nenhum problema encontrado após ordenação por sequência.")
            return None

    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return None

if __name__ == "__main__":
    df = pd.read_csv('logs/teste.csv', encoding='utf-8')
    verificar_sequencia(df)   
