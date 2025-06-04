from geopy.geocoders import Nominatim
import osmnx as ox
import pickle
import os

class LocationData:
    """Gerencia a geocodificação de locais e o cache de coordenadas."""
    def __init__(self, graph_manager_instance):
        self.geolocator = Nominatim(user_agent="meu_aplicativo_mogi_caminhos_v4_osmnx")
        self.CACHE_COORDENADAS = 'coordenadas_cache_v3.pkl'
        self.locais_cache = {}
        self.graph_manager = graph_manager_instance # Dependência do GraphManager

    def load_cache(self):
        """Carrega o cache de coordenadas de um arquivo."""
        if os.path.exists(self.CACHE_COORDENADAS):
            try:
                with open(self.CACHE_COORDENADAS, 'rb') as f:
                    self.locais_cache = pickle.load(f)
                    print(f"Cache de coordenadas carregado: {len(self.locais_cache)} entradas.")
            except Exception as e:
                print(f"Erro ao carregar cache ({self.CACHE_COORDENADAS}): {e}. Retornando cache vazio.")
                self.locais_cache = {}
        return self.locais_cache

    def save_cache(self):
        """Salva o cache de coordenadas em um arquivo."""
        try:
            with open(self.CACHE_COORDENADAS, 'wb') as f:
                pickle.dump(self.locais_cache, f)
            print("Cache de coordenadas salvo.")
        except Exception as e:
            print(f"Erro ao salvar cache ({self.CACHE_COORDENADAS}): {e}")

    def get_coords_and_node(self, local_nome):
        """
        Obtém as coordenadas [lat, lon] e o nó mais próximo no grafo G para um dado local.
        Prioriza o cache, depois OSMnx, e por último Nominatim se OSMnx falhar.
        Retorna (coordenadas, node_id).
        """
        G = self.graph_manager.get_graph()
        if G is None:
            print("Erro: Grafo G não carregado. Não é possível obter nós.")
            return None, None

        if local_nome in self.locais_cache:
            if 'coords' in self.locais_cache[local_nome] and 'node_id' in self.locais_cache[local_nome]:
                return self.locais_cache[local_nome]['coords'], self.locais_cache[local_nome]['node_id']
            else:
                print(f"Cache incompleto para {local_nome}. Tentando geocoding novamente.")
                del self.locais_cache[local_nome]

        try:
            print(f"Tentando geocoding via OSMnx para: {local_nome}")
            point = ox.geocode(f"{local_nome}, Mogi das Cruzes, Brasil")
            if point:
                coords = [point[0], point[1]]
                node_id = ox.nearest_nodes(G, coords[1], coords[0])
                self.locais_cache[local_nome] = {'coords': coords, 'node_id': node_id}
                self.save_cache()
                print(f"-> Coordenadas e nó para {local_nome} (OSMnx): {coords}, {node_id}")
                return coords, node_id
        except Exception as e:
            print(f"Aviso: Falha ao obter coordenadas/nó via OSMnx para {local_nome}: {e}")

        print(f"Tentando geocoding (Nominatim) para: {local_nome}")
        try:
            resultado = self.geolocator.geocode(f"{local_nome}, Mogi das Cruzes, Brasil", timeout=15)
            if resultado:
                coords = [resultado.latitude, resultado.longitude]
                node_id = ox.nearest_nodes(G, coords[1], coords[0])
                self.locais_cache[local_nome] = {'coords': coords, 'node_id': node_id}
                self.save_cache()
                print(f"-> Coordenadas e nó para {local_nome} (Nominatim): {coords}, {node_id}")
                return coords, node_id
            else:
                print(f"!! Não encontrou coordenadas para {local_nome} via Nominatim.")
                return None, None
        except Exception as e:
            print(f"!! Erro no geocoding para {local_nome} (Nominatim): {e}")
            return None, None

    def get_all_hospitals(self):
        # A lista de hospitais pode vir de um arquivo, BD, ou ser constante no Model
        return [
            'Hospital Municipal de Mogi das Cruzes',
            'Hospital Municipal de Brás Cubas, Mogi das Cruzes',
            'Hospital Santana, Mogi das Cruzes',
            'Hospital Ipiranga Mogi das Cruzes Unidade Avançada',
            'Hospital de Clínicas Luzia de Pinho Melo, Mogi das Cruzes',
            'Santa Casa de Misericórdia de Mogi das Cruzes'
        ]