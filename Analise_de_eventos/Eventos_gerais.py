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
        def classificar_evento(row):
            tipo = str(row.get('Tipo Mensagem', '')).strip().upper()
            motion = str(row.get('Motion Status', '')).strip()
            motion_prefix = motion[0] if motion else ''
            report_type_raw = row.get('Position Report Type', '')
            try:
                report_type = str(int(float(str(report_type_raw)))) if report_type_raw not in [None, ''] else ''
            except (ValueError, TypeError):
                report_type = ''

            # Lógica para GTERI
            if tipo == 'GTERI':
                if motion_prefix == '1':
                    return 'Modo Econômico'
                elif motion_prefix == '2' and report_type == '10':
                    return 'Posicionamento por tempo em movimento'
                elif report_type == '11':
                    return 'Cornering'
                else:
                    return None  # Não conta outros GTERI
            # Demais eventos contam normalmente
            return tipo

        # Aplica a classificação
        df['Evento Classificado'] = df.apply(classificar_evento, axis=1)

        # Remove linhas que não devem ser contadas (Evento Classificado == None)
        df = df[df['Evento Classificado'].notnull()]

        # Contagem total
        contagem = df['Evento Classificado'].value_counts().reset_index()
        contagem.columns = ['Tipo mensagem', 'Quantidade']

        # Tabela por dia, se houver coluna de data
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
            return contagem, tabela_pivo
        else:
            return contagem

    except Exception as e:
        print(f"❌ Erro inesperado no eventos: {str(e)}")
        return None

if __name__ == "__main__":
    df_exemplo = pd.read_csv('logs/867488061438379_decoded.csv', encoding='latin-1', low_memory=False)
    resultado = eventos(df_exemplo)
    print(resultado)