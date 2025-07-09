import pandas as pd
import os

# Função principal para análise de eventos
def eventos(caminho_arquivo, caminho_saida='Analise de eventos/quantidade_tipos_mensagem.csv'):
    try:
        df = None
        # Tenta ler o arquivo com diferentes codificações
        for enc in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
            try:
                df = pd.read_csv(caminho_arquivo, encoding=enc, low_memory=False)
                break
            except Exception:
                continue
        if df is None:
            print("❌ Não foi possível ler o arquivo.")
            return

        if 'Tipo Mensagem' not in df.columns:
            print("❌ A coluna 'Tipo Mensagem' não foi encontrada no arquivo.")
            return

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
                valor = df['Tipo Dispositivo'].iloc[0]
                if pd.notna(valor):
                    try:
                        tipo_dispositivo = str(int(float(valor)))
                    except ValueError:
                        tipo_dispositivo = str(valor).strip()
            return tipo_dispositivo

        dispositivo = tipo_dispositivo(df)
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
            if dispositivo in ['802003']:
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

        contagem.to_csv(caminho_saida, index=False, encoding='utf-8-sig')
        print(f"✅ Arquivo salvo em: {caminho_saida}")

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

            caminho_saida_dia = caminho_saida.replace('.csv', '_por_dia.csv')
            tabela_pivo.to_csv(caminho_saida_dia, index=False, encoding='utf-8-sig')
            print(f'✅ Arquivo de eventos por dia salvo em: {caminho_saida_dia}')
        else:
            print('⚠️ Coluna "Data/Hora Evento" não encontrada para análise por dia.')

    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")

if __name__ == "__main__":
    eventos('logs/analise_par09.csv')
