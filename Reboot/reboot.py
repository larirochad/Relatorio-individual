import pandas as pd

def reboot(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    try:
        # Adiciona coluna 'linha' como index global
        df['linha'] = df.index + 2

        if 'Data/Hora Evento' not in df.columns:
            print("❌ A coluna 'Data/Hora Evento' não foi encontrada.")
            return
        df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')

        # Filtrar eventos GTPNR
        df_reboot = pd.DataFrame(df[df['Tipo Mensagem'].astype(str).str.upper().str.strip() == 'GTPNR'].copy())
        df_reboot = df_reboot.dropna(subset=['Data/Hora Evento'])  # Remove linhas sem data válida
        df_reboot = df_reboot.sort_values(by='Data/Hora Evento').reset_index(drop=True)

        # Adicionar número sequencial do reboot
        df_reboot['Reboot Nº'] = df_reboot.index + 1

        # Garantir que a coluna 'Motivo Power On' seja inteira, valores inválidos viram -1
        df_reboot['Motivo Power On'] = pd.to_numeric(df_reboot['Motivo Power On'], errors='coerce')
        df_reboot['Motivo Power On'] = df_reboot['Motivo Power On'].fillna(-1).astype(int)
        # Mapeamento dos motivos (chaves como inteiros)
        motivo_map = {
            0: 'Normal power on: Acionamento normal do dispositivo.',
            1: 'FOTA reboot',
            2: 'RTO reboot',
            3: 'Watchdog reboot',
            5: 'System watchdog reboot',
            6: 'Configuration upgrade reboot'
        }
        # Adicionar coluna de descrição do motivo
        df_reboot['Descrição Motivo Power On'] = df_reboot['Motivo Power On'].apply(lambda x: motivo_map.get(x, 'Motivo desconhecido'))

        # Selecionar apenas as colunas relevantes, incluindo 'linha'
        resultado = df_reboot[['linha', 'Reboot Nº', 'Data/Hora Evento', 'Tipo Mensagem', 'Motivo Power On', 'Descrição Motivo Power On']]

        # Salvar CSV
        # print(f"✅ Reboots encontrados: {len(resultado)}")
        # print(f"📁 Resultado salvo em: {caminho_saida}")
        return resultado

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return None

if __name__ == "__main__":
    reboot('logs/867488061317839_decoded.csv')
