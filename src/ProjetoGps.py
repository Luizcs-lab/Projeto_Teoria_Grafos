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
# API do OpenRouteService (crie uma conta gratuita em https://openrouteservice.org/)
ORS_API_KEY = 'SUA_CHAVE_API_ORS_AQUI'  # Substitua aqui
client = ors.Client(key=ORS_API_KEY)
geolocator = Nominatim(user_agent="meu_aplicativo_mogi_caminhos")
CACHE_COORDENADAS = 'coordenadas_cache.pkl'

# ==================== GRAFO ====================
grafo = {
    'Centro': {'Vila Industrial': 4, 'Vila Oliveira': 3, 'Bairro do Mercado': 2, 'Hospital Municipal de Mogi': 2},
    'Vila Industrial': {'Centro': 4, 'Bairro do Mercado': 3, 'Bairro do Carmo': 5, 'Hospital Municipal de Mogi': 3},
    'Vila Oliveira': {'Centro': 3, 'Vila São João': 2, 'Hospital Santana': 4},
    'Bairro do Mercado': {'Centro': 2, 'Vila Industrial': 3, 'Hospital Municipal de Mogi': 1},
    'Bairro do Carmo': {'Vila Industrial': 5, 'Bairro das Laranjeiras': 3, 'Hospital de Clínicas Luzia de Pinho Melo': 4},
    'Vila São João': {'Vila Oliveira': 2, 'Bairro das Laranjeiras': 4, 'Hospital Santana': 3},
    'Bairro das Laranjeiras': {'Bairro do Carmo': 3, 'Vila São João': 4, 'Hospital de Clínicas Luzia de Pinho Melo': 2},
    'Hospital Municipal de Mogi': {'Centro': 2, 'Vila Industrial': 3, 'Bairro do Mercado': 1},
    'Hospital Municipal de Bras Cubas': {'Centro': 3, 'Bairro do Carmo': 5},
    'Hospital Santana': {'Vila Oliveira': 4, 'Vila São João': 3},
    'Hospital Ipiranga - Unidade Avançada': {'Centro': 3, 'Vila Industrial': 5},
    'Hospital de Clínicas Luzia de Pinho Melo': {'Bairro do Carmo': 4, 'Bairro das Laranjeiras': 2}
}

hospitais = [n for n in grafo if 'Hospital' in n]

# ==================== COORDENADAS COM CACHE ====================
def obter_coordenadas(local):
    try:
        return locais[local]
    except:
        resultado = geolocator.geocode(f"{local}, Mogi das Cruzes, Brasil")
        if resultado:
            locais[local] = [resultado.latitude, resultado.longitude]
            salvar_cache()
            return locais[local]
        return None

def salvar_cache():
    with open(CACHE_COORDENADAS, 'wb') as f:
        pickle.dump(locais, f)

def carregar_cache():
    if os.path.exists(CACHE_COORDENADAS):
        with open(CACHE_COORDENADAS, 'rb') as f:
            return pickle.load(f)
    return {}

locais = carregar_cache()
for local in grafo:
    if local not in locais:
        obter_coordenadas(local)

# ==================== ALGORITMO DE DIJKSTRA ====================
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

    # Marcadores
    for local in caminho:
        coord = obter_coordenadas(local)
        if coord:
            folium.Marker(coord, popup=local, icon=folium.Icon(color='blue')).add_to(marker_cluster)

    # Traçar rota real com ORS
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
    inicio = entry_inicio.get().strip()

    if inicio not in grafo:
        resultado_label.config(text="Local de partida inválido.")
        return

    caminho, dist, hospital = hospital_mais_proximo(inicio)
    if caminho:
        resultado_label.config(text=f"Destino automático: {hospital}\nCaminho: {' -> '.join(caminho)}\nDistância: {dist} km")
        criar_mapa(caminho)
    else:
        resultado_label.config(text="Não foi possível encontrar um caminho.")

root = tk.Tk()
root.title("Roteador Inteligente para Hospitais - Mogi das Cruzes")

ttk.Label(root, text="Local de partida:").grid(row=0, column=0)
entry_inicio = ttk.Entry(root)
entry_inicio.grid(row=0, column=1)

botao = ttk.Button(root, text="Calcular Rota", command=calcular_rota)
botao.grid(row=1, column=0, columnspan=2)

resultado_label = ttk.Label(root, text="")
resultado_label.grid(row=2, column=0, columnspan=2)

root.mainloop()