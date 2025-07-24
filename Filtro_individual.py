import pandas as pd
import os
from pathlib import Path
import traceback


from Analise_de_eventos.Eventos_gerais import eventos
from Analise_de_eventos.bloco_eventos import gerar_bloco_eventos
from efeito_estrela.pinning import analise_pinning
from efeito_estrela.pinning_html import gerar_bloco_pinning
from hodometro.Hodometro import viagens, regressao
from hodometro.html_hodometro import gerar_bloco_hodometro_from_csv
from Log.mensagens_log import logs
from Log.log_html import gerar_bloco_log
from Reboot.reboot import reboot
from Reboot.reboot_html import gerar_bloco_reboot
from Satelites.satelites import analise_medias
from Satelites.html_satelites import gerar_bloco_satelites
from sequence_number.sequenceNumber import verificar_sequencia
from sequence_number.sequenceNumber_html import gerar_bloco_sequenceNumber
from Tempo_de_posicoes.tempo_ERI import temporizadas_entre_si_com_ign
from Tempo_de_posicoes.temporizadas_html import gerar_bloco_temporizadas
from Tempo_ignicao.time_ignicao import time_ign_por_viagem
from Tempo_ignicao.ignicao_html import gerar_bloco_ignicao
from Time_fix.Analise_de_TTFF import calcular_time_fix
from Time_fix.fix_html import gerar_bloco_timefix
from Velocidade.velocidade import velocidade
from Velocidade.velocidade_html import gerar_bloco_velocidade
from html_final import unir_blocos
from L2.Sempre_modoeco import sempre_modoeco
from L2.html_smp_eco import gerar_bloco_smp_eco
from L2.GAP import gap
from L2.gap_html import gerar_bloco_gap

def organizar_dataframe(df: pd.DataFrame, caminho_saida_debug: str = 'csv_ordenado_debug.csv') -> pd.DataFrame:
    """
    Organiza e trata o DataFrame conforme a lógica robusta, mas SEM alterar os nomes das colunas.
    Apenas ordena as linhas e salva o resultado em um CSV para conferência.
    """
    df = df.copy()
    colunas_originais = df.columns.copy()

    # Cria coluna de referência para rastrear a linha original
    if 'Linha Original' not in df.columns:
        df['Linha Original'] = df.index + 2

    # Conversões básicas (sem alterar nomes das colunas)
    if 'Data/Hora Evento' in df.columns:
        df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
    if 'Sequência' in df.columns:
        df['Sequência'] = pd.to_numeric(df['Sequência'], errors='coerce')
    if 'Hodômetro Total' in df.columns:
        df['Hodômetro Total'] = pd.to_numeric(df['Hodômetro Total'], errors='coerce')

    # Remove linhas sem data/hora ou sequência válidas
    subset_cols = [col for col in ['Data/Hora Evento', 'Sequência'] if col in df.columns]
    if subset_cols:
        df = df.dropna(subset=subset_cols).copy()
    else:
        return df  # Não há colunas para organizar

    # Identifica registros com datas problemáticas (2019)
    if 'Data/Hora Evento' in df.columns:
        df['data_problematica'] = df['Data/Hora Evento'].dt.year == 2019
        df_normais = df[~df['data_problematica']].copy()
        df_problematicos = df[df['data_problematica']].copy()
    else:
        df_normais = df.copy()
        df_problematicos = pd.DataFrame(columns=df.columns)

    if len(df_normais) == 0:
        return df  # Todos os registros têm datas problemáticas ou não há dados

    # Ordena os dados normais por data/hora e sequência
    sort_cols = [col for col in ['Data/Hora Evento', 'Sequência'] if col in df_normais.columns]
    df_normais = df_normais.sort_values(sort_cols).reset_index(drop=True)

    # Para cada registro problemático, encontra a melhor posição nos dados normais
    for _, row_prob in df_problematicos.iterrows():
        seq_prob = row_prob.get('Sequência', None)
        melhor_posicao = None
        menor_diff = float('inf')
        if seq_prob is None or 'Sequência' not in df_normais.columns:
            continue
        for i, row_normal in df_normais.iterrows():
            diff = abs(row_normal['Sequência'] - seq_prob)
            if diff < menor_diff:
                menor_diff = diff
                melhor_posicao = i
        if melhor_posicao is not None:
            if seq_prob > df_normais.iloc[melhor_posicao]['Sequência']:
                df_normais = pd.concat([
                    df_normais.iloc[:melhor_posicao+1],
                    pd.DataFrame([row_prob]),
                    df_normais.iloc[melhor_posicao+1:]
                ]).reset_index(drop=True)
            else:
                df_normais = pd.concat([
                    df_normais.iloc[:melhor_posicao],
                    pd.DataFrame([row_prob]),
                    df_normais.iloc[melhor_posicao:]
                ]).reset_index(drop=True)

    df_ordenado = df_normais.copy()
    if 'data_problematica' in df_ordenado.columns:
        df_ordenado = df_ordenado.drop(columns=['data_problematica'])
    # Remove coluna auxiliar se não quiser no resultado final
    # if 'Linha Original' in df_ordenado.columns:
    #     df_ordenado = df_ordenado.drop(columns=['Linha Original'])
    # Reordena as colunas para manter a ordem original
    df_ordenado = df_ordenado[[col for col in colunas_originais if col in df_ordenado.columns] + [col for col in df_ordenado.columns if col not in colunas_originais]]
    # Salva para conferência
    df_ordenado.to_csv(caminho_saida_debug, index=False, encoding='utf-8-sig')
    return df_ordenado

def executar_analise_completa(input1):
    try:
        df = None
        for enc in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
            try:
                df = pd.read_csv(input1, encoding=enc, low_memory=False)
                break
            except Exception:
                continue
        if df is None:
            print(f"❌ Não foi possível ler o arquivo {input1}.")
            return
        # print(df.columns[10])
        # Conversão robusta de datas para garantir que as colunas estejam no formato datetime
        for col in ['Data/Hora Inclusão', 'Data/Hora Evento']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        # ORGANIZAÇÃO PADRÃO DO DATAFRAME
        df = organizar_dataframe(df)
        # print(df.columns[10])
        
        df_eventos = eventos(df)
        df_pinning = analise_pinning(df)
        df_sequencia = verificar_sequencia(df)
        df_viagens = viagens(df)
        df_reg = regressao(df)
        df_logs, df_estatisticas_logs, df_temporizadas, df_periodicas, df_eco = logs(df)
        df_reboot = reboot(df)
        df_satelites_result = analise_medias(df)
        if df_satelites_result is not None:
            df_satelites_todos, df_satelites_validos, df_satelites_invalidos, df_satelites_resumo = df_satelites_result
            gerar_bloco_satelites(df_satelites_todos, df_satelites_validos, df_satelites_invalidos, df_satelites_resumo)
        df_velocidade = velocidade(df)
        df_temporizadas = temporizadas_entre_si_com_ign(df)
        df_ignicao = time_ign_por_viagem(df)
        df_timefix = calcular_time_fix(df)
        df_smp_eco = sempre_modoeco(df)
        df_gap = gap(df)

        if df_eventos is not None:
            if isinstance(df_eventos, tuple):
                # Se eventos retornou uma tupla (contagem, tabela_pivo)
                df_eventos_contagem, df_eventos_diario = df_eventos
                gerar_bloco_eventos(df_eventos_contagem, df_eventos_diario)
            else:
                # Se eventos retornou apenas contagem
                gerar_bloco_eventos(df_eventos)
        if df_pinning is not None:
            gerar_bloco_pinning(df_pinning, df_pinning)
        else:
            # Cria DataFrame vazio com as colunas esperadas
            colunas = [
                'linha', 'bloco', 'ordem_no_bloco', 'latitude', 'longitude', 'latitude_anterior', 'longitude_anterior',
                'Hodômetro Total', 'Hodômetro anterior', 'Hodômetro incremental do bloco', 'Data/Hora Evento',
                'GNSS UTC Time', 'Tipo Mensagem', 'Motion Status', 'Distância incremental (m)'
            ]
            df_vazio = pd.DataFrame(data=None, columns=colunas)
            gerar_bloco_pinning(df_vazio, df_vazio)
        if df_sequencia is not None:
            gerar_bloco_sequenceNumber(df_sequencia)
        else:
            # Cria um DataFrame vazio com as colunas esperadas
            colunas = [
                'linha', 'sequencia_anterior', 'sequencia_atual', 'data_anterior', 'data_atual',
                'tipo_mensagem_anterior', 'tipo_mensagem_atual', 'tipo_problema', 'Diferenca'
            ]
            df_vazio = pd.DataFrame(data=None, columns=colunas)
            gerar_bloco_sequenceNumber(df_vazio)

            gerar_bloco_hodometro_from_csv(df_viagens, df_reg)
        if df_logs is not None and df_estatisticas_logs is not None:
            gerar_bloco_log(df_logs, df_estatisticas_logs, df_temporizadas, df_periodicas, df_eco)

        gerar_bloco_reboot(df_reboot, mostrar_todos=True)

        gerar_bloco_velocidade(df_velocidade)

        gerar_bloco_temporizadas(df_temporizadas)
   
        gerar_bloco_ignicao(df_ignicao)

        if df_timefix is not None and isinstance(df_timefix, pd.DataFrame):
            gerar_bloco_timefix(df_timefix)
 
        gerar_bloco_smp_eco(df_smp_eco['diagnostico'], tipo_veiculo=df_smp_eco['tipo_veiculo'])
        gerar_bloco_gap(df_gap)
        print("✅ Blocos HTML gerados com sucesso!")
        unir_blocos(df)
    except Exception as e:
        print('❌ Erro inesperado (traceback completo):')
        traceback.print_exc()

if __name__ == "__main__":  
    executar_analise_completa(
        input1='logs/867488061395116_decoded.csv',
    )

