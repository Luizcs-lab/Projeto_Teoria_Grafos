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
from PIL import Image, ImageTk
import math

ORS_API_KEY = '5b3ce3597851110001cf6248fb22514c6265851ccebb33ee2ad4675470f6925f2e309a6c1a57ef7c'
client = ors.Client(key=ORS_API_KEY)
geolocator = Nominatim(user_agent="meu_aplicativo_mogi_caminhos")
CACHE_COORDENADAS = 'coordenadas_cache.pkl'

# GRAFO
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



# Função para calcular a distância geográfica (Haversine)
def distancia_haversine(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    R = 6371.0  # Raio da Terra em km

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

# Cache com coordenadas geográficas dos pontos
coordenadas_cache = {
    "Hospital Mogi das Cruzes": (-23.5221, -46.1884),
    "UBS Vila Suíssa": (-23.5273, -46.1852),
    "Hospital Santana": (-23.5302, -46.1915),
    "UBS Jardim Universo": (-23.5182, -46.1783),
    "UBS Alto Ipiranga": (-23.5199, -46.1912),
    "Hospital Luzia de Pinho Melo": (-23.5201, -46.1995),
    "UBS Jundiapeba": (-23.5401, -46.1722),
    "UBS Braz Cubas": (-23.5228, -46.1831),
}

# Função para obter coordenadas a partir do cache
def obter_coordenadas(nome):
    return coordenadas_cache.get(nome)

# Grafo inicial com conexões lógicas
grafo_original = {
    "Hospital Mogi das Cruzes": {
        "UBS Vila Suíssa": 1, "Hospital Santana": 1, "UBS Jardim Universo": 1
    },
    "UBS Vila Suíssa": {
        "Hospital Mogi das Cruzes": 1, "Hospital Santana": 1, "UBS Alto Ipiranga": 1
    },
    "Hospital Santana": {
        "Hospital Mogi das Cruzes": 1, "UBS Vila Suíssa": 1, "Hospital Luzia de Pinho Melo": 1
    },
    "UBS Jardim Universo": {
        "Hospital Mogi das Cruzes": 1, "UBS Alto Ipiranga": 1, "UBS Jundiapeba": 1
    },
    "UBS Alto Ipiranga": {
        "UBS Vila Suíssa": 1, "UBS Jardim Universo": 1, "UBS Braz Cubas": 1
    },
    "Hospital Luzia de Pinho Melo": {
        "Hospital Santana": 1, "UBS Braz Cubas": 1
    },
    "UBS Jundiapeba": {
        "UBS Jardim Universo": 1, "UBS Braz Cubas": 1
    },
    "UBS Braz Cubas": {
        "UBS Alto Ipiranga": 1, "Hospital Luzia de Pinho Melo": 1, "UBS Jundiapeba": 1
    }
}

# Função para atualizar pesos com distâncias reais
def atualizar_pesos_grafo(grafo_original, obter_coordenadas):
    grafo_atualizado = {}
    for origem in grafo_original:
        grafo_atualizado[origem] = {}
        for destino in grafo_original[origem]:
            coord_origem = obter_coordenadas(origem)
            coord_destino = obter_coordenadas(destino)
            if coord_origem and coord_destino:
                distancia_real = distancia_haversine(coord_origem, coord_destino)
                grafo_atualizado[origem][destino] = round(distancia_real, 3)
    return grafo_atualizado

# Geração do novo grafo com pesos atualizados
grafo_com_distancias_reais = atualizar_pesos_grafo(grafo_original, obter_coordenadas)

# Exibindo resultado
for origem, vizinhos in grafo_com_distancias_reais.items():
    print(f"{origem}:")
    for destino, distancia in vizinhos.items():
        print(f"  -> {destino}: {distancia} km")

# COORDENADAS COM CACHE
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

# DIJKSTRA PADRÃO
def dijkstra(grafo, inicio, fim, modo_ambulancia=False):
    fila = [(0, inicio, [])]
    visitados = set()

    while fila:
        custo, atual, caminho = heappop(fila)
        if atual in visitados:
            continue

        caminho = caminho + [atual]
        visitados.add(atual)

        if atual == fim:
            return caminho, custo

        for vizinho, peso in grafo[atual].items():
            peso_final = peso * 0.7 if modo_ambulancia else peso
            if vizinho not in visitados:
                heappush(fila, (custo + peso_final, vizinho, caminho))

    return None, float('inf')

# TEMPO ESTIMADO ORS
def tempo_estimado_real(caminho):
    coords = [obter_coordenadas(l)[::-1] for l in caminho]
    total_segundos = 0
    for i in range(len(coords)-1):
        try:
            rota = client.directions([coords[i], coords[i+1]], profile='driving-car')
            total_segundos += rota['routes'][0]['summary']['duration']
        except:
            pass
    return total_segundos / 60  # minutos

# HOSPITAL MAIS PRÓXIMO
def hospital_mais_proximo(origem, modo_ambu=False):
    menor_dist = float('inf')
    melhor_caminho = []
    hospital_perto = None
    for hospital in hospitais:
        caminho, dist = dijkstra(grafo, origem, hospital, modo_ambu)
        if dist < menor_dist:
            menor_dist = dist
            melhor_caminho = caminho
            hospital_perto = hospital
    return melhor_caminho, menor_dist, hospital_perto

# MAPA
def criar_mapa(caminho):
    mapa = folium.Map(location=[-23.5, -46.2], zoom_start=13)
    marker_cluster = MarkerCluster().add_to(mapa)
    coords_rota = []

    for local in caminho:
        coord = obter_coordenadas(local)
        if coord:
            folium.Marker(coord, popup=local, icon=folium.Icon(color='blue')).add_to(marker_cluster)
            coords_rota.append(coord[::-1])  # ORS

    if len(coords_rota) >= 2:
        for i in range(len(coords_rota)-1):
            try:
                rota = client.directions([coords_rota[i], coords_rota[i+1]], profile='driving-car', format='geojson')
                folium.GeoJson(rota, name=f'Rota {i+1}').add_to(mapa)
            except Exception as e:
                print(f"Erro rota ORS: {e}")

    mapa.save("mapa_com_caminho.html")
    webbrowser.open("mapa_com_caminho.html", new=2)

# CALCULAR ROTA
def calcular_rota():
    inicio = combo_inicio.get()
    fim = combo_fim.get()
    modo_ambu = modo_ambulancia.get()
    usar_tempo_real = tempo_real.get()

    if not inicio or inicio not in grafo:
        resultado_label.config(text="Partida inválida.")
        return

    progress.start()

    if fim:
        if fim not in grafo:
            resultado_label.config(text="Destino inválido.")
            progress.stop()
            return
        caminho, distancia = dijkstra(grafo, inicio, fim, modo_ambu)
    else:
        caminho, distancia, fim = hospital_mais_proximo(inicio, modo_ambu)

    if caminho:
        tempo = tempo_estimado_real(caminho) if usar_tempo_real else None
        texto = f"Destino: {fim}\nCaminho: {' -> '.join(caminho)}\nDistância: {distancia:.1f} km"
        if tempo:
            texto += f"\nTempo estimado: {tempo:.1f} minutos"
        resultado_label.config(text=texto)
        criar_mapa(caminho)
    else:
        resultado_label.config(text="Caminho não encontrado.")

    progress.stop()

# INTERFACE
def mostrar_janela_principal():
    global combo_inicio, combo_fim, resultado_label, modo_ambulancia, tempo_real, progress
    root.deiconify()
    root.title("Roteador para Hospitais - Mogi")
    root.geometry("480x300")
    frame = ttk.Frame(root, padding=10)
    frame.grid(row=0, column=0)

    ttk.Label(frame, text="Local de partida:").grid(row=0, column=0, sticky='e')
    combo_inicio = ttk.Combobox(frame, values=list(grafo.keys()), width=30)
    combo_inicio.grid(row=0, column=1, padx=10, pady=5)

    ttk.Label(frame, text="Destino (opcional):").grid(row=1, column=0, sticky='e')
    combo_fim = ttk.Combobox(frame, values=list(grafo.keys()), width=30)
    combo_fim.grid(row=1, column=1, padx=10, pady=5)

    modo_ambulancia = tk.BooleanVar()
    tempo_real = tk.BooleanVar()

    ttk.Checkbutton(frame, text="Modo Ambulância", variable=modo_ambulancia).grid(row=2, column=0, columnspan=2)
    ttk.Checkbutton(frame, text="Filtrar por Tempo Real", variable=tempo_real).grid(row=3, column=0, columnspan=2)

    ttk.Button(frame, text="Calcular Rota", command=calcular_rota).grid(row=4, column=0, columnspan=2, pady=10)
    resultado_label = ttk.Label(frame, text="", wraplength=400)
    resultado_label.grid(row=5, column=0, columnspan=2, pady=5)

    progress = ttk.Progressbar(frame, mode='indeterminate')
    progress.grid(row=6, column=0, columnspan=2, pady=5)

# SPLASH SCREEN
def mostrar_splash():
    splash = tk.Toplevel()
    splash.overrideredirect(True)
    splash.geometry("400x300+500+250")
    splash.configure(bg='white')
    if os.path.exists("Projeto_Teoria_grafos/imagens/logo.png"):
        img = Image.open("Projeto_Teoria_grafos/imagens/logo.png")
        img = img.resize((200, 200))
        logo = ImageTk.PhotoImage(img)
        label_logo = tk.Label(splash, image=logo, bg='white')
        label_logo.image = logo
        label_logo.pack(pady=10)
    barra = ttk.Progressbar(splash, mode='indeterminate')
    barra.pack(fill='x', padx=30, pady=10)
    barra.start()
    root.after(5000, lambda: (splash.destroy(), mostrar_janela_principal()))

# EXECUÇÃO
root = tk.Tk()
root.withdraw()
mostrar_splash()
root.mainloop() 