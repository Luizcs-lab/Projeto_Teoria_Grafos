import networkx as nx;
class Grafo:
    def __init__(self):
        self.grafo = {}

    def adicionar_vertice(self, vertice):
        if vertice not in self.grafo:
            self.grafo[vertice] = []

    def adicionar_aresta(self, vertice1, vertice2):
        if vertice1 in self.grafo and vertice2 in self.grafo:
            self.grafo[vertice1].append(vertice2)
            self.grafo[vertice2].append(vertice1)  # Para grafos não direcionados

    def mostrar_grafo(self):
        for vertice in self.grafo:
            print(f"{vertice}: {self.grafo[vertice]}")

    def dfs(self, inicio, visitado=None):
        if visitado is None:
            visitado = set()
        visitado.add(inicio)
        print(inicio, end=' ')

        for vizinho in self.grafo[inicio]:
            if vizinho not in visitado:
                self.dfs(vizinho, visitado)

# Exemplo de uso
g = Grafo()
g.adicionar_vertice('A')
g.adicionar_vertice('B')
g.adicionar_vertice('C')
g.adicionar_vertice('D')
g.adicionar_aresta('A', 'B')
g.adicionar_aresta('A', 'C')
g.adicionar_aresta('B', 'D')
g.adicionar_aresta('C', 'D')

print("Grafo:")
g.mostrar_grafo()

print("\nDFS a partir do vértice 'A':")
g.dfs('A')