import heapq
import matplotlib.pyplot as plt
import networkx as nx

# Representação da cidade usando um grafo
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
        (custo, atual, caminho) = heapq.heappop(fila)
        if atual in visitados:
            continue

        caminho = caminho + [atual]
        visitados.add(atual)

        if atual == fim:
            return caminho, custo

        for vizinho, peso in grafo[atual].items():
            if vizinho not in visitados:
                heapq.heappush(fila, (custo + peso, vizinho, caminho))

    return None, float('inf')

# Representação gráfica do grafo
def plot_grafo(grafo):
    G = nx.Graph()

    # Adicionar vértices e arestas
    for vertice, vizinhos in grafo.items():
        for vizinho, peso in vizinhos.items():
            G.add_edge(vertice, vizinho, weight=peso)

    pos = nx.spring_layout(G)
    weights = nx.get_edge_attributes(G, 'weight')

    # Desenhar grafo
    nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=500, font_size=10)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=weights)
    plt.title("Mapa da Cidade")
    plt.show()

# Pedir entrada do usuário
inicio = input("Digite o bairro de partida (ex: A): ").upper()
fim = input("Digite o destino (ex: HOSPITAL): ").upper()

# Verificar se os pontos existem no grafo
if inicio in grafo and fim in grafo:
    caminho, distancia = dijkstra(grafo, inicio, fim)
    if caminho:
        print(f"\nCaminho mais curto de {inicio} até {fim}: {' -> '.join(caminho)}")
        print(f"Distância total: {distancia}")
    else:
        print("Não foi possível encontrar um caminho.")
else:
    print("Ponto de partida ou destino inválido.")

# Mostrar grafo
plot_grafo(grafo)