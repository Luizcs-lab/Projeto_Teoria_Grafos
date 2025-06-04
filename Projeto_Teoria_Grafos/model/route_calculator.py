import networkx as nx
import openrouteservice as ors
from tkinter import messagebox # Preferível que o Controller lide com messageboxes

class RouteCalculator:
    """Calcula rotas usando OSMnx/NetworkX e OpenRouteService."""
    def __init__(self, graph_manager_instance, location_data_instance, ors_api_key):
        self.graph_manager = graph_manager_instance
        self.location_data = location_data_instance
        self.ors_client = ors.Client(key=ors_api_key)
        self.ORS_API_KEY = ors_api_key # Para validação

    def _validate_api_key(self):
        """Verifica se a API Key foi substituída."""
        if self.ORS_API_KEY == "5b3ce3597851110001cf6248fb22514c6265851ccebb33ee2ad4675470f6925f2e309a6c1a57ef7c" or not self.ORS_API_KEY:
            # Não use messagebox aqui, retorne o erro para o Controller
            return False
        return True

    def find_shortest_path_osmnx(self, origem_nome, destino_nome):
        """
        Encontra o caminho mais curto entre dois locais usando Dijkstra do NetworkX/OSMnx.
        Retorna (custo_minutos, route_nodes, erro_msg).
        """
        G = self.graph_manager.get_graph()
        if G is None:
            return None, None, "Grafo não carregado. Não é possível calcular a rota."

        _, orig_node_id = self.location_data.get_coords_and_node(origem_nome)
        _, dest_node_id = self.location_data.get_coords_and_node(destino_nome)

        if orig_node_id is None:
            return None, None, f"Não foi possível encontrar o local de partida: '{origem_nome}'."
        if dest_node_id is None:
            return None, None, f"Não foi possível encontrar o local de destino: '{destino_nome}'."

        if orig_node_id == dest_node_id:
            return 0.0, [orig_node_id], "A origem e o destino são o mesmo local."

        weight_attribute = 'travel_time'

        try:
            route_nodes = nx.shortest_path(G, orig_node_id, dest_node_id, weight=weight_attribute)
            total_cost = nx.shortest_path_length(G, orig_node_id, dest_node_id, weight=weight_attribute)
            total_cost_minutes = total_cost / 60.0
            print(f"Custo do caminho (Dijkstra - tempo): {total_cost_minutes:.1f} minutos.")
            return total_cost_minutes, route_nodes, None
        except nx.NetworkXNoPath:
            return None, None, f"Não há caminho entre '{origem_nome}' e '{destino_nome}' na rede de ruas."
        except Exception as e:
            return None, None, f"Ocorreu um erro ao calcular a rota: {e}"

    def find_nearest_hospital(self, origem_nome):
        """
        Encontra o hospital mais próximo do local de origem usando Dijkstra do OSMnx/NetworkX.
        Retorna (tempo_minutos, hospital_nome, route_nodes, erro_msg).
        """
        G = self.graph_manager.get_graph()
        if G is None:
            return None, None, None, "Grafo não carregado. Não é possível encontrar hospital."

        _, orig_node_id = self.location_data.get_coords_and_node(origem_nome)

        if orig_node_id is None:
            return None, None, None, "Não foi possível encontrar o local de partida no mapa."

        menor_dist = float('inf')
        hospital_perto_nome = None
        melhor_route_nodes = None
        
        hospitais = self.location_data.get_all_hospitals()
        weight_attribute = 'travel_time'

        for hospital_destino_nome in hospitais:
            if origem_nome == hospital_destino_nome:
                continue

            _, dest_node_id = self.location_data.get_coords_and_node(hospital_destino_nome)
            if dest_node_id is None:
                print(f"Aviso: Não foi possível obter nó para o hospital {hospital_destino_nome}. Pulando.")
                continue

            try:
                cost = nx.shortest_path_length(G, orig_node_id, dest_node_id, weight=weight_attribute)
                if cost < menor_dist:
                    menor_dist = cost
                    hospital_perto_nome = hospital_destino_nome
                    melhor_route_nodes = nx.shortest_path(G, orig_node_id, dest_node_id, weight=weight_attribute)
            except nx.NetworkXNoPath:
                print(f"Não há caminho entre {origem_nome} e {hospital_destino_nome}.")
                continue
            except Exception as e:
                print(f"Erro ao encontrar hospital mais próximo para {hospital_destino_nome}: {e}")

        if hospital_perto_nome:
            total_cost_minutes = menor_dist / 60.0
            return total_cost_minutes, hospital_perto_nome, melhor_route_nodes, None
        else:
            return None, None, None, "Não foi possível encontrar um hospital válido e mais próximo para o destino."

    def get_ors_realtime_traffic(self, route_nodes_osmnx):
        """
        Obtém o tempo de viagem em tempo real usando OpenRouteService para a rota.
        Retorna (tempo_minutos, erro_msg).
        """
        if not self._validate_api_key():
            return None, "Erro: Chave da API ORS inválida ou não configurada."

        G = self.graph_manager.get_graph()
        if G is None:
            return None, "Grafo não carregado. Não é possível obter tempo ORS."
            
        coords_para_ors = []
        step = max(1, len(route_nodes_osmnx) // 100)
        selected_nodes = route_nodes_osmnx[::step]
        if route_nodes_osmnx and route_nodes_osmnx[-1] not in selected_nodes:
            selected_nodes.append(route_nodes_osmnx[-1])

        for node_id in selected_nodes:
            node_data = G.nodes[node_id]
            coords_para_ors.append([node_data['x'], node_data['y']])

        if len(coords_para_ors) < 2:
            return None, "Não há pontos suficientes para calcular tempo ORS completo."

        try:
            rota_ors = self.ors_client.directions(coordinates=coords_para_ors, profile='driving-car')
            total_segundos_ors = rota_ors['routes'][0]['summary']['duration']
            tempo_ors_rota_completa_minutos = round(total_segundos_ors / 60, 1)
            return tempo_ors_rota_completa_minutos, None
        except Exception as e:
            return None, f"Erro ao obter tempo ORS para rota completa: {e}"