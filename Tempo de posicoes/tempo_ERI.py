import pandas as pd
from typing import Optional
from datetime import datetime

def temporizadas_entre_si_com_ign(df_path: str, caminho_saida: str = 'Tempo de posicoes/temporizadas_final.csv') -> None:
    try:
        for enc in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
            try:
                df = pd.read_csv(df_path, encoding=enc, low_memory=False)
                break
            except Exception:
                continue
        else:
            print("❌ Erro: Não foi possível abrir o arquivo.")
            return

        # Padronizações
        df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
        df['Tipo Mensagem'] = df['Tipo Mensagem'].astype(str).str.strip().str.upper()

        df['Position Report Type'] = df['Position Report Type'].apply(
            lambda x: str(int(float(x))) if pd.notna(x) and str(x).strip() != '' else ''
        )
        df['Motion Status'] = df['Motion Status'].astype(str).str.strip()

        df = df.dropna(subset=['Data/Hora Evento']).copy()
        df.sort_values(by='Data/Hora Evento', inplace=True)

        # Variáveis de controle
        last_ign = None
        last_igf = None
        last_gteri_ign = None
        last_gteri_igf = None

        resultado = []

        for _, row in df.iterrows():
            tipo = row['Tipo Mensagem']
            report_type = row['Position Report Type']
            motion_status = row['Motion Status']
            data = row['Data/Hora Evento']

            diffON = None
            diffOFF = None

            motion_prefix = motion_status[0] if len(motion_status) > 0 else None

            if tipo == 'GTIGN':
                last_ign = data
                last_gteri_ign = None
                resultado.append({
                    'Data/Hora Evento': data,
                    'Tipo Mensagem': tipo,
                    # 'Position Report Type': '',
                    'Motion Status': '',
                    'Diferença entre GTERI (IGN)': '',
                    'Diferença entre GTERI (IGF)': ''
                })

            elif tipo == 'GTIGF':
                last_igf = data
                last_gteri_igf = None
                resultado.append({
                    'Data/Hora Evento': data,
                    'Tipo Mensagem': tipo,
                    # 'Position Report Type': '',
                    'Motion Status': '',
                    'Diferença entre GTERI (IGN)': '',
                    'Diferença entre GTERI (IGF)': ''
                })

            elif tipo == 'GTERI' and report_type == '10':
                if motion_prefix == '2':  # IGN ligado
                    if last_gteri_ign is not None:
                        diffON = (data - last_gteri_ign).total_seconds()
                    elif last_ign is not None:
                        diffON = (data - last_ign).total_seconds()
                    last_gteri_ign = data

                elif motion_prefix == '1':  # IGF desligado
                    if last_gteri_igf is not None:
                        diffOFF = (data - last_gteri_igf).total_seconds()
                    elif last_igf is not None:
                        diffOFF = (data - last_igf).total_seconds()
                    last_gteri_igf = data

                resultado.append({
                    'Data/Hora Evento': data,
                    'Tipo Mensagem': tipo,
                    # 'Position Report Type': report_type,
                    'Motion Status': motion_status,
                    'Diferença entre GTERI (IGN)': diffON if diffON is not None else '',
                    'Diferença entre GTERI (IGF)': diffOFF if diffOFF is not None else ''
                })

        # Exportar resultado
        df_result = pd.DataFrame(resultado)
        df_result.to_csv(caminho_saida, index=False, encoding='utf-8-sig')
        print(f"✅ Resultado salvo em: {caminho_saida}")

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    temporizadas_entre_si_com_ign('logs/analise_par09.csv')
