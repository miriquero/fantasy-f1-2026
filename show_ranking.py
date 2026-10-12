import pandas as pd
import json
import os
from f1.scoring import procesar_carrera

with open('resultados.json', encoding='utf-8') as f:
    resultados = json.load(f)

todos = []
for archivo in os.listdir('respuestas'):
    if not archivo.endswith('.csv'): continue
    nombre_carrera = archivo.replace('respuestas_', '').replace('.csv', '').title()
    # Find matching real race key
    found_key = None
    for k in resultados:
        if nombre_carrera.lower() in k.lower():
            found_key = k; break
    if not found_key: continue
    
    ranking, _ = procesar_carrera(nombre_carrera, os.path.join('respuestas', archivo), resultados[found_key])
    todos.append(ranking)

if todos:
    all_rankings = pd.concat(todos, ignore_index=True)
    acumulado = all_rankings.groupby('Participante')['Puntos'].sum().sort_values(ascending=False).reset_index()
    print("NUEVO RANKING ACUMULADO (TOP 10):")
    for i, row in acumulado.head(10).iterrows():
        print(f"{i+1}. {row['Participante']} - {row['Puntos']} pts")
