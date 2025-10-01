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
        # df = organizar_dataframe(df)
        # print(df.columns[10])
        
        df_eventos = eventos(df)
        df_blocos, df_incremento = analise_pinning(df)
        df_sequencia = verificar_sequencia(df)
        df_viagens = viagens(df)
        df_reg = regressao(df)
        df_logs, df_estatisticas_logs, df_temporizadas, df_periodicas, df_eco = logs(df)
        df_reboot = reboot(df)
        df_satelites_result = analise_medias(df)
        if df_satelites_result is not None:
            (   df_satelites_todos,
                df_satelites_validos,
                df_satelites_invalidos,
                df_satelites_resumo,
                df_satelites_invalidos_eco,
                df_satelites_invalidos_peri,
                df_satelites_resumo_eco,
                df_satelites_resumo_peri,
                df_satelites_resumo_modos
            ) = df_satelites_result
            gerar_bloco_satelites(
                df_satelites_todos,
                df_satelites_validos,
                df_satelites_invalidos,
                df_satelites_resumo,
                df_satelites_invalidos_eco,
                df_satelites_invalidos_peri,
                df_satelites_resumo_eco,
                df_satelites_resumo_peri,
                df_satelites_resumo_modos
            )
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
        if df_blocos is not None:
            gerar_bloco_pinning(df_incremento, df_blocos)
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
        input1='logs/teste_mapeado.csv',
    )
