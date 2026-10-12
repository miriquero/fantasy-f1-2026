import json
import os
import pandas as pd
from f1.normalizacion import normalizar_nombre_carrera

with open('resultados.json', encoding='utf-8') as f:
    resultados = json.load(f)

matches = []

for archivo in os.listdir('respuestas'):
    if not archivo.endswith('.csv'): continue
    race_key_raw = archivo.replace('respuestas_', '').replace('.csv', '')
    
    # Encontrar la clave correcta en resultados.json
    found_race = None
    for key in resultados:
        if normalizar_nombre_carrera(key) == normalizar_nombre_carrera(race_key_raw):
            found_race = key
            break
            
    if not found_race: continue

    res_carrera = resultados[found_race].get('resultado_carrera', [])
    if len(res_carrera) < 11: continue
    
    p11_real = res_carrera[10] # El de índice 10 es P11
    p11_real_norm = normalizar_nombre_carrera(p11_real)
    
    df = pd.read_csv(os.path.join('respuestas', archivo))
    df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)
    
    # Buscar la columna de P10
    col_p10 = None
    for c in df.columns:
        if 'écimo' in c or 'ecimo' in c:
            col_p10 = c
            break
            
    col_participante = 'Dirección de correo electrónico' if 'Dirección de correo electrónico' in df.columns else df.columns[1]

    for _, row in df.iterrows():
        participante = row.get(col_participante, 'Desconocido')
        p10_pred = str(row.get(col_p10, '')).strip()
        if not p10_pred or p10_pred == 'nan': continue
        
        p10_pred_norm = normalizar_nombre_carrera(p10_pred)
        
        if p10_pred_norm == p11_real_norm or p10_pred.split()[-1].lower() == p11_real.split()[-1].lower():
            matches.append({
                'Carrera': found_race,
                'Participante': participante.split('@')[0],
                'Piloto': p11_real
            })

for m in matches:
    print(f"- {m['Participante']} apostó P10 a {m['Piloto']} en la carrera de {m['Carrera']}")
print(f"\nTOTAL VECES QUE PASO: {len(matches)}")
