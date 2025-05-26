import folium
import tkinter as tk
from tkinter import ttk
from folium.plugins import MarkerCluster
from heapq import heappop, heappush
from geopy.geocoders import Nominatim
import openrouteservice as ors
import pickle
import os
import webbrowser

# ==================== CONFIGURAÇÕES ====================
ORS_API_KEY = 'SUA_CHAVE_API_ORS_AQUI'  # Substitua pela sua chave
client = ors.Client(key='5b3ce3597851110001cf62489a8c327265074323adbb26d3d3fb9107')
geolocator = Nominatim(user_agent="meu_aplicativo_mogi_caminhos")
CACHE_COORDENADAS = 'coordenadas_cache.pkl'

# ==================== GRAFO ====================
grafo = {
    'A': {'B': 2, 'C': 5, 'D': 3},
    'B': {'A': 2, 'E': 4, 'F': 7},
    'C': {'A': 5, 'G': 6},
    'D': {'A': 3, 'H': 1},
    'E': {'B': 4, 'I': 2, 'J': 3},
    'F': {'B': 7, 'K': 5},
    'G': {'C': 6, 'L': 4},
    'H': {'D': 1, 'M': 3},
    'I': {'E': 2, 'N': 5},
    'J': {'E': 3, 'O': 2},
    'K': {'F': 5, 'P': 4},
    'L': {'G': 4, 'Q': 6},
    'M': {'H': 3, 'R': 2},
    'N': {'I': 5, 'S': 1},
    'O': {'J': 2, 'T': 7},
    'P': {'K': 4, 'U': 3},
    'Q': {'L': 6, 'V': 4},
    'R': {'M': 2, 'W': 1},
    'S': {'N': 1, 'X': 3},
    'T': {'O': 7, 'Y': 6},
    'U': {'P': 3, 'Z': 2},
    'V': {'Q': 4, 'HOSPITAL': 5},
    'W': {'R': 1, 'HOSPITAL': 2},
    'X': {'S': 3, 'HOSPITAL': 4},
    'Y': {'T': 6, 'HOSPITAL': 3},
    'Z': {'U': 2, 'HOSPITAL': 1},
    'HOSPITAL': {}
}

def dijkstra(grafo, inicio, fim):
    fila = [(0, inicio, [])]
    visitados = set()

    while fila:
        (custo, atual, caminho) = heappop(fila)
        if atual in visitados:
            continue

        caminho = caminho + [atual]
        visitados.add(atual)

        if atual == fim:
            return caminho, custo

        for vizinho, peso in grafo[atual].items():
            if vizinho not in visitados:
                heappush(fila, (custo + peso, vizinho, caminho))

    return None, float('inf')

# ==================== HOSPITAL MAIS PRÓXIMO ====================
def hospital_mais_proximo(origem):
    menor_dist = float('inf')
    melhor_caminho = []
    hospital_mais_perto = None

    for hospital in hospitais:
        caminho, dist = dijkstra(grafo, origem, hospital)
        if dist < menor_dist:
            menor_dist = dist
            melhor_caminho = caminho
            hospital_mais_perto = hospital

    return melhor_caminho, menor_dist, hospital_mais_perto

# ==================== MAPA COM ROTA REAL ====================
def criar_mapa(caminho):
    mapa = folium.Map(location=[-23.5, -46.2], zoom_start=13)
    marker_cluster = MarkerCluster().add_to(mapa)

    for local in caminho:
        coord = obter_coordenadas(local)
        if coord:
            folium.Marker(coord, popup=local, icon=folium.Icon(color='blue')).add_to(marker_cluster)

    coords = [tuple(obter_coordenadas(local)[::-1]) for local in caminho if obter_coordenadas(local)]
    if len(coords) >= 2:
        try:
            rota = client.directions(coords, profile='driving-car', format='geojson')
            folium.GeoJson(rota, name='rota').add_to(mapa)
        except Exception as e:
            print(f"Erro ao traçar rota real: {e}")

    mapa.save("mapa_com_caminho.html")
    webbrowser.open("mapa_com_caminho.html", new=2)

# ==================== INTERFACE ====================
def calcular_rota():
    inicio = entry_inicio.get()
    fim = entry_fim.get()

    if inicio not in grafo:
        resultado_label.config(text="Local de partida inválido.")
        return

    if fim:
        if fim not in grafo:
            resultado_label.config(text="Destino inválido.")
            return
        caminho, distancia = dijkstra(grafo, inicio, fim)
        if caminho:
            resultado_label.config(
                text=f"Destino: {fim}\nCaminho: {' -> '.join(caminho)}\nDistância: {distancia} km"
            )
            criar_mapa(caminho)
        else:
            resultado_label.config(text="Não foi possível encontrar o caminho.")
    else:
        melhor_caminho, menor_distancia, hospital_mais_proximo_nome = hospital_mais_proximo(inicio)
        if melhor_caminho:
            resultado_label.config(
                text=f"Hospital mais próximo: {hospital_mais_proximo_nome}\n"
                     f"Caminho: {' -> '.join(melhor_caminho)}\n"
                     f"Distância: {menor_distancia} km"
            )
            criar_mapa(melhor_caminho)
        else:
            resultado_label.config(text="Não foi possível encontrar um hospital próximo.")

root = tk.Tk()
root.title("Roteador Inteligente para Hospitais - Mogi das Cruzes")

# Interface
frame = ttk.Frame(root, padding=10)
frame.grid(row=0, column=0)

ttkg = ttk.Label
entryg = ttk.Entry

# Entrada de origem e destino
ttkg(frame, text="Local de partida:").grid(row=0, column=0)
entry_inicio = entryg(frame)
entry_inicio.grid(row=0, column=1)

ttkg(frame, text="Destino (opcional):").grid(row=1, column=0)
entry_fim = entryg(frame)
entry_fim.grid(row=1, column=1)

# Botão
ttk.Button(frame, text="Calcular Rota", command=calcular_rota).grid(row=2, column=0, columnspan=2)

# Resultado
resultado_label = ttk.Label(frame, text="")
resultado_label.grid(row=3, column=0, columnspan=2, pady=10)

root.mainloop()