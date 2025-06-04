import osmnx as ox
import pickle
import os
import networkx as nx

class GraphManager:
    """Gerencia o carregamento e criação do grafo de ruas de Mogi das Cruzes."""
    def __init__(self):
        self.G = None
        ox.settings.log_console = True
        ox.settings.use_cache = True # Habilita o cache de downloads do OSMnx

    def load_graph(self):
        """
        Carrega ou baixa o grafo de ruas de Mogi das Cruzes usando OSMnx.
        Adiciona atributos de velocidade e tempo de viagem às arestas.
        """
        print("--- Carregando/Criando grafo de ruas de Mogi das Cruzes com OSMnx ---")
        try:
            graph_path = "mogi_das_cruzes_street_network.pkl"
            if os.path.exists(graph_path):
                with open(graph_path, 'rb') as f:
                    self.G = pickle.load(f)
                print(f"Grafo carregado do cache local: {graph_path}")
            else:
                place_name = "Mogi das Cruzes, São Paulo, Brazil"
                self.G = ox.graph_from_place(place_name, network_type="drive")
                self.G = ox.add_edge_speeds(self.G)
                self.G = ox.add_edge_travel_times(self.G)
                with open(graph_path, 'wb') as f:
                    pickle.dump(self.G, f)
                print(f"Grafo de Mogi das Cruzes baixado e salvo em: {graph_path}")

            print(f"Grafo carregado: {len(self.G.nodes)} nós, {len(self.G.edges)} arestas.")
            return True
        except Exception as e:
            print(f"ERRO ao carregar/criar grafo OSMnx: {e}")
            return False

    def get_graph(self):
        return self.G