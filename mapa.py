import pandas as pd
import folium
from folium.plugins import FeatureGroupSubGroup
from pathlib import Path
import json
import os

# Paleta de cores do bloco_eventos.py
CORES_EVENTOS = [
    "#BDB76B", "#DAA520", "#708090", "#0000FF", "#836FFF",
    "#191970", "#4B0082", "#FF1493", "#7FFFD4", "#66c7ff", "#1C1C1C",  "#808000", "#A020F0",  "#87CEEB","#BC8F8F"
]

def cor_evento(tipo, tipos_unicos=None):
    if tipos_unicos is None:
        return CORES_EVENTOS[0]
    idx = tipos_unicos.index(tipo) if tipo in tipos_unicos else 0
    return CORES_EVENTOS[idx % len(CORES_EVENTOS)]

def extrair_viagens_detalhadas(df):
    """
    Retorna uma lista de viagens com 'IGN' (início) e 'IGF' (fim) usando a lógica do hodometro/Hodometro.py.
    """
    df = df.copy()
    df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
    df = df.dropna(subset=['Data/Hora Evento'])
    df = df.sort_values('Data/Hora Evento')
    def get_evento(row):
        tipo = str(row.get('Tipo Mensagem', '')).strip().upper()
        codigo = str(row.get('Event Code', '')).strip()
        if tipo:
            return tipo
        elif codigo:
            mapa = {'20': 'GTIGF', '21': 'GTIGN'}
            return mapa.get(codigo, '')
        return ''
    ignicoes = df[df.apply(lambda row: get_evento(row) == 'GTIGN', axis=1)].reset_index(drop=True)
    desligamentos = df[df.apply(lambda row: get_evento(row) == 'GTIGF', axis=1)].reset_index(drop=True)
    viagens = []
    viagens_gtign = set()
    for i, ign in ignicoes.iterrows():
        ign_time = ign['Data/Hora Evento']
        next_ign_time = ignicoes.iloc[i + 1]['Data/Hora Evento'] if i + 1 < len(ignicoes) else pd.Timestamp.max
        igfs_possiveis = desligamentos[
            (desligamentos['Data/Hora Evento'] > ign_time) &
            (desligamentos['Data/Hora Evento'] < next_ign_time)
        ]
        if not igfs_possiveis.empty:
            igf = igfs_possiveis.iloc[0]
            igf_time = igf['Data/Hora Evento']
            viagens.append({'IGN': ign_time, 'IGF': igf_time})
            viagens_gtign.add((ign_time, igf_time))
    # Motion Status fallback (caso não haja eventos GTIGN/GTIGF)
    df = df.sort_values('Data/Hora Evento')
    in_viagem = False
    start_time = None
    for idx, row in df.iterrows():
        motion = str(row.get('Motion Status', '')).strip()
        datahora = row['Data/Hora Evento']
        if motion.startswith('2') and not in_viagem:
            in_viagem = True
            start_time = datahora
        elif in_viagem and (motion.startswith('1')):
            end_time = datahora
            if start_time != end_time and (start_time, end_time) not in viagens_gtign:
                viagens.append({'IGN': start_time, 'IGF': end_time})
            in_viagem = False
            start_time = None
    return viagens

def gerar_bloco_trajetos(df, filename='bloco_trajetos.html'):
    """
    Gera um bloco HTML com um mapa interativo de eventos filtrados: GTIGN, GTIGF, e GTERI (apenas Periódica e Modo Eco).
    """
    df = df.copy()
    df['Data/Hora Evento'] = pd.to_datetime(df['Data/Hora Evento'], errors='coerce')
    df = df.dropna(subset=['Latitude', 'Longitude', 'Data/Hora Evento'])
    df = df[(df['Latitude'] != 0) & (df['Longitude'] != 0)]
    df = df.dropna(subset=['Data/Hora Evento'])
    df['Dia'] = df['Data/Hora Evento'].dt.strftime('%d/%m/%Y')
    # --- FILTRO DOS EVENTOS ---
    def tipo_evento(row):
        tipo = str(row.get('Tipo Mensagem', '')).strip().upper()
        report_type_raw = row.get('Position Report Type', '')
        try:
            report_type = '10' if float(report_type_raw) == 10.0 else ''
        except (ValueError, TypeError):
            report_type = ''
        motion = row.get('Motion Status', '')
        if isinstance(motion, (float, int)):
            if isinstance(motion, float) and pd.isna(motion):
                motion_str = ''
            else:
                motion_str = str(int(motion))
        elif isinstance(motion, (str, bytes)):
            motion_str = str(motion)
        else:
            motion_str = ''
        motion_prefix = motion_str[0] if len(motion_str) > 0 else None
        if tipo == 'GTIGN':
            return 'GTIGN'
        elif tipo == 'GTIGF':
            return 'GTIGF'
        elif tipo == 'GTERI' and report_type == '10' and motion_prefix == '2':
            return 'Periódica'
        elif tipo == 'GTERI' and motion_prefix == '1':
            return 'Modo Eco'
        else:
            return None
    df['tipo_evento_filtro'] = df.apply(tipo_evento, axis=1)
    df = df[df['tipo_evento_filtro'].notnull()].copy()
    tipos_unicos = df['tipo_evento_filtro'].dropna().unique().tolist()

    # Extrair viagens detalhadas (IGN/IGF)
    viagens_lista = extrair_viagens_detalhadas(df)

    # Atribuir viagem a cada evento
    def atribuir_viagem(row):
        for i, v in enumerate(viagens_lista):
            if v['IGN'] <= row['Data/Hora Evento'] <= v['IGF']:
                return i  # índice da viagem
        return None
    df['viagem_idx'] = df.apply(atribuir_viagem, axis=1)
    df = df.dropna(subset=['viagem_idx'])
    df['viagem_idx'] = df['viagem_idx'].astype(int)

    # Criar mapa centralizado no centro dos pontos
    lat_centro = df['Latitude'].mean()
    lon_centro = df['Longitude'].mean()
    m = folium.Map(location=[lat_centro, lon_centro], zoom_start=13, tiles='OpenStreetMap')

    # Filtro: FeatureGroup por dia
    dias_unicos = sorted(df['Dia'].unique().tolist())
    grupos_dia = {}
    polylines_refs = []
    for dia in dias_unicos:
        grupo = folium.FeatureGroup(name=f"Dia: {dia}", show=False)
        grupos_dia[dia] = grupo
        m.add_child(grupo)

    # Adicionar marcadores e linhas por viagem
    CORES_LINHAS = [
        "#FF0000", "#0066FF", "#FF6600", "#9900FF", "#00CC00", "#FF0099", "#00CCCC", "#FFCC00",
        "#CC0066", "#6600CC", "#FF3333", "#3366FF", "#FF9900", "#CC00CC", "#00FF66",
    ]
    viagem_ids = []
    viagem_info = []
    for viagem_idx in sorted(df['viagem_idx'].unique()):
        viagem_df = df[df['viagem_idx'] == viagem_idx].sort_values('Data/Hora Evento')
        if viagem_df.empty:
            continue
        dia_viagem = viagem_df.iloc[0]['Dia']
        grupo = grupos_dia[dia_viagem]
        coords = list(zip(viagem_df['Latitude'], viagem_df['Longitude']))
        cor_linha = CORES_LINHAS[viagem_idx % len(CORES_LINHAS)]
        viagem_id = f"viagem_{dia_viagem.replace('/', '')}_{viagem_idx}"
        viagem_ids.append(viagem_id)
        viagem_info.append({
            'id': str(viagem_id),
            'dia': str(dia_viagem),
            'idx': int(viagem_idx),
            'cor': str(cor_linha)
        })
        poly = folium.PolyLine(
            locations=coords,
            color=cor_linha,
            weight=5,
            opacity=0.7,
            tooltip=f'Viagem {viagem_idx+1}',
            class_name=viagem_id  # Adiciona classe CSS
        )
        poly.add_to(grupo)
        for _, row in viagem_df.iterrows():
            tipo = row['tipo_evento_filtro']
            cor = cor_evento(tipo, tipos_unicos)
            popup = f"""
            <b>Tipo:</b> {tipo}<br>
            <b>Data/Hora:</b> {row['Data/Hora Evento']}<br>
            <b>Viagem:</b> {row['viagem_idx']+1}<br>
            <b>Dia:</b> {row['Dia']}<br>
            <b>Lat/Lon:</b> {row['Latitude']:.6f}, {row['Longitude']:.6f}
            """
            marker = folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=6,
                color=cor,
                fill=True,
                fill_color=cor,
                fill_opacity=0.8,
                popup=folium.Popup(popup, max_width=300),
                class_name=viagem_id  # Adiciona classe CSS
            )
            marker.add_to(grupo)
            marker._name = viagem_id
    # LayerControl só para os dias
    folium.LayerControl(collapsed=False).add_to(m)

    # Legenda de cores
    legenda_html = '<div style="position: fixed; bottom: 30px; left: 30px; z-index:9999; background: white; border:2px solid #666; border-radius:10px; padding: 10px 18px; font-size: 13px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);">'
    legenda_html += '<b>Legenda de eventos:</b><br>'
    for i, tipo in enumerate(tipos_unicos):
        cor = cor_evento(tipo, tipos_unicos)
        legenda_html += f'<span style="display:inline-block;width:16px;height:16px;background:{cor};border-radius:4px;margin-right:6px;"></span> {tipo}<br>'
    legenda_html += '<br><input type="checkbox" id="toggleLines" checked style="vertical-align:middle;"> <label for="toggleLines" style="vertical-align:middle;">Mostrar linhas das viagens</label>'
    legenda_html += '</div>'
    m.get_root().html.add_child(folium.Element(legenda_html))

    # Adiciona JS para mostrar/ocultar linhas
    custom_js = '''
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        var toggle = document.getElementById('toggleLines');
        function setLinesVisible(visible) {
            var map = document.querySelector('.leaflet-container');
            if (!map) return;
            var svgs = map.querySelectorAll('svg polyline, svg path.leaflet-interactive');
            svgs.forEach(function(line) {
                if (visible) {
                    line.style.display = '';
                } else {
                    line.style.display = 'none';
                }
            });
        }
        if (toggle) {
            toggle.addEventListener('change', function() {
                setLinesVisible(toggle.checked);
            });
            setLinesVisible(toggle.checked);
        }
    });
    </script>
    '''
    m.get_root().html.add_child(folium.Element(custom_js))

    # Painel de filtro de viagens (checkboxes)
    viagens_by_dia = {}
    for v in viagem_info:
        viagens_by_dia.setdefault(v['dia'], []).append(v)
    filtro_viagens_html = '''<div id="filtro-viagens-panel" style="position:fixed;top:20px;left:50%;transform:translateX(-50%);z-index:99999;background:#fff;border:2px solid #764ba2;border-radius:16px;padding:16px 18px;box-shadow:0 2px 16px rgba(102,51,153,0.13);font-size:16px;display:none;max-width:90vw;width:auto;">
    <b>Filtrar viagens do dia:</b><br><div id="filtro-viagens-checkboxes" style="display:flex;flex-wrap:wrap;gap:8px;"></div></div>'''
    m.get_root().html.add_child(folium.Element(filtro_viagens_html))
    try:
        custom_js = r'''
        <script>
        console.log('viagensByDia:', window.viagensByDia);
        var viagemDestaque = null;
        function updateViagemCheckboxes() {
            var dias = [];
            document.querySelectorAll('.leaflet-control-layers-overlays input[type=checkbox]').forEach(function(cb) {
                if(cb.checked && cb.nextSibling && cb.nextSibling.textContent.includes('Dia:')) {
                    var dia = cb.nextSibling.textContent.replace('Dia:','').trim();
                    dias.push(dia);
                }
            });
            var panel = document.getElementById('filtro-viagens-panel');
            var box = document.getElementById('filtro-viagens-checkboxes');
            if(dias.length === 1) {
                panel.style.display = '';
                var dia = dias[0];
                var viagens = window.viagensByDia && window.viagensByDia[dia] ? window.viagensByDia[dia] : [];
                var html = '';
                viagens.forEach(function(v) {
                    html += `<label style='margin-right:10px;'><input type='checkbox' class='viagem-cb' data-vid='${v.id}' checked style='vertical-align:middle;'><span style='color:${v.cor};font-weight:bold;'> Viagem ${v.idx+1}</span></label>`;
                });
                box.innerHTML = html;
            } else {
                panel.style.display = 'none';
                box.innerHTML = '';
            }
            setTimeout(bindViagemCheckboxes, 100);
        }
        function bringPointsToFront() {
            var svg = document.querySelector('.leaflet-overlay-pane svg');
            if (svg) {
                var circles = svg.querySelectorAll('circle');
                circles.forEach(function(circ) {
                    svg.appendChild(circ);
                });
            }
        }
        function bindViagemCheckboxes() {
            document.querySelectorAll('.viagem-cb').forEach(function(cb) {
                cb.onchange = function() {
                    var vid = cb.getAttribute('data-vid');
                    var visible = cb.checked;
                    document.querySelectorAll('svg polyline.'+vid+', svg path.leaflet-interactive.'+vid).forEach(function(line) {
                        if (!viagemDestaque || viagemDestaque === vid) {
                            line.style.display = visible ? '' : 'none';
                        }
                    });
                    bringPointsToFront();
                };
            });
            // Adiciona evento de clique nas linhas (apenas polylines)
            document.querySelectorAll('svg polyline, svg path.leaflet-interactive').forEach(function(line) {
                line.onclick = function(e) {
                    var classes = line.getAttribute('class') || '';
                    var match = classes.match(/viagem_\d+_\d+/);
                    if (!match) return;
                    var vid = match[0];
                    if (viagemDestaque === vid) {
                        viagemDestaque = null;
                        document.querySelectorAll('svg polyline, svg path.leaflet-interactive').forEach(function(l) {
                            l.style.display = '';
                            l.style.strokeWidth = '';
                            l.style.filter = '';
                        });
                        // Aplica filtro dos checkboxes
                        document.querySelectorAll('.viagem-cb').forEach(function(cb) {
                            var v = cb.getAttribute('data-vid');
                            var visible = cb.checked;
                            document.querySelectorAll('svg polyline.'+v+', svg path.leaflet-interactive.'+v).forEach(function(l) {
                                l.style.display = visible ? '' : 'none';
                            });
                        });
                        bringPointsToFront();
                    } else {
                        viagemDestaque = vid;
                        document.querySelectorAll('svg polyline, svg path.leaflet-interactive').forEach(function(l) {
                            if ((l.getAttribute('class')||'').includes(vid)) {
                                l.style.display = '';
                                l.style.strokeWidth = '6px';
                                l.style.filter = 'drop-shadow(0 0 6px #0006)';
                            } else {
                                l.style.display = 'none';
                                l.style.strokeWidth = '';
                                l.style.filter = '';
                            }
                        });
                        bringPointsToFront();
                    }
                    e.stopPropagation();
                };
            });
        }
        // Evento global: clique fora de linha/ponto/popup remove destaque
        document.addEventListener('click', function(e) {
            var tag = (e.target.tagName || '').toLowerCase();
            var isPopup = false;
            var el = e.target;
            while (el) {
                if (el.classList && (el.classList.contains('leaflet-popup') || el.classList.contains('leaflet-popup-content-wrapper'))) {
                    isPopup = true;
                    break;
                }
                el = el.parentElement;
            }
            if (viagemDestaque && !(tag === 'polyline' || tag === 'path' || tag === 'circle' || isPopup)) {
                viagemDestaque = null;
                document.querySelectorAll('svg polyline, svg path.leaflet-interactive').forEach(function(l) {
                    l.style.display = '';
                    l.style.strokeWidth = '';
                    l.style.filter = '';
                });
                // Aplica filtro dos checkboxes
                document.querySelectorAll('.viagem-cb').forEach(function(cb) {
                    var v = cb.getAttribute('data-vid');
                    var visible = cb.checked;
                    document.querySelectorAll('svg polyline.'+v+', svg path.leaflet-interactive.'+v).forEach(function(l) {
                        l.style.display = visible ? '' : 'none';
                    });
                });
                bringPointsToFront();
            }
        });
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(function() {
                document.querySelectorAll('.leaflet-control-layers-overlays input[type=checkbox]').forEach(function(cb) {
                    cb.addEventListener('change', updateViagemCheckboxes);
                });
                updateViagemCheckboxes();
                bringPointsToFront();
            }, 800);
        });
        </script>
        '''
        m.get_root().html.add_child(folium.Element(custom_js))
    except Exception as e:
        print('Erro ao gerar painel de filtro de viagens:', e)

    # Salvar HTML temporário do mapa
    saida = Path('temp_blocos')
    saida.mkdir(exist_ok=True)
    temp_map_path = saida / '_mapa_trajetos_temp.html'
    m.save(temp_map_path)
    with open(temp_map_path, 'r', encoding='utf-8') as f:
        mapa_html = f.read()

    aviso = ''
    if os.path.exists(temp_map_path) and os.path.getsize(temp_map_path) > 5 * 1024 * 1024:
        aviso = "<div style='background:#ffe0e0;color:#a00;padding:12px 18px;border-radius:10px;margin-bottom:18px;font-weight:bold;'>⚠️ O mapa contém muitos pontos e pode ficar lento. Considere filtrar os dados para melhor performance.</div>"

    bloco_html = f"""
    <div class='dashboard-bloco-analise bloco-trajetos' id='bloco-trajetos'>
        <span class='dashboard-title-analise'>Trajetos e Eventos no Mapa</span>
        {aviso}
        <div style='width:100%;height:700px;'>
    """
    bloco_html += mapa_html
    bloco_html += "</div></div>"
    caminho = saida / filename
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(bloco_html)

# Exemplo de uso (remova no pipeline final):
if __name__ == "__main__":
    df = pd.read_csv('logs/analise_par09.csv')
    gerar_bloco_trajetos(df)
