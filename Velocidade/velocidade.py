import pandas as pd
from haversine import haversine, Unit

def velocidade(df_path, caminho_saida='Velocidade/velocidade_analisada.csv'):
    try:
        # Tenta múltiplas codificações para abrir o CSV
        for enc in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
            try:
                df = pd.read_csv(df_path, encoding=enc, low_memory=False)
                break
            except Exception:
                continue
        else:
            print("❌ Erro: Não foi possível abrir o arquivo.")
            return

        # Converte a coluna de velocidade para numérico
        df['Velocidade'] = pd.to_numeric(df['Velocidade'], errors='coerce')

        # Verifica velocidades extremas
        df['Alerta_Velocidade'] = df['Velocidade'].apply(lambda x: 'Acima de 150 km/h' if x is not None and x > 150 else '')

        # Identifica linhas com ignição desligada e ligada baseado no Motion Status
        # Motion Status prefix "1" = ignição desligada (IGF)
        # Motion Status prefix "2" = ignição ligada (IGN)
        df['Motion_Status_Str'] = df['Motion Status'].astype(str).str.strip()
        df['IGF'] = df['Motion_Status_Str'].str.startswith('1')
        df['IGN'] = df['Motion_Status_Str'].str.startswith('2')

        # Inicializa listas para os dois tipos de alerta
        alerta_velocidade_absurda = []
        alerta_ignicao_off = []
        linhas_originais = []
        analise_ignicao_off = False  # Estado: só analisa entre IGF e IGN

        for i, row in df.iterrows():
            try:
                vel_float = float(row['Velocidade'])
            except Exception:
                vel_float = float('nan')
            # Alerta de velocidade absurda: valor da velocidade
            if pd.notna(vel_float) and vel_float > 150:
                alerta_velocidade_absurda.append(vel_float)
            else:
                alerta_velocidade_absurda.append('')
            # Controle de análise de ignição OFF
            if bool(row['IGF']):
                analise_ignicao_off = True  # Ativa análise
            if bool(row['IGN']):
                analise_ignicao_off = False  # Desativa análise
            # Só processa alerta de ignição OFF se dentro do bloco
            if analise_ignicao_off and pd.notna(vel_float) and vel_float > 0:
                alerta_ignicao_off.append(vel_float)
            else:
                alerta_ignicao_off.append('')
            # Guarda a linha original (começando em 2 por causa do cabeçalho)
            try:
                linhas_originais.append(int(str(i)) + 2)
            except Exception:
                linhas_originais.append(None)

        df['Velocidade absurda'] = alerta_velocidade_absurda
        df['Velocidade com ignição OFF'] = alerta_ignicao_off
        df['Linha Original'] = linhas_originais
    
        # Filtra apenas as linhas com algum alerta
        df_alerta = df[(df['Velocidade absurda'] != '') | (df['Velocidade com ignição OFF'] != '')]

        # Seleciona apenas as colunas desejadas para o output, se existirem
        colunas_desejadas = ['Linha Original', 'Data/Hora Evento', 'Tipo Mensagem', 'Velocidade absurda','Velocidade com ignição OFF']
        colunas_existentes = [col for col in colunas_desejadas if col in df_alerta.columns]
        if colunas_existentes:
            df_alerta = df_alerta[colunas_existentes]
        else:
            df_alerta = pd.DataFrame({col: [] for col in colunas_desejadas})

        # Garante que df_alerta é um DataFrame antes de salvar
        if not isinstance(df_alerta, pd.DataFrame):
            df_alerta = pd.DataFrame(df_alerta)

        # Salva os alertas em CSV
        df_alerta.to_csv(caminho_saida, index=False, encoding='utf-8-sig')

        # Conta e imprime a quantidade de ocorrências de cada problema
        qtd_absurda = df['Velocidade absurda'].astype(str).replace('', pd.NA).dropna().shape[0]
        qtd_ignicao_off = df['Velocidade com ignição OFF'].astype(str).replace('', pd.NA).dropna().shape[0]
        print(f' Quantidade de velocidades absurdas (>150 km/h): {qtd_absurda}')
        print(f' Quantidade de velocidades com ignição OFF: {qtd_ignicao_off}')
        print(f"✅ Análise concluída. Resultados salvos em: {caminho_saida}")

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    velocidade('Velocidade/logs/analise_par09.csv')

