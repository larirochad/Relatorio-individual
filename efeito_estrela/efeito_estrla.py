import pandas as pd
import folium
from datetime import datetime
import webbrowser
import os
from typing import List, Tuple, Optional
from haversine import haversine
import math


def analise_efeito_estrela(df_ou_caminho, nome_arquivo: str = "lat_lon.html"):
    """
    Executa toda a análise de efeito estrela a partir de um DataFrame já carregado ou caminho de arquivo.
    Salva e abre o mapa gerado em HTML se nome_arquivo for fornecido.
    Retorna o DataFrame processado e a lista de blocos.
    """
    import pandas as pd
    import os
    import webbrowser
    # Permitir tanto DataFrame quanto caminho
    if isinstance(df_ou_caminho, pd.DataFrame):
        df = df_ou_caminho.copy()
    else:
        df = pd.read_csv(df_ou_caminho)

    def validar_colunas(df: pd.DataFrame) -> bool:
        colunas_necessarias = ['Data/Hora Evento', 'Latitude', 'Longitude', 'Motion Status']
        for coluna in colunas_necessarias:
            if coluna not in df.columns:
                print(f"❌ Coluna '{coluna}' não encontrada no DataFrame")
                print(f"Colunas disponíveis: {list(df.columns)}")
                return False
        print("✅ Todas as colunas necessárias foram encontradas")
        return True

    def processar_dados(df: pd.DataFrame) -> pd.DataFrame:
        print("🔄 Processando dados...")
        df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
        df_limpo = df.dropna(subset=['Data/Hora Evento', 'Latitude', 'Longitude', 'Motion Status'])
        df_limpo = df_limpo[
            (df_limpo['Latitude'] != 0) & 
            (df_limpo['Longitude'] != 0) &
            (df_limpo['Latitude'].abs() <= 90) &
            (df_limpo['Longitude'].abs() <= 180)
        ]
        df_limpo = df_limpo.sort_values(by='Data/Hora Evento').reset_index(drop=True)
        print(f"📊 Dados processados: {len(df_limpo)} registros válidos de {len(df)} originais")
        return df_limpo

    def identificar_blocos_ignicao(df: pd.DataFrame) -> List[pd.DataFrame]:
        print("🔄 Identificando blocos de ignição...")
        blocos = []
        bloco_atual = []
        ignicao_ligada = False
        for idx, row in df.iterrows():
            motion_status = str(row['Motion Status'])
            motion_prefix = motion_status[0] if len(motion_status) > 0 else None
            if motion_prefix == '2':
                if not ignicao_ligada:
                    ignicao_ligada = True
                    bloco_atual = [row]
                else:
                    bloco_atual.append(row)
            elif motion_prefix == '1':
                if ignicao_ligada:
                    ignicao_ligada = False
                    if bloco_atual:
                        blocos.append(pd.DataFrame(bloco_atual))
                        bloco_atual = []
        if bloco_atual:
            blocos.append(pd.DataFrame(bloco_atual))
        print(f"✅ Identificados {len(blocos)} blocos de ignição")
        return blocos

    def gerar_cores_blocos(num_blocos: int) -> List[str]:
        cores_base = [
            '#FF0000', '#0066FF', '#FF6600', '#9900FF', '#00CC00', '#FF0099', '#00CCCC', '#FFCC00',
            '#CC0066', '#6600CC', '#FF3333', '#3366FF', '#FF9900', '#CC00CC', '#00FF66',
        ]
        return [cores_base[i % len(cores_base)] for i in range(num_blocos)]

    def gerar_degrade_azul_roxo_vermelho(num_pontos: int) -> list:
        if num_pontos <= 1:
            return ['#00f6ff']
        result = []
        for i in range(num_pontos):
            t = i / (num_pontos - 1)
            if t < 0.5:
                ratio = t / 0.5
                r = int(0x00 + (0x80 - 0x00) * ratio)
                g = int(0xf6 + (0x00 - 0xf6) * ratio)
                b = int(0xff + (0xff - 0xff) * ratio)
            else:
                ratio = (t - 0.5) / 0.5
                r = int(0x80 + (0xff - 0x80) * ratio)
                g = int(0x00 + (0x00 - 0x00) * ratio)
                b = int(0xff + (0x00 - 0xff) * ratio)
            result.append(f'#{r:02x}{g:02x}{b:02x}')
        return result

    def criar_mapa_interativo_otimizado(blocos: List[pd.DataFrame]) -> folium.Map:
        print("🗺️  Criando mapa interativo otimizado...")
        pontos_plotados = []
        todas_lats = []
        todas_lons = []
        for bloco in blocos:
            todas_lats.extend(bloco['Latitude'].tolist())
            todas_lons.extend(bloco['Longitude'].tolist())
        centro_lat = sum(todas_lats) / len(todas_lats)
        centro_lon = sum(todas_lons) / len(todas_lons)
        mapa = folium.Map(
            location=[centro_lat, centro_lon], 
            zoom_start=16,
            tiles='OpenStreetMap'
        )
        cores_blocos = gerar_cores_blocos(len(blocos))
        for i, bloco in enumerate(blocos):
            bloco_21 = bloco[bloco['Motion Status'].astype(float).astype(int) == 21]
            if bloco_21.empty:
                continue
            cores_degrade = gerar_degrade_azul_roxo_vermelho(len(bloco_21))
            coordenadas = []
            dist_total = 0.0
            hodometro_anterior = None
            for j, (_, ponto) in enumerate(bloco_21.iterrows()):
                latlon = (float(ponto['Latitude']), float(ponto['Longitude']))
                coordenadas.append(latlon)
                if j > 0:
                    anterior = (float(bloco_21.iloc[j - 1]['Latitude']), float(bloco_21.iloc[j - 1]['Longitude']))
                    dist_incr = haversine(anterior, latlon) * 1000
                    dist_total += dist_incr
                else:
                    dist_incr = 0.0
                if j == 0:
                    cor_ponto = '#00f6ff'
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
                hodometro_atual = ponto.get('Hodômetro Total', None)
                if j == 0 or hodometro_atual != hodometro_anterior:
                    marco_hodometro = True
                else:
                    marco_hodometro = False
                hodometro_anterior = hodometro_atual
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
                    progresso = 100.0
                data_hora_str = ponto['Data/Hora Evento']
                if hasattr(data_hora_str, 'strftime'):
                    data_hora_str = data_hora_str.strftime('%d/%m/%Y %H:%M:%S')
                popup_text = f"""
                <div style=\"font-family: Arial, sans-serif; min-width: 200px;\">
                    <h4 style=\"color: {cor_ponto}; margin: 0;\">🚗 Bloco {i+1} - Ponto {j+1}/{len(bloco_21)}</h4>
                    <hr style=\"margin: 5px 0;\">
                    <b>📅 Data/Hora:</b> {data_hora_str}<br>
                    <b>🌍 Coordenadas:</b> {ponto['Latitude']:.6f}, {ponto['Longitude']:.6f}<br>
                    <b>🔧 Motion Status:</b> {ponto['Motion Status']}<br>
                    <b>📏 Distância incremental:</b> {dist_incr:.1f} m<br>
                    <b>📏 Distância acumulada:</b> {dist_total:.1f} m<br>
                    <b>⏱️ Progresso temporal:</b> {progresso:.1f}%<br>
                    <b>🛣️ Hodômetro Atual:</b> {hodometro_atual}
                </div>
                """
                if j == 0:
                    folium.Marker(
                        location=latlon,
                        icon=folium.Icon(icon='star', color='red'),
                        popup=folium.Popup(popup_text, max_width=300)
                    ).add_to(mapa)
                elif marco_hodometro:
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
        import csv
        with open('pontos_plotados.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['bloco', 'ordem_no_bloco', 'latitude', 'longitude', 'data_hora', 'hodometro_atual', 'motion_status'])
            writer.writeheader()
            for row in pontos_plotados:
                writer.writerow(row)
        legenda_html = f"""
        <div style=\"position: fixed; 
                    top: 10px; right: 10px; width: 320px; height: auto; 
                    background-color: white; border: 3px solid #333; z-index: 9999; 
                    font-size: 12px; padding: 15px; border-radius: 10px; 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3); max-height: 80vh; overflow-y: auto;\">
        <h3 style=\"margin: 0 0 10px 0; color: #333;\">🚗 Análise de Ignição</h3>
        <p style=\"margin: 5px 0;\"><b>Total de blocos:</b> {len(blocos)}</p>
        <hr style=\"margin: 10px 0;\">
        <p style=\"margin: 5px 0; font-size: 11px;\"><b>Blocos de Ignição:</b></p>
        """
        for i, bloco in enumerate(blocos):
            inicio = bloco.iloc[0]['Data/Hora Evento']
            fim = bloco.iloc[-1]['Data/Hora Evento']
            duracao = fim - inicio
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
        <hr style=\"margin: 10px 0;\">
        <div style=\"font-size: 10px; color: #666;\">
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
        mapa.save(nome_arquivo)
        caminho_completo = os.path.abspath(nome_arquivo)
        print(f"🌐 Abrindo mapa no navegador: {caminho_completo}")
        webbrowser.open(f"file://{caminho_completo}")
        print("✅ Processo concluído com sucesso!")

    print("🚗 Analisador de Dados de Ignição OTIMIZADO (função única)")
    print("=" * 50)
    if not validar_colunas(df):
        print("\n❌ Erro: Colunas necessárias não encontradas")
        return None, None
    df_processado = processar_dados(df)
    if len(df_processado) == 0:
        print("\n❌ Erro: Nenhum dado válido encontrado")
        return None, None
    blocos_ignicao = identificar_blocos_ignicao(df_processado)
    if len(blocos_ignicao) == 0:
        print("\n⚠️  Nenhum bloco de ignição encontrado")
        return df_processado, []
    mapa = criar_mapa_interativo_otimizado(blocos_ignicao)
    if nome_arquivo:
        salvar_e_abrir_mapa(mapa, nome_arquivo)
    print("\n📈 RESUMO DA ANÁLISE:")
    print("=" * 30)
    print(f"📊 Registros válidos: {len(df_processado)}")
    print(f"🔥 Blocos de ignição: {len(blocos_ignicao)}")
    for i, bloco in enumerate(blocos_ignicao):
        inicio = bloco.iloc[0]['Data/Hora Evento']
        fim = bloco.iloc[-1]['Data/Hora Evento']
        duracao = fim - inicio
        print(f"   • Bloco {i+1}: {len(bloco)} pontos | {duracao}")
    return df_processado, blocos_ignicao

if __name__ == "__main__":
    df = pd.read_csv('logs/analise_par09.csv')
    analise_efeito_estrela(df)  