import pandas as pd
import os

# Função principal para análise de eventos
def eventos(df: pd.DataFrame) -> pd.DataFrame:
    try:
        df = df.copy()

        if 'Tipo Mensagem' not in df.columns:
            print("❌ A coluna 'Tipo Mensagem' não foi encontrada no arquivo.")
            return None

        # Função para classificar o evento com base APENAS nos códigos numéricos
        def get_evento(row):
            try:
                valor = row.get('Tipo Mensagem', '')
                if pd.isna(valor):
                    return ''
                # Normaliza para int quando possível
                if isinstance(valor, str) and valor.strip() != '':
                    try:
                        valor_int = int(float(valor))
                    except Exception:
                        return valor  # mantém como está se não for número
                elif isinstance(valor, (int, float)):
                    try:
                        valor_int = int(valor)
                    except Exception:
                        return ''
                else:
                    return ''
                # Mapas de classificação amigável
                if valor_int == 667:
                    return 667  # GTIGN
                if valor_int == 668:
                    return 668  # GTIGF
                if valor_int == 760:
                    return 760  # ECO
                if valor_int == 761:
                    return 761  # PERIÓDICO
                if valor_int == 775:
                    return 775  # GTMPN
                if valor_int == 776:
                    return 776  # GTMPF
                return valor_int
            except Exception:
                return ''

        # Função para identificar o tipo de dispositivo
        def tipo_dispositivo(df):
            tipo_dispositivo = ''
            if 'Tipo Dispositivo' in df.columns and not df['Tipo Dispositivo'].empty:
                # Busca o primeiro valor não nulo e não vazio
                valor = df['Tipo Dispositivo'].dropna().astype(str).str.strip()
                valor = valor[valor != '']  # Remove strings vazias
                if not valor.empty:
                    try:
                        tipo_dispositivo = str(int(float(valor.iloc[0])))
                    except ValueError:
                        tipo_dispositivo = valor.iloc[0]
            return tipo_dispositivo
        # print(tipo_dispositivo)
        dispositivo = tipo_dispositivo(df)
        # print(f"Tipo Dispositivo detectado: {dispositivo} ({type(dispositivo)})")
        df = df.sort_values('Sequência', ascending=True)
        df = df.drop_duplicates(subset='Sequência', keep='first')

        df['Evento Classificado'] = ''

        # Inicialização das variáveis de controle (não utilizadas fora, mas mantidas)
        ign_on = 0
        ign_off = 0
        eco = 0
        peri = 0

        for idx, row in df.iterrows():
            evento = get_evento(row)
            final = evento

            # Classificação textual simples baseada nos códigos definidos
            if evento == 760:
                final = 'Modo Econômico'
                eco += 1
            elif evento == 761:
                final = 'Posicionamento por tempo em movimento'
                peri += 1
            elif evento == 667:
                final = 667
                ign_on += 1
            elif evento == 668:
                final = 668
                ign_off += 1
            elif evento in [775, 776]:
                final = evento

            df.at[idx, 'Evento Classificado'] = final

        df['Evento Classificado'] = df['Evento Classificado'].fillna(df['Tipo Mensagem'])

        contagem = df['Evento Classificado'].value_counts().reset_index()
        contagem.columns = ['Tipo mensagem', 'Quantidade']

        if 'Data/Hora Evento' in df.columns:
            df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
            df = df.dropna(subset=['Data/Hora Evento'])
            df['Dia'] = df['Data/Hora Evento'].dt.strftime('%d/%m/%Y')

            tabela_pivo = df.pivot_table(
                index='Dia',
                columns='Evento Classificado',
                values='Sequência',  
                aggfunc='count',
                fill_value=0
            ).reset_index()
            # print(tabela_pivo)
            return contagem, tabela_pivo
        else:
            # print('⚠️ Coluna "Data/Hora Evento" não encontrada para análise por dia.')
            return contagem

    except Exception as e:
        print(f"❌ Erro inesperado no eventos: {str(e)}")
        return None

if __name__ == "__main__":
    df_exemplo = pd.read_csv('logs/867488061438379_decoded.csv', encoding='latin-1', low_memory=False)
    resultado = eventos(df_exemplo)
    print(resultado)