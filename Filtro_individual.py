import pandas as pd
import os
from pathlib import Path
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
import copy


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


# Funções auxiliares para processamento paralelo
def process_eventos(df):
    return eventos(df)

def process_pinning(df):
    return analise_pinning(df)

def process_reboot(df):
    return reboot(df)

def process_velocidade(df):
    return velocidade(df)

def process_sequencia(df):
    return verificar_sequencia(df)

def process_viagens(df):
    return viagens(df)

def process_regressao(df):
    return regressao(df)

def process_logs(df):
    return logs(df)

def process_satelites(df):
    return analise_medias(df)

def process_temporizadas(df):
    return temporizadas_entre_si_com_ign(df)

def process_ignicao(df):
    return time_ign_por_viagem(df)

def process_timefix(df):
    return calcular_time_fix(df)

def process_modoeco(df):
    return sempre_modoeco(df)

def process_gap(df):
    return gap(df)

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

        # Conversão robusta de datas para garantir que as colunas estejam no formato datetime
        for col in ['Data/Hora Inclusão', 'Data/Hora Evento']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Agrupe as funções que podem rodar em paralelo
        funcoes_para_executar = {
            "eventos": process_eventos,
            "pinning": process_pinning,
            "reboot": process_reboot,
            "velocidade": process_velocidade,
            "sequencia": process_sequencia,
            "viagens": process_viagens,
            "regressao": process_regressao,
            "logs": process_logs,
            "satelites": process_satelites,
            "temporizadas": process_temporizadas,
            "ignicao": process_ignicao,
            "timefix": process_timefix,
            "modoeco": process_modoeco,
            "gap": process_gap,
        }

        resultados = {}

        with ProcessPoolExecutor() as executor:
            # Submete todas as funções para execução com o DataFrame como argumento
            futuros = {executor.submit(func, df): nome for nome, func in funcoes_para_executar.items()}
            
            # Processa os resultados conforme eles são completados
            for futuro in as_completed(futuros):
                nome = futuros[futuro]
                try:
                    resultados[nome] = futuro.result()
                    # print(f"✅ Função '{nome}' completada com sucesso")
                except Exception as exc:
                    print(f"❌ Erro na função '{nome}': {exc}")
                    traceback.print_exc()

        # Gera os blocos HTML com os resultados obtidos
        if "eventos" in resultados and resultados["eventos"] is not None:
            ev = resultados["eventos"]
            if isinstance(ev, tuple):
                df_eventos_contagem, df_eventos_diario = ev
                gerar_bloco_eventos(df_eventos_contagem, df_eventos_diario)
            else:
                gerar_bloco_eventos(ev)

        if "pinning" in resultados and resultados["pinning"] is not None:
            df_blocos, df_incremento = resultados["pinning"]
            gerar_bloco_pinning(df_incremento, df_blocos)

        if "sequencia" in resultados and resultados["sequencia"] is not None:
            gerar_bloco_sequenceNumber(resultados["sequencia"])
        else:
            colunas = [
                'linha', 'sequencia_anterior', 'sequencia_atual', 'data_anterior', 'data_atual',
                'tipo_mensagem_anterior', 'tipo_mensagem_atual', 'tipo_problema', 'Diferenca'
            ]
            df_vazio = pd.DataFrame(data=None, columns=colunas)
            gerar_bloco_sequenceNumber(df_vazio)

        if "viagens" in resultados and "regressao" in resultados:
            gerar_bloco_hodometro_from_csv(resultados["viagens"], resultados["regressao"])

        if "logs" in resultados and resultados["logs"] is not None:
            df_logs, df_estatisticas_logs, df_temporizadas, df_periodicas, df_eco = resultados["logs"]
            if df_logs is not None and df_estatisticas_logs is not None:
                gerar_bloco_log(df_logs, df_estatisticas_logs, df_temporizadas, df_periodicas, df_eco)

        if "reboot" in resultados:
            gerar_bloco_reboot(resultados["reboot"], mostrar_todos=True)

        if "velocidade" in resultados:
            gerar_bloco_velocidade(resultados["velocidade"])

        if "temporizadas" in resultados:
            gerar_bloco_temporizadas(resultados["temporizadas"])

        if "ignicao" in resultados:
            gerar_bloco_ignicao(resultados["ignicao"])

        if "timefix" in resultados and resultados["timefix"] is not None:
            df_timefix = resultados["timefix"]
            if isinstance(df_timefix, pd.DataFrame):
                gerar_bloco_timefix(df_timefix)

        if "modoeco" in resultados and resultados["modoeco"] is not None:
            eco = resultados["modoeco"]
            gerar_bloco_smp_eco(eco["diagnostico"], tipo_veiculo=eco["tipo_veiculo"])

        if "gap" in resultados:
            gerar_bloco_gap(resultados["gap"])

        if "satelites" in resultados and resultados["satelites"] is not None:
            (
                df_satelites_todos,
                df_satelites_validos,
                df_satelites_invalidos,
                df_satelites_resumo,
                df_satelites_invalidos_eco,
                df_satelites_invalidos_peri,
                df_satelites_resumo_eco,
                df_satelites_resumo_peri,
                df_satelites_resumo_modos
            ) = resultados["satelites"]
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

        print("✅ Blocos HTML gerados com sucesso!")
        unir_blocos(df)

    except Exception as e:
        print('❌ Erro inesperado (traceback completo):')
        traceback.print_exc()

if __name__ == "__main__":  
    executar_analise_completa(
        input1='logs/867488061438387_decoded.csv',
    )

