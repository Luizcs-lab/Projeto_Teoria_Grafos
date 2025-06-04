import folium
from folium.plugins import MarkerCluster
import webbrowser
import os
from tkinter import messagebox # Usado para exibir erros ao abrir o mapa

class MapViewer:
    """Gerencia a criação e exibição de mapas Folium."""
    def __init__(self, graph_manager_instance, location_data_instance):
        self.graph_manager = graph_manager_instance
        self.location_data = location_data_instance

    def create_and_display_map(self, caminho_nomes, route_nodes_osmnx):
        """
        Cria um mapa Folium exibindo os locais de partida/destino e a rota calculada.
        Recebe a lista de nomes dos locais no caminho e a lista de nós do OSMnx para a rota.
        """
        if not caminho_nomes or not route_nodes_osmnx:
            messagebox.showwarning("Mapa Vazio", "Não há caminho para exibir no mapa.")
            return

        coords_primeiro_ponto, _ = self.location_data.get_coords_and_node(caminho_nomes[0])
        map_location = coords_primeiro_ponto if coords_primeiro_ponto else [-23.5237, -46.1884] # Coordenadas de Mogi das Cruzes

        mapa = folium.Map(location=map_location, zoom_start=13)
        marker_cluster = MarkerCluster().add_to(mapa)

        for local_nome in caminho_nomes:
            coords_geo, _ = self.location_data.get_coords_and_node(local_nome)
            if coords_geo:
                if local_nome == caminho_nomes[0]:
                    icon = folium.Icon(color='green', icon='play')
                else:
                    icon = folium.Icon(color='red', icon='stop')
                folium.Marker(coords_geo, popup=local_nome, icon=icon).add_to(marker_cluster)

        route_coords = []
        G = self.graph_manager.get_graph()
        if G: # Verifica se o grafo existe antes de tentar acessá-lo
            for node_id in route_nodes_osmnx:
                node_data = G.nodes[node_id]
                route_coords.append((node_data['y'], node_data['x']))

            folium.PolyLine(route_coords, color='red', weight=5, opacity=0.7).add_to(mapa)
        else:
            messagebox.showwarning("Erro no Mapa", "Não foi possível carregar o grafo para desenhar a rota.")

        mapa_path = os.path.join(os.getcwd(), "mapa_transplante_rota.html")
        mapa.save(mapa_path)
        try:
            webbrowser.open(f"file://{mapa_path}", new=2)
        except Exception as e:
            print(f"Erro ao abrir mapa no navegador: {e}. O arquivo foi salvo em {mapa_path}")
            messagebox.showerror("Erro ao Abrir Mapa", f"Não foi possível abrir o mapa no navegador. O arquivo foi salvo em:\n{mapa_path}")