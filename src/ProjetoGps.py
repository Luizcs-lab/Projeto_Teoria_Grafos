import folium
import tkinter as tk
from tkinter import ttk
from folium.plugins import MarkerCluster
import webbrowser
from heapq import heappop, heappush
from geopy.geocoders import Nominatim

# Grafo atualizado com hospitais e distâncias aproximadas entre bairros e hospitais
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

# Inicializa o geocodificador
geolocator = Nominatim(user_agent="meu_aplicativo_mogi_caminhos")

# Obtém coordenadas automaticamente
def obter_coordenadas(local):
    resultado = geolocator.geocode(f"{local}, Mogi das Cruzes, Brasil")
    if resultado:
        return [resultado.latitude, resultado.longitude]
    return None  # Retorna None se não encontrar

# Criar dicionário com coordenadas de bairros e hospitais
locais = {local: obter_coordenadas(local) for local in grafo.keys()}

# Função de Dijkstra para encontrar o caminho mais curto
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

# Função para criar e salvar o mapa
def criar_mapa(caminho):
    # Criar mapa centrado em Mogi das Cruzes
    mapa = folium.Map(location=[-23.1893, -46.3100], zoom_start=13)
    marker_cluster = MarkerCluster().add_to(mapa)

    # Adicionar os marcadores no mapa
    for local, coord in locais.items():
        if coord:
            folium.Marker(location=coord, popup=local).add_to(marker_cluster)

    # Adicionar o caminho no mapa
    for i in range(len(caminho) - 1):
        if locais[caminho[i]] and locais[caminho[i + 1]]:
            folium.PolyLine(
                locations=[locais[caminho[i]], locais[caminho[i + 1]]],
                color='red', weight=4, opacity=0.7
            ).add_to(mapa)

    # Salvar e abrir o mapa
    mapa.save("mapa_com_caminho.html")
    webbrowser.open('mapa_com_caminho.html', new=2)

# Função para interface gráfica
def calcular_rota():
    inicio = entry_inicio.get()
    fim = entry_fim.get()

    if inicio in grafo and fim in grafo:
        caminho, distancia = dijkstra(grafo, inicio, fim)
        if caminho:
            resultado_label.config(text=f"Caminho: {' -> '.join(caminho)}\nDistância: {distancia} km")
            criar_mapa(caminho)
        else:
            resultado_label.config(text="Não foi possível encontrar um caminho.")
    else:
        resultado_label.config(text="Local de partida ou destino inválido.")

# Interface gráfica com Tkinter
root = tk.Tk()
root.title("Roteador de Caminho entre Bairros e Hospitais de Mogi das Cruzes")

# Adicionar campos de entrada
ttk.Label(root, text="Local de partida:").grid(column=0, row=0)
entry_inicio = ttk.Entry(root)
entry_inicio.grid(column=1, row=0)

ttk.Label(root, text="Local de destino:").grid(column=0, row=1)
entry_fim = ttk.Entry(root)
entry_fim.grid(column=1, row=1)

# Botão para calcular rota
calcular_button = ttk.Button(root, text="Calcular Rota", command=calcular_rota)
calcular_button.grid(column=0, row=2, columnspan=2)

# Label para exibir resultado
resultado_label = ttk.Label(root, text="")
resultado_label.grid(column=0, row=3, columnspan=2)

# Iniciar interface
root.mainloop()