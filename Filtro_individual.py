import pandas as pd
import os

from pathlib import Path
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

def executar_analise_completa(input1):
    """
    Função orquestradora: recebe o caminho do CSV de entrada,
    executa todas as análises e gera os blocos HTML e dashboard final.
    """
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

    # print("🔄 Iniciando análises...")
    df_eventos = eventos(df)
    # print("✅ Eventos concluído")
    df_pinning = analise_pinning(df)
    # print("✅ Pinning concluído")
    # print("🔄 Iniciando verificar_sequencia...")
    df_sequencia = verificar_sequencia(df)
    # print("✅ Sequência concluído")
    df_viagens = viagens(df)
    df_reg = regressao(df)
    # print("✅ Viagens concluído")
    df_logs, df_estatisticas_logs = logs(df)
    # print("✅ Logs concluído")
    df_reboot = reboot(df)
    # print("✅ Reboot concluído")
    # Satélites: obter todos, válidos e resumo
    df_satelites_result = analise_medias(df)
    # print("✅ Satélites concluído")
    if df_satelites_result is not None:
        df_satelites_todos, df_satelites_validos, df_satelites_resumo = df_satelites_result
        gerar_bloco_satelites(df_satelites_todos, df_satelites_validos, df_satelites_resumo)
    df_velocidade = velocidade(df)
    # print("✅ Velocidade concluído")
    # temporizadas_entre_si_com_ign aceita DataFrame
    df_temporizadas = temporizadas_entre_si_com_ign(df)
    # print("✅ Temporizadas concluído")
    # gerar_bloco_satelites aceita DataFrame como primeiro argumento
    # gerar_bloco_temporizadas aceita DataFrame
    # gerar_bloco_timefix aceita DataFrame
    df_ignicao = time_ign_por_viagem(df)
    # print("✅ Ignição concluído")
    df_timefix = calcular_time_fix(df)
    # print("✅ Timefix concluído")

    # print("🔄 Iniciando geração de blocos HTML...")
    if df_eventos is not None:
        if isinstance(df_eventos, tuple):
            # Se eventos retornou uma tupla (contagem, tabela_pivo)
            df_eventos_contagem, df_eventos_diario = df_eventos
            gerar_bloco_eventos(df_eventos_contagem, df_eventos_diario)
        else:
            # Se eventos retornou apenas contagem
            gerar_bloco_eventos(df_eventos)
    if df_pinning is not None:
        gerar_bloco_pinning(df_pinning)
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
    if df_viagens is not None:
        gerar_bloco_hodometro_from_csv(df_viagens, df_reg)
    if df_logs is not None and df_estatisticas_logs is not None:
        gerar_bloco_log(df_logs, df_estatisticas_logs)
    if df_reboot is not None:
        gerar_bloco_reboot(df_reboot, mostrar_todos=True)
    if df_velocidade is not None:
        gerar_bloco_velocidade(df_velocidade)
    if df_temporizadas is not None:
        gerar_bloco_temporizadas(df_temporizadas)
    if df_ignicao is not None:
        gerar_bloco_ignicao(df_ignicao)
    if df_timefix is not None and isinstance(df_timefix, pd.DataFrame):
        gerar_bloco_timefix(df_timefix)
    print("✅ Blocos HTML gerados com sucesso!")
    unir_blocos(df)

if __name__ == "__main__":  
    executar_analise_completa(
        input1='logs/867488061438379_decoded.csv',
    )
