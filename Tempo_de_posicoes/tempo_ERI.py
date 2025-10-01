import pandas as pd
from typing import Optional
from datetime import datetime

def temporizadas_entre_si_com_ign(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    try:
        # Padronizações
        df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
        # Usa somente numéricos na coluna Tipo Mensagem
        def to_int_safe(v):
            try:
                return int(float(v)) if pd.notna(v) and str(v).strip() != '' else None
            except Exception:
                return None
        df['Tipo Mensagem'] = df['Tipo Mensagem'].apply(to_int_safe)

        df = df.dropna(subset=['Data/Hora Evento']).copy()
        df.sort_values(by='Data/Hora Evento', inplace=True)

        # Variáveis de controle
        last_ign = None
        last_igf = None
        last_gteri_ign = None
        last_gteri_igf = None

        resultado = []

        for idx, row in df.iterrows():
            # Garante que idx_int seja sempre inteiro
            try:
                if isinstance(idx, (int, float)):
                    idx_int = int(idx)
                elif isinstance(idx, str) and idx.isdigit():
                    idx_int = int(idx)
                else:
                    idx_int = 0
            except Exception:
                idx_int = 0
            tipo = row['Tipo Mensagem']
            data = row['Data/Hora Evento']

            diffON = None
            diffOFF = None

            if tipo == 667:
                last_ign = data
                last_gteri_ign = None
                resultado.append({
                    'linha': idx_int + 2,
                    'Data/Hora Evento': data,
                    'Tipo Mensagem': tipo,
                    'Diferença entre GTERI (IGN)': '',
                    'Diferença entre GTERI (IGF)': ''
                })

            elif tipo == 668:
                last_igf = data
                last_gteri_igf = None
                resultado.append({
                    'linha': idx_int + 2,
                    'Data/Hora Evento': data,
                    'Tipo Mensagem': tipo,
                    'Diferença entre GTERI (IGN)': '',
                    'Diferença entre GTERI (IGF)': ''
                })

            elif tipo in [760, 761]:
                if tipo == 761:  # Periódico (movimento)
                    if last_gteri_ign is not None:
                        diffON = (data - last_gteri_ign).total_seconds()
                    elif last_ign is not None:
                        diffON = (data - last_ign).total_seconds()
                    last_gteri_ign = data

                elif tipo == 760:  # Econômico (ignição desligada)
                    if last_gteri_igf is not None:
                        diffOFF = (data - last_gteri_igf).total_seconds()
                    elif last_igf is not None:
                        diffOFF = (data - last_igf).total_seconds()
                    last_gteri_igf = data

                resultado.append({
                    'linha': idx_int + 2,
                    'Data/Hora Evento': data,
                    'Tipo Mensagem': tipo,
                    'Diferença entre GTERI (IGN)': diffON if diffON is not None else '',
                    'Diferença entre GTERI (IGF)': diffOFF if diffOFF is not None else ''
                })

        # Exportar resultado
        df_result = pd.DataFrame(resultado)
        return df_result

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return None

if __name__ == "__main__":
    # This part of the code will now require a DataFrame object, not a file path.
    # For demonstration, you would typically load a DataFrame here.
    # Example: df = pd.read_csv('logs/867488061317839_decoded.csv')
    # Then call the function: temporizadas_entre_si_com_ign(df)
    print("Este script agora espera um DataFrame como entrada.")
    print("Por favor, forneça um DataFrame válido.")
