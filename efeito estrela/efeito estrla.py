import pandas as pd
import folium
from datetime import datetime
import webbrowser
import os
import sys
from typing import List, Tuple, Optional
from haversine import haversine
import math


caminho_csv = "logs/867488065171646_novo.csv"  # ALTERE AQUI para o caminho do seu arquivo


def ler_csv_com_encoding(caminho_csv: str) -> Optional[pd.DataFrame]:
    if not os.path.exists(caminho_csv):
        print(f"❌ Arquivo não encontrado: {caminho_csv}")
        return None
    
    codificacoes = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    
    for encoding in codificacoes:
        try:
            print(f"🔄 Tentando ler com encoding: {encoding}")
            df = pd.read_csv(caminho_csv, encoding=encoding, low_memory=False)
            print(f"✅ Arquivo lido com sucesso usando encoding: {encoding}")
            return df
        except Exception as e:
            print(f"❌ Falha com {encoding}: {str(e)}")
            continue
    
    print("❌ Não foi possível ler o arquivo com nenhuma codificação testada")
    return None


def validar_colunas(df: pd.DataFrame) -> bool:
    colunas_necessarias = ['Data/Hora Evento', 'Latitude', 'Longitude', 'Motion Status']
    
    for coluna in colunas_necessarias:
        if coluna not in df.columns:
            print(f"❌ Coluna '{coluna}' não encontrada no CSV")
            print(f"Colunas disponíveis: {list(df.columns)}")
            return False
    
    print("✅ Todas as colunas necessárias foram encontradas")
    return True


def processar_dados(df: pd.DataFrame) -> pd.DataFrame:
    print("🔄 Processando dados...")
    
    # Converter Data/Hora Evento para datetime
    df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
    
    # Converter coordenadas para numérico
    df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
    df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
    
    # Remover linhas com dados inválidos
    df_limpo = df.dropna(subset=['Data/Hora Evento', 'Latitude', 'Longitude', 'Motion Status'])
    
    # Remover coordenadas inválidas (0,0 ou muito distantes)
    df_limpo = df_limpo[
        (df_limpo['Latitude'] != 0) & 
        (df_limpo['Longitude'] != 0) &
        (df_limpo['Latitude'].abs() <= 90) &
        (df_limpo['Longitude'].abs() <= 180)
    ]
    
    # Ordenar por data/hora
    df_limpo = df_limpo.sort_values('Data/Hora Evento').reset_index(drop=True)
    
    print(f"📊 Dados processados: {len(df_limpo)} registros válidos de {len(df)} originais")
    return df_limpo


def identificar_blocos_ignicao(df: pd.DataFrame) -> List[pd.DataFrame]:
    print("🔄 Identificando blocos de ignição...")
    
    blocos = []
    bloco_atual = []
    ignicao_ligada = False
    
    for idx, row in df.iterrows():
        motion_status = str(row['Motion Status'])
        # print('motion_status', motion_status)
        motion_prefix = motion_status[0] if len(motion_status) > 0 else None
        # print('motion_prefix', motion_prefix)
        # Início de bloco: motion_prefix == '2'
        if motion_prefix == '2':
            if not ignicao_ligada:
                ignicao_ligada = True
                bloco_atual = [row]
            else:
                bloco_atual.append(row)
        # Fim de bloco: motion_prefix == '1'
        elif motion_prefix == '1':
            if ignicao_ligada:
                ignicao_ligada = False
                if bloco_atual:
                    blocos.append(pd.DataFrame(bloco_atual))
                    bloco_atual = []
    # Adicionar último bloco se ainda estiver ativo
    if bloco_atual:
        blocos.append(pd.DataFrame(bloco_atual))
    print(f"✅ Identificados {len(blocos)} blocos de ignição")
    return blocos


def gerar_cores_blocos(num_blocos: int) -> List[str]:
    """Gera cores bem distintas para cada bloco"""
    cores_base = [
        '#FF0000',  # Vermelho
        '#0066FF',  # Azul
        '#FF6600',  # Laranja
        '#9900FF',  # Roxo
        '#00CC00',  # Verde
        '#FF0099',  # Rosa
        '#00CCCC',  # Ciano
        '#FFCC00',  # Amarelo
        '#CC0066',  # Magenta escuro
        '#6600CC',  # Violeta
        '#FF3333',  # Vermelho claro
        '#3366FF',  # Azul royal
        '#FF9900',  # Laranja dourado
        '#CC00CC',  # Magenta
        '#00FF66',  # Verde limão
    ]
    
    cores = []
    for i in range(num_blocos):
        cores.append(cores_base[i % len(cores_base)])
    
    return cores


def gerar_degrade_temporal_otimizado(cor_base: str, num_pontos: int) -> List[str]:
    """
    Gera degradê MUITO mais contrastante: do quase preto ao muito claro
    """
    if num_pontos <= 1:
        return [cor_base]
    
    # Converter cor base para RGB
    cor_base = cor_base.lstrip('#')
    r = int(cor_base[0:2], 16)
    g = int(cor_base[2:4], 16)
    b = int(cor_base[4:6], 16)
    
    cores = []
    for i in range(num_pontos):
        # Progressão MUITO mais dramática: de 10% a 100% com curva exponencial
        progress = i / (num_pontos - 1)
        
        # Usar curva exponencial para criar contraste mais dramático
        fator = 0.1 + (0.9 * (progress ** 0.5))  # Curva suave do escuro para claro
        
        # Para os primeiros pontos, usar cores muito escuras
        if i < num_pontos * 0.3:  # Primeiros 30% bem escuros
            fator = 0.1 + (0.4 * progress * 3.33)  # 10% a 50%
        elif i < num_pontos * 0.7:  # Meio termo
            fator = 0.5 + (0.3 * (progress - 0.3) * 2.5)  # 50% a 80%
        else:  # Últimos 30% bem claros
            fator = 0.8 + (0.2 * (progress - 0.7) * 3.33)  # 80% a 100%
        
        # Calcular nova cor
        r_new = min(255, int(r * fator))
        g_new = min(255, int(g * fator))
        b_new = min(255, int(b * fator))
        
        cor_hex = f"#{r_new:02x}{g_new:02x}{b_new:02x}"
        cores.append(cor_hex)
    
    return cores


def gerar_degrade_azul_roxo_vermelho(num_pontos: int) -> list:
    """Gera um degradê de azul fluorescente para roxo e depois vermelho."""
    if num_pontos <= 1:
        return ['#00f6ff']
    result = []
    for i in range(num_pontos):
        t = i / (num_pontos - 1)
        if t < 0.5:
            # Azul (#00f6ff) -> Roxo (#8000ff)
            ratio = t / 0.5
            r = int(0x00 + (0x80 - 0x00) * ratio)
            g = int(0xf6 + (0x00 - 0xf6) * ratio)
            b = int(0xff + (0xff - 0xff) * ratio)
        else:
            # Roxo (#8000ff) -> Vermelho (#ff0000)
            ratio = (t - 0.5) / 0.5
            r = int(0x80 + (0xff - 0x80) * ratio)
            g = int(0x00 + (0x00 - 0x00) * ratio)
            b = int(0xff + (0x00 - 0xff) * ratio)
        result.append(f'#{r:02x}{g:02x}{b:02x}')
    return result


def filtrar_pontos_distintos(bloco: pd.DataFrame) -> pd.DataFrame:
    """Retorna apenas os pontos onde a posição mudou em relação ao anterior."""
    if bloco.empty:
        return bloco
    indices = [0]
    for i in range(1, len(bloco)):
        lat1, lon1 = bloco.iloc[i-1]['Latitude'], bloco.iloc[i-1]['Longitude']
        lat2, lon2 = bloco.iloc[i]['Latitude'], bloco.iloc[i]['Longitude']
        if lat1 != lat2 or lon1 != lon2:
            indices.append(i)
    return bloco.iloc[indices].reset_index(drop=True)


def criar_mapa_interativo_otimizado(blocos: List[pd.DataFrame]) -> folium.Map:
    print("🗺️  Criando mapa interativo otimizado...")

    # Lista para salvar os pontos plotados
    pontos_plotados = []

    # Calcular centro do mapa
    todas_lats = []
    todas_lons = []
    for bloco in blocos:
        todas_lats.extend(bloco['Latitude'].tolist())
        todas_lons.extend(bloco['Longitude'].tolist())

    centro_lat = sum(todas_lats) / len(todas_lats)
    centro_lon = sum(todas_lons) / len(todas_lons)

    # Criar mapa com melhor visualização
    mapa = folium.Map(
        location=[centro_lat, centro_lon], 
        zoom_start=16,  # Zoom maior para melhor visualização
        tiles='OpenStreetMap'
    )
    
    cores_blocos = gerar_cores_blocos(len(blocos))

    for i, bloco in enumerate(blocos):
        # Filtra apenas os pontos com Motion Status == 21
        bloco_21 = bloco[bloco['Motion Status'].astype(float).astype(int) == 21]
        # print('bloco_21', bloco_21)
        if bloco_21.empty:
            continue  # Pula blocos sem pontos 21
        # Use bloco_21 para plotar e analisar
        cores_degrade = gerar_degrade_azul_roxo_vermelho(len(bloco_21))
        coordenadas = []
        dist_total = 0.0

        print(f"📍 Processando bloco {i+1} com {len(bloco_21)} pontos distintos...")

        hodometro_anterior = None
        for j, (_, ponto) in enumerate(bloco_21.iterrows()):
            latlon = (float(ponto['Latitude']), float(ponto['Longitude']))
            coordenadas.append(latlon)

            # Calcular distância incremental e acumulada
            if j > 0:
                anterior = (float(bloco_21.iloc[j - 1]['Latitude']), float(bloco_21.iloc[j - 1]['Longitude']))
                dist_incr = haversine(anterior, latlon) * 1000  # metros
                dist_total += dist_incr
            else:
                dist_incr = 0.0

            # Cor e destaque especial para o primeiro ponto
            if j == 0:
                cor_ponto = '#00f6ff'  # Azul fluorescente
                borda = 'black'
                peso = 4
                raio = 10
                opacidade = 1.0
            else:
                cor_ponto = cores_degrade[j]
                borda = 'black'
                peso = 2
                raio = 6
                opacidade = 0.85

            # Verificar marco de hodômetro
            hodometro_atual = ponto.get('Hodômetro Total', None)
            if j == 0 or hodometro_atual != hodometro_anterior:
                marco_hodometro = True
            else:
                marco_hodometro = False
            hodometro_anterior = hodometro_atual

            # Salvar ponto plotado
            pontos_plotados.append({
                'bloco': i+1,
                'ordem_no_bloco': j+1,
                'latitude': latlon[0],
                'longitude': latlon[1],
                'data_hora': ponto['Data/Hora Evento'],
                'hodometro_atual': hodometro_atual,
                'motion_status': ponto['Motion Status']
            })

            if len(bloco_21) > 1:
                progresso = (j / (len(bloco_21) - 1)) * 100
            else:
                progresso = 100.0  # Ou 0.0, dependendo do que faz mais sentido para você

            popup_text = f"""
            <div style="font-family: Arial, sans-serif; min-width: 200px;">
                <h4 style="color: {cor_ponto}; margin: 0;">🚗 Bloco {i+1} - Ponto {j+1}/{len(bloco_21)}</h4>
                <hr style="margin: 5px 0;">
                <b>📅 Data/Hora:</b> {ponto['Data/Hora Evento'].strftime('%d/%m/%Y %H:%M:%S')}<br>
                <b>🌍 Coordenadas:</b> {ponto['Latitude']:.6f}, {ponto['Longitude']:.6f}<br>
                <b>🔧 Motion Status:</b> {ponto['Motion Status']}<br>
                <b>📏 Distância incremental:</b> {dist_incr:.1f} m<br>
                <b>📏 Distância acumulada:</b> {dist_total:.1f} m<br>
                <b>⏱️ Progresso temporal:</b> {progresso:.1f}%<br>
                <b>🛣️ Hodômetro Atual:</b> {hodometro_atual}
            </div>
            """

            if j == 0:
                # Primeiro ponto do bloco: estrela vermelha
                folium.Marker(
                    location=latlon,
                    icon=folium.Icon(icon='star', color='red'),
                    popup=folium.Popup(popup_text, max_width=300)
                ).add_to(mapa)
            elif marco_hodometro:
                # Outros marcos de hodômetro: pino verde
                folium.Marker(
                    location=latlon,
                    icon=folium.Icon(icon='flag', color='green'),
                    popup=folium.Popup(popup_text, max_width=300)
                ).add_to(mapa)
            else:
                folium.CircleMarker(
                    location=latlon,
                    radius=raio,
                    popup=folium.Popup(popup_text, max_width=300),
                    color=borda,
                    weight=peso,
                    fill=True,
                    fillColor=cor_ponto,
                    fillOpacity=opacidade
                ).add_to(mapa)

        # Desenhar linhas com degradê: cada segmento recebe a cor do ponto de origem
        for j in range(1, len(coordenadas)):
            cor_linha = cores_degrade[j-1]
            peso_linha = 6 if j == 1 else 4
            opacidade_linha = 0.95 if j == 1 else 0.8
            folium.PolyLine(
                locations=[coordenadas[j-1], coordenadas[j]],
                color=cor_linha,
                weight=peso_linha,
                opacity=opacidade_linha
            ).add_to(mapa)

    # Salvar pontos plotados em CSV
    import csv
    with open('pontos_plotados.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['bloco', 'ordem_no_bloco', 'latitude', 'longitude', 'data_hora', 'hodometro_atual', 'motion_status'])
        writer.writeheader()
        for row in pontos_plotados:
            writer.writerow(row)

    # Legenda melhorada
    legenda_html = f"""
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 320px; height: auto; 
                background-color: white; border: 3px solid #333; z-index: 9999; 
                font-size: 12px; padding: 15px; border-radius: 10px; 
                box-shadow: 0 4px 8px rgba(0,0,0,0.3); max-height: 80vh; overflow-y: auto;">
    <h3 style="margin: 0 0 10px 0; color: #333;">🚗 Análise de Ignição</h3>
    <p style="margin: 5px 0;"><b>Total de blocos:</b> {len(blocos)}</p>
    <hr style="margin: 10px 0;">
    <p style="margin: 5px 0; font-size: 11px;"><b>Blocos de Ignição:</b></p>
    """
    
    for i, bloco in enumerate(blocos):
        inicio = bloco.iloc[0]['Data/Hora Evento']
        fim = bloco.iloc[-1]['Data/Hora Evento']
        duracao = fim - inicio
        
        # Calcular distância total do bloco
        dist_total = 0.0
        for j in range(1, len(bloco)):
            p1 = (bloco.iloc[j-1]['Latitude'], bloco.iloc[j-1]['Longitude'])
            p2 = (bloco.iloc[j]['Latitude'], bloco.iloc[j]['Longitude'])
            dist_total += haversine(p1, p2) * 1000
        
        legenda_html += f'''
        <div style="margin: 5px 0; padding: 5px; border-left: 4px solid {cores_blocos[i]};">
            <b>Bloco {i+1}:</b> {len(bloco)} pontos<br>
            <small>Duração: {duracao} | Dist: {dist_total:.1f}m</small>
        </div>
        '''
    
    legenda_html += """
    <hr style="margin: 10px 0;">
    <div style="font-size: 10px; color: #666;">
        <b>Degradê Temporal:</b><br>
        🌑 Pontos escuros = Início<br>
        🌕 Pontos claros = Fim<br>
        📏 Tamanho cresce com tempo
    </div>
    </div>
    """
    
    mapa.get_root().html.add_child(folium.Element(legenda_html))

    return mapa


def salvar_e_abrir_mapa(mapa: folium.Map, nome_arquivo: str = "lat_lon.html"):
    print(f"💾 Salvando mapa como '{nome_arquivo}'...")
    
    # Salvar mapa
    mapa.save(nome_arquivo)
    
    # Abrir no navegador
    caminho_completo = os.path.abspath(nome_arquivo)
    print(f"🌐 Abrindo mapa no navegador: {caminho_completo}")
    webbrowser.open(f"file://{caminho_completo}")
    
    print("✅ Processo concluído com sucesso!")


def main():
    print("🚗 Analisador de Dados de Ignição OTIMIZADO")
    print("=" * 50)
    
    # Ler arquivo CSV
    df = ler_csv_com_encoding(caminho_csv)
    if df is None:
        print("\n❌ Erro: Não foi possível ler o arquivo CSV")
        return
    
    # Validar colunas
    if not validar_colunas(df):
        print("\n❌ Erro: Colunas necessárias não encontradas")
        return
    
    # Processar dados
    df_processado = processar_dados(df)
    if len(df_processado) == 0:
        print("\n❌ Erro: Nenhum dado válido encontrado")
        return
    
    # Identificar blocos de ignição
    blocos_ignicao = identificar_blocos_ignicao(df_processado)
    if len(blocos_ignicao) == 0:
        print("\n⚠️  Nenhum bloco de ignição encontrado")
        return
    
    # Criar mapa interativo otimizado
    mapa = criar_mapa_interativo_otimizado(blocos_ignicao)
    
    # Salvar e abrir mapa
    salvar_e_abrir_mapa(mapa)
    
    # Resumo final
    print("\n📈 RESUMO DA ANÁLISE:")
    print("=" * 30)
    print(f"📄 Arquivo: {caminho_csv}")
    print(f"📊 Registros válidos: {len(df_processado)}")
    print(f"🔥 Blocos de ignição: {len(blocos_ignicao)}")
    
    for i, bloco in enumerate(blocos_ignicao):
        inicio = bloco.iloc[0]['Data/Hora Evento']
        fim = bloco.iloc[-1]['Data/Hora Evento']
        duracao = fim - inicio
        print(f"   • Bloco {i+1}: {len(bloco)} pontos | {duracao}")


if __name__ == "__main__":
    main()