from tkinter import EventType
import pandas as pd
import os
from datetime import datetime


def sempre_modoeco(df: pd.DataFrame) -> dict:
    try:
        df = df.copy()
        # print(df.columns)
        if 'Tipo Mensagem' not in df.columns:
            print("❌ A coluna 'Tipo Mensagem' não foi encontrada no arquivo.")
            return None

        # Função para classificar o evento
        def get_evento(row):
            tipo = str(row.get('Tipo Mensagem', '')).strip().upper()
            return tipo

        def tipo_dispositivo(df):
            tipo_dispositivo = ''
            if 'Tipo Dispositivo' in df.columns and not df['Tipo Dispositivo'].empty:
                # Busca o primeiro valor não nulo e não vazio
                valor = df['Tipo Dispositivo'].dropna().astype(str).str.strip()
                valor = valor[valor != '']  # Remove strings vazias
                if not valor.empty:
                    try:
                        tipo_dispositivo = str(int(float(valor.iloc[0])))
                    except ValueError:
                        tipo_dispositivo = valor.iloc[0]
            return tipo_dispositivo

        dispositivo = tipo_dispositivo(df)
        # print(f"Dispositivo identificado: {dispositivo}")

        tensao_col = df['Alimentação Externa']
        # Filtra apenas valores numéricos válidos (diferentes de zero e não vazios)
        tensao_validos = pd.to_numeric(tensao_col, errors='coerce')
        tensao_validos = tensao_validos[(tensao_validos != 0) & (~tensao_validos.isna())]
        tensao_media = tensao_validos.mean() if not tensao_validos.empty else None
        tipo_veiculo = None
        if tensao_media is not None:
            tipo_veiculo = 'pesado' if tensao_media >= 22000 else 'leve'
        else:
            tipo_veiculo = 'desconhecido'
        # print(tipo_veiculo)

        # Contadores
        ign_on = 0
        ign_off = 0
        eco = 0
        peri = 0
        desconexao = 0
        
        # Lista para armazenar os índices dos eventos ECO
        indices_eco = []

        # Loop de contagem
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

            if dispositivo == '802003':
                if evento == 'GTIGN':
                    ign_on += 1                           
                elif evento == 'GTIGF':
                    ign_off += 1                   
                elif evento == 'GTERI':
                    if motion_prefix == '1':
                        eco += 1
                        indices_eco.append(idx)  # Armazena o índice do evento ECO
                    elif (motion_prefix == '2' and report_type == '10') or codigo == '30':
                        peri += 1
                elif evento == 'GTMPF':
                    desconexao += 1 

        # Análise de velocidade para eventos ECO (fora do loop)
        velocidades_eco = []
        if indices_eco and 'Velocidade' in df.columns:
            # print(f"\n📊 Analisando velocidades para {len(indices_eco)} eventos ECO...")
            
            for idx in indices_eco:
                velocidade = df.loc[idx, 'Velocidade']
                
                # Tenta converter velocidade para float
                try:
                    if pd.notna(velocidade):
                        velocidade_num = float(velocidade)
                    else:
                        velocidade_num = 0.0
                except (ValueError, TypeError):
                    velocidade_num = 0.0
                
                velocidades_eco.append({
                    'Indice': idx,
                    'Velocidade': velocidade_num,
                    'Data_Hora': df.loc[idx].get('Data/Hora', ''),
                    'Tipo_Mensagem': df.loc[idx].get('Tipo Mensagem', ''),
                    'Motion_Status': df.loc[idx].get('Motion Status', ''),
                    'Event_Code': df.loc[idx].get('Event Code', '')
                })


        velocidades_valores = [v['Velocidade'] for v in velocidades_eco]


        # Resumo dos resultados
        resultados = {
            'dispositivo': dispositivo,
            'contagens': {
                'ign_on': ign_on,
                'ign_off': ign_off,
                'eco': eco,
                'peri': peri,
                'desconexao': desconexao,
                'tensao': tensao_col
            },
            'velocidades_eco': velocidades_eco,
            'tipo_veiculo': tipo_veiculo,
            'tensao_media': tensao_media,
            # 'estatisticas_velocidade': estatisticas_velocidade
        }

        # Chama o diagnóstico e adiciona ao resultado
        resultados['diagnostico'] = diagnosticar_irregularidades(resultados)

        return resultados
    except Exception as e:
        print(f"❌ Erro inesperado sempre_modoeco: {str(e)}")
        return None


# def salvar_resultados_csv(resultados: dict, nome_arquivo: str = None):
#     """
#     Salva os resultados da análise em arquivos CSV.
#     """
#     if not resultados:
#         print("❌ Nenhum resultado para salvar.")
#         return
    
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
#     if not nome_arquivo:
#         nome_arquivo = f"analise_modo_eco_{timestamp}"
    
#     # 1. Salvar resumo geral
#     resumo_df = pd.DataFrame([{
#         'Dispositivo': resultados['dispositivo'],
#         'IGN_ON': resultados['contagens']['ign_on'],
#         'IGN_OFF': resultados['contagens']['ign_off'],
#         'MODO_ECONOMICO': resultados['contagens']['eco'],
#         'PERIODICO': resultados['contagens']['peri'],
#         'DESCONEXAO': resultados['contagens']['desconexao'],
#         'Data_Analise': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     }])
    

#     arquivo_resumo = "resumo_contagem.csv"
#     resumo_df.to_csv(arquivo_resumo, index=False, encoding='utf-8-sig')
#     print(f"✅ Resumo salvo em: {arquivo_resumo}")
    
#     # 2. Salvar detalhes dos eventos ECO com velocidades
#     if resultados['velocidades_eco']:
#         eco_df = pd.DataFrame(resultados['velocidades_eco'])
#         arquivo_eco = "detalhes_eco.csv"
#         eco_df.to_csv(arquivo_eco, index=False, encoding='utf-8-sig')
#         print(f"✅ Detalhes dos eventos ECO salvos em: {arquivo_eco}")
    
#     return arquivo_resumo, arquivo_eco if resultados['velocidades_eco'] else None


def diagnosticar_irregularidades(resultados):
    """
    Analisa os resultados e aponta possíveis irregularidades operacionais.
    Retorna uma lista de códigos numéricos para cada irregularidade detectada.
    """
    irregularidades = []

    cont = resultados['contagens']
    eco = cont['eco']
    ign_on = cont['ign_on']
    ign_off = cont['ign_off']
    peri = cont['peri']
    desconexao = cont['desconexao']
    velocidades_eco = resultados['velocidades_eco']
    tensao_media = resultados.get('tensao_media', 0)

    # Regra 1: Sempre em modo econômico (sem desconexão)
    if eco > 0 and peri == 0 and (ign_on + ign_off) <= 2 and desconexao == 0 and any(v['Velocidade'] > 0 for v in velocidades_eco):
        irregularidades.append(1)  # Código 1

    # Regra 2: Sempre em modo econômico (com desconexão)
    if eco > 0 and peri == 0 and (ign_on + ign_off) == 0 and desconexao > 0 and any(v['Velocidade'] > 0 for v in velocidades_eco):
        irregularidades.append(2)  # Código 2

    # Regra 3: Ligado invertido
    if eco == 0 and peri > 0 and (ign_on + ign_off) <= 1 and desconexao > 0:
        irregularidades.append(3)  # Código 3

    # Regra 4: Desconexões de bateria superiores a 4
    if desconexao >= 4:
        irregularidades.append(4)  # Código 4: Desconexões superior a 4

    # Regras 5 e 6: Velocidade em modo eco com diferentes condições de tensão
    if any(v['Velocidade'] > 0 for v in velocidades_eco):
        if tensao_media < 13000:
            irregularidades.append(5)  # Código 5: Possível TOW
        else:
            irregularidades.append(6)  # Código 6: Conexão errada em T15

    if not irregularidades:
        irregularidades.append(0)  # 0 = Nenhuma irregularidade operacional detectada

    return irregularidades



if __name__ == "__main__":
    df_exemplo = pd.read_csv('logs/teste.csv', encoding='utf-8', low_memory=False)

    # print("📊 Iniciando análise...")
    resultado = sempre_modoeco(df_exemplo)

    # print(resultado)

    # if resultado:
    #     print("\n💾 Salvando resultados...")
    #     arquivos = salvar_resultados_csv(resultado)
    #     print(f"\n✅ Análise concluída! Arquivos gerados:")
    #     for arquivo in arquivos:
    #         if arquivo:
    #             print(f"   📄 {arquivo}")
    # else:
    #     print("❌ Falha na análise.")
        
 