import pandas as pd
import os

# Função principal para análise de eventos
def eventos(df: pd.DataFrame) -> pd.DataFrame:
    try:
        df = df.copy()

        if 'Tipo Mensagem' not in df.columns:
            print("❌ A coluna 'Tipo Mensagem' não foi encontrada no arquivo.")
            return None

        # Função para classificar o evento
        def get_evento(row):
            tipo = str(row.get('Tipo Mensagem', '')).strip().upper()
            codigo = str(row.get('Event Code', '')).strip()

            if tipo:
                if 'MODO ECONÔMICO' in tipo:
                    return 'MODOECO'
                return tipo
            elif codigo:
                mapa = {
                    '20': 'GTIGF',
                    '21': 'GTIGN',
                    '30': 'GTERI',
                    '27': 'GTERI'
                }
                return mapa.get(codigo, '')
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

        # Inicialização das variáveis de controle
        modo_eco_ativo = False
        periodicas = False
        ign_on = 0
        ign_off = 0
        eco = 0
        peri = 0

        for idx, row in df.iterrows():
            evento = get_evento(row)
            # Garante que motion seja string simples e nunca NDFrame
            motion = row.get('Motion Status', '')
            if isinstance(motion, (float, int)):
                if pd.notna(motion):
                    motion_str = str(int(motion))
                else:
                    motion_str = ''
            elif isinstance(motion, (str, bytes)):
                motion_str = str(motion)
            else:
                motion_str = ''
            motion_prefix = motion_str[0] if len(motion_str) > 0 else None
            codigo = str(row.get('Event Code', '')).strip()

            report_type_raw = row.get('Position Report Type', '')
            report_type = ''
            try:
                if report_type_raw is not None and str(report_type_raw).strip():
                    report_type = str(int(float(str(report_type_raw))))
            except (ValueError, TypeError):
                pass

            final = evento  # valor padrão

            # Lógica para dispositivos específicos
            if dispositivo == '802003':
                if evento == 'GTIGN':
                    ign_on += 1
                    modo_eco_ativo = False
                    periodicas = True
                elif evento == 'GTIGF':
                    ign_off += 1
                    modo_eco_ativo = True
                    periodicas = False
                elif evento == 'GTERI':
                    if motion_prefix == '1':
                        eco += 1
                        final = 'Modo Econômico'
                    elif motion_prefix == '2':
                        peri += 1
                        final = 'Posicionamento por tempo em movimento'
                    elif (motion_prefix == '2' and report_type == '10') or codigo == '30':
                        peri += 1
                    # Se quiser manter outros casos, pode adicionar aqui
                elif evento == 'MODOECO':
                    eco += 1



            df.at[idx, 'Evento Classificado'] = final

        df['Evento Classificado'] = df['Evento Classificado'].fillna(df['Tipo Mensagem'])

        contagem = df['Evento Classificado'].value_counts().reset_index()
        contagem.columns = ['Tipo mensagem', 'Quantidade']

        # --- NOVO: Contagem de eventos por dia (tabela pivô) ---
        if 'Data/Hora Evento' in df.columns:
            df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
            df = df.dropna(subset=['Data/Hora Evento'])
            df['Dia'] = df['Data/Hora Evento'].dt.strftime('%d/%m/%Y')

            tabela_pivo = df.pivot_table(
                index='Dia',
                columns='Evento Classificado',
                values='Sequência',  # Pode ser qualquer coluna, pois vamos contar
                aggfunc='count',
                fill_value=0
            ).reset_index()
            print(tabela_pivo)
            return contagem, tabela_pivo
        else:
            # print('⚠️ Coluna "Data/Hora Evento" não encontrada para análise por dia.')
            return contagem

    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return None

if __name__ == "__main__":
    # Exemplo de uso: ler um arquivo CSV e passar o DataFrame para a função
    df_exemplo = pd.read_csv('logs/867488061438379_decoded.csv', encoding='latin-1', low_memory=False)
    resultado = eventos(df_exemplo)
  