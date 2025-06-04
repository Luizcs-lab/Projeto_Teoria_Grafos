import threading
from tkinter import messagebox # Para messageboxes da inicialização e erros fatais
from model.graph_manager import GraphManager
from model.location_data import LocationData
from model.route_calculator import RouteCalculator
from view.main_view import MainView
from view.splash_view import SplashView
from view.map_viewer import MapViewer

# ATENÇÃO: SUBSTITUA PELA SUA CHAVE DA OPENROUTESERVICE!
ORS_API_KEY = '5b3ce3597851110001cf6248fb22514c6265851ccebb33ee2ad4675470f6925f2e309a6c1a57ef7c'

class AppController:
    """Controlador principal da aplicação, orquestra Model e View."""
    def __init__(self, master_root):
        self.master_root = master_root

        # 1. Instanciar Models (ordem importa devido a dependências)
        self.graph_manager = GraphManager()
        self.location_data = LocationData(self.graph_manager)
        self.route_calculator = RouteCalculator(self.graph_manager, self.location_data, ORS_API_KEY)

        # 2. Instanciar Views (MainView precisa de uma referência ao método de cálculo do Controller)
        self.splash_view = SplashView(self.master_root)
        self.main_view = MainView(self.master_root, 
                                  self.calculate_route_gui_command, # Passa o método do Controller como callback
                                  self.location_data.get_all_hospitals()) # Passa a lista de hospitais para a View
        self.map_viewer = MapViewer(self.graph_manager, self.location_data)

    def start_app(self):
        """Inicia o fluxo do aplicativo, mostrando a splash screen primeiro."""
        self.master_root.withdraw() # Esconde a janela principal
        self.splash_view.show_splash(self._after_splash_action)
        self.master_root.mainloop()

    def _after_splash_action(self):
        """Ação a ser executada após o término da tela de splash."""
        self.location_data.load_cache() # Carrega o cache de coordenadas
        
        # Carrega o grafo de ruas de Mogi das Cruzes em uma thread separada
        threading.Thread(target=self._load_graph_and_show_main_view).start()

    def _load_graph_and_show_main_view(self):
        """Carrega o grafo e então exibe a janela principal ou um erro."""
        if self.graph_manager.load_graph():
            # Verifica se a lista de hospitais não está vazia (caso a função get_all_hospitals falhe, embora improvável aqui)
            if not self.location_data.get_all_hospitals():
                self.master_root.after(0, lambda: messagebox.showerror("Erro Fatal", "A lista de hospitais está vazia. Não é possível iniciar a aplicação."))
                self.master_root.after(0, self.master_root.destroy)
                return

            self.master_root.after(0, self.main_view.master_root.deiconify) # Torna a janela principal visível
        else:
            self.master_root.after(0, lambda: messagebox.showerror("Erro de Rede", "Não foi possível carregar a rede de ruas de Mogi das Cruzes. Verifique sua conexão com a internet e a chave da API ORS. A aplicação será encerrada."))
            self.master_root.after(0, self.master_root.destroy)
            exit()

    def calculate_route_gui_command(self):
        """
        Função chamada pelo botão 'Calcular Rota' da GUI.
        Executa o cálculo da rota em uma thread separada para não bloquear a GUI.
        """
        inicio_val = self.main_view.get_selected_origin()
        fim_val = self.main_view.get_selected_destination()
        usar_tempo_real_bool = self.main_view.get_real_time_traffic_preference()

        if not inicio_val or inicio_val == "Selecione um hospital (opcional)":
            self.main_view.update_status_label("Selecione um local de partida válido.")
            self.main_view.show_message("Entrada Inválida", "Por favor, selecione um local de partida válido.", type='warning')
            return
        
        if fim_val == "Selecione um hospital (opcional)":
            fim_val = ""

        # Desabilita o botão e inicia a barra de progresso
        self.main_view.start_progress_bar()
        self.main_view.update_status_label("Calculando rota, por favor aguarde...")

        # Executa a lógica de cálculo em uma thread separada
        threading.Thread(target=self._calculate_route_logic, args=(inicio_val, fim_val, usar_tempo_real_bool)).start()

    def _calculate_route_logic(self, inicio_val, fim_val, usar_tempo_real_bool):
        """
        Lógica de cálculo da rota, executada em uma thread separada.
        """
        caminho_nomes_final = None
        distancia_final_min = float('inf')
        destino_display_nome = fim_val
        route_nodes_osmnx = None
        
        # --- Lógica de cálculo da rota (comunicação com o Model) ---
        if fim_val: # Rota entre dois hospitais específicos
            distancia_final_min, route_nodes_osmnx, error_msg = self.route_calculator.find_shortest_path_osmnx(inicio_val, fim_val)
            caminho_nomes_final = [inicio_val, fim_val] # Define o caminho de nomes
            destino_display_nome = fim_val
            if error_msg:
                self.master_root.after(0, lambda: self.main_view.show_message("Erro de Localização", error_msg, type='error'))

        else: # Encontrar o hospital mais próximo
            distancia_final_min, destino_display_nome, route_nodes_osmnx, error_msg = self.route_calculator.find_nearest_hospital(inicio_val)
            if error_msg:
                self.master_root.after(0, lambda: self.main_view.show_message("Erro de Localização", error_msg, type='error'))
            if destino_display_nome: # Se encontrou um hospital próximo
                caminho_nomes_final = [inicio_val, destino_display_nome]
            else: # Caso não encontre nenhum hospital próximo
                caminho_nomes_final = []


        # --- Atualiza a GUI após o cálculo (via master_root.after para thread-safety) ---
        self.master_root.after(0, lambda: self._update_gui_after_calculation(
            caminho_nomes_final, distancia_final_min, destino_display_nome, route_nodes_osmnx, usar_tempo_real_bool
        ))

    def _update_gui_after_calculation(self, caminho_nomes_final, distancia_final_min, destino_display_nome, route_nodes_osmnx, usar_tempo_real_bool):
        """Atualiza a GUI com os resultados do cálculo da rota."""
        if caminho_nomes_final and route_nodes_osmnx:
            texto_custo_grafo = f"Custo da rota (via grafo): {distancia_final_min:.1f} min"
            
            texto = f"Destino: {destino_display_nome}\nCaminho: {' -> '.join(caminho_nomes_final)}\n{texto_custo_grafo}"
            
            if usar_tempo_real_bool:
                # Chama o Model para obter tempo ORS
                tempo_ors, ors_error_msg = self.route_calculator.get_ors_realtime_traffic(route_nodes_osmnx)
                if tempo_ors is not None:
                    texto += f"\nTempo ORS (com tráfego): {tempo_ors:.1f} min"
                    texto += "\n(A precisão do tráfego depende da sua chave ORS e da disponibilidade de dados.)"
                elif ors_error_msg:
                    texto += f"\nErro ao obter tempo ORS: {ors_error_msg}"
                else:
                    texto += "\nNão há pontos suficientes para calcular tempo ORS completo."

            self.main_view.update_status_label(texto)
            self.map_viewer.create_and_display_map(caminho_nomes_final, route_nodes_osmnx)
        else:
            self.main_view.update_status_label("Caminho não encontrado ou erro no cálculo.")
        
        self.main_view.stop_progress_bar()