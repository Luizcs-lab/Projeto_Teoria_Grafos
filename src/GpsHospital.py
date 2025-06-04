import tkinter as tk
from tkinter import ttk, messagebox
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim 
import openrouteservice as ors
import pickle
import os
import webbrowser
from PIL import Image, ImageTk
import threading

import folium
import osmnx as ox
import networkx as nx

# --- 1. CONSTANTES E CONFIGURAÇÕES INICIAIS ---
# ATENÇÃO: SUBSTITUA PELA SUA CHAVE DA OPENROUTESERVICE!
# Você pode obter uma chave gratuita em: https://openrouteservice.org/sign-up
# Para produção, considere usar variáveis de ambiente (ex: os.environ.get('ORS_API_KEY'))
ORS_API_KEY = '5b3ce3597851110001cf6248fb22514c6265851ccebb33ee2ad4675470f6925f2e309a6c1a57ef7c'
client = ors.Client(key=ORS_API_KEY)

# Inicializa o geolocator globalmente para Nominatim
geolocator = Nominatim(user_agent="meu_aplicativo_mogi_caminhos_v4_osmnx") 

# Configurações do OSMnx
ox.settings.log_console = True
ox.settings.use_cache = True # Habilita o cache de downloads do OSMnx para evitar baixar o grafo repetidamente

# --- 2. DEFINIÇÃO DE VARIÁVEIS GLOBAIS ---
# Variáveis globais para os elementos da GUI
combo_inicio = None
combo_fim = None
resultado_label = None
tempo_real_var_tk = None
progress_bar_tk = None
main_tk_root = None
btn_calcular_rota = None # Variável global para o botão

# O grafo principal de ruas do OSMnx
G = None # Será carregado na splash screen

# Cache para coordenadas de locais e node_id (para acelerar geocodificação)
CACHE_COORDENADAS = 'coordenadas_cache_v3.pkl'
locais_cache = {} # Cache global de coordenadas [lat, lon] e node_id

# Lista de hospitais em Mogi das Cruzes
# Use nomes o mais específicos possível para melhor geocodificação via Nominatim/OSMnx
HOSPITAIS_MOGI = [
    'Hospital Municipal de Mogi das Cruzes',
    'Hospital Municipal de Brás Cubas, Mogi das Cruzes',
    'Hospital Santana, Mogi das Cruzes',
    'Hospital Ipiranga Mogi das Cruzes Unidade Avançada',
    'Hospital de Clínicas Luzia de Pinho Melo, Mogi das Cruzes',
    'Santa Casa de Misericórdia de Mogi das Cruzes' 
]

# --- 3. FUNÇÕES DE SUPORTE E LÓGICA DO GRAFO ---

def carregar_cache():
    """Carrega o cache de coordenadas de um arquivo."""
    global locais_cache
    if os.path.exists(CACHE_COORDENADAS):
        try:
            with open(CACHE_COORDENADAS, 'rb') as f:
                locais_cache = pickle.load(f)
                print(f"Cache de coordenadas carregado: {len(locais_cache)} entradas.")
        except Exception as e:
            print(f"Erro ao carregar cache ({CACHE_COORDENADAS}): {e}. Retornando cache vazio.")
            locais_cache = {}
    return locais_cache

def salvar_cache():
    """Salva o cache de coordenadas em um arquivo."""
    try:
        with open(CACHE_COORDENADAS, 'wb') as f:
            pickle.dump(locais_cache, f)
        print("Cache de coordenadas salvo.")
    except Exception as e:
        print(f"Erro ao salvar cache ({CACHE_COORDENADAS}): {e}")

def obter_coordenadas_e_no(local_nome):
    """
    Obtém as coordenadas [lat, lon] e o nó mais próximo no grafo G para um dado local.
    Prioriza o cache, depois OSMnx, e por último Nominatim se OSMnx falhar.
    Retorna (coordenadas, node_id).
    """
    if G is None:
        print("Erro: Grafo G não carregado. Não é possível obter nós.")
        return None, None

    # Verifica o cache primeiro
    if local_nome in locais_cache:
        if 'coords' in locais_cache[local_nome] and 'node_id' in locais_cache[local_nome]:
            return locais_cache[local_nome]['coords'], locais_cache[local_nome]['node_id']
        else:
            # Se o cache está incompleto para este local, tenta novamente
            print(f"Cache incompleto para {local_nome}. Tentando geocoding novamente.")
            del locais_cache[local_nome] # Remove a entrada incompleta para tentar de novo

    # Tenta obter via OSMnx (mais preciso para pontos na rede de ruas)
    try:
        print(f"Tentando geocoding via OSMnx para: {local_nome}")
        # ox.geocode retorna (latitude, longitude)
        point = ox.geocode(f"{local_nome}, Mogi das Cruzes, Brasil")
        if point:
            coords = [point[0], point[1]] # lat, lon
            # ox.nearest_nodes espera (longitude, latitude)
            node_id = ox.nearest_nodes(G, coords[1], coords[0]) 
            
            locais_cache[local_nome] = {'coords': coords, 'node_id': node_id}
            salvar_cache()
            print(f"-> Coordenadas e nó para {local_nome} (OSMnx): {coords}, {node_id}")
            return coords, node_id
    except Exception as e:
        print(f"Aviso: Falha ao obter coordenadas/nó via OSMnx para {local_nome}: {e}")

    # Se OSMnx falhar ou não encontrar, tenta Nominatim (genérico)
    print(f"Tentando geocoding (Nominatim) para: {local_nome}")
    try:
        # Use o objeto geolocator global.
        resultado = geolocator.geocode(f"{local_nome}, Mogi das Cruzes, Brasil", timeout=15)
        if resultado:
            coords = [resultado.latitude, resultado.longitude] # lat, lon
            # Se obteve via Nominatim, tenta encontrar o nó mais próximo no grafo G
            node_id = ox.nearest_nodes(G, coords[1], coords[0]) # ox.nearest_nodes espera (longitude, latitude)
            
            locais_cache[local_nome] = {'coords': coords, 'node_id': node_id}
            salvar_cache()
            print(f"-> Coordenadas e nó para {local_nome} (Nominatim): {coords}, {node_id}")
            return coords, node_id
        else:
            print(f"!! Não encontrou coordenadas para {local_nome} via Nominatim.")
            return None, None
    except Exception as e:
        print(f"!! Erro no geocoding para {local_nome} (Nominatim): {e}")
        return None, None


def carregar_grafo_mogi():
    """
    Carrega ou baixa o grafo de ruas de Mogi das Cruzes usando OSMnx.
    Adiciona atributos de velocidade e tempo de viagem às arestas.
    """
    global G
    print("--- Carregando/Criando grafo de ruas de Mogi das Cruzes com OSMnx ---")
    try:
        graph_path = "mogi_das_cruzes_street_network.pkl"
        if os.path.exists(graph_path):
            with open(graph_path, 'rb') as f:
                G = pickle.load(f)
            print(f"Grafo carregado do cache local: {graph_path}")
        else:
            # Baixa a rede de ruas de Mogi das Cruzes. network_type='drive' é ideal para carros.
            place_name = "Mogi das Cruzes, São Paulo, Brazil"
            G = ox.graph_from_place(place_name, network_type="drive")

            # Adiciona o atributo 'travel_time' (tempo de viagem em segundos) a cada aresta.
            G = ox.add_edge_speeds(G)
            G = ox.add_edge_travel_times(G)

            # Salva o grafo para uso futuro (acelera inicializações subsequentes)
            with open(graph_path, 'wb') as f:
                pickle.dump(G, f)
            print(f"Grafo de Mogi das Cruzes baixado e salvo em: {graph_path}")

        print(f"Grafo carregado: {len(G.nodes)} nós, {len(G.edges)} arestas.")
        return True
    except Exception as e:
        print(f"ERRO ao carregar/criar grafo OSMnx: {e}")
        messagebox.showerror("Erro de Carregamento do Grafo",
                             f"Não foi possível carregar a rede de ruas de Mogi das Cruzes.\n"
                             f"Verifique sua conexão com a internet e tente novamente.\nDetalhes: {e}")
        return False

def encontrar_caminho_dijkstra_osmnx(origem_nome, destino_nome):
    """
    Encontra o caminho mais curto entre dois locais usando o algoritmo de Dijkstra do NetworkX/OSMnx.
    O peso padrão para o cálculo é 'travel_time' (tempo de viagem em segundos).
    Retorna uma lista de nomes dos locais, o custo total (em minutos), e a rota como uma lista de IDs de nós do OSMnx.
    """
    _, orig_node_id = obter_coordenadas_e_no(origem_nome)
    _, dest_node_id = obter_coordenadas_e_no(destino_nome)

    if orig_node_id is None:
        messagebox.showerror("Erro de Localização", f"Não foi possível encontrar o local de partida: '{origem_nome}'. Verifique o nome.")
        return None, float('inf'), None
    if dest_node_id is None:
        messagebox.showerror("Erro de Localização", f"Não foi possível encontrar o local de destino: '{destino_nome}'. Verifique o nome.")
        return None, float('inf'), None

    if orig_node_id == dest_node_id:
        messagebox.showinfo("Mesmo Local", "A origem e o destino são o mesmo local. O tempo de viagem é 0 minutos.")
        return [origem_nome, destino_nome], 0.0, [orig_node_id] # Retorna o próprio nó como rota

    weight_attribute = 'travel_time' # Usando o tempo de viagem estimado do OSMnx (em segundos)

    try:
        route_nodes = nx.shortest_path(G, orig_node_id, dest_node_id, weight=weight_attribute)
        total_cost = nx.shortest_path_length(G, orig_node_id, dest_node_id, weight=weight_attribute)

        total_cost_minutes = total_cost / 60.0 # Converte o custo de segundos para minutos

        print(f"Custo do caminho (Dijkstra - tempo): {total_cost_minutes:.1f} minutos.")
        
        return [origem_nome, destino_nome], total_cost_minutes, route_nodes

    except nx.NetworkXNoPath:
        messagebox.showinfo("Caminho Não Encontrado", f"Não há caminho entre '{origem_nome}' e '{destino_nome}' na rede de ruas. Tente outros locais ou verifique a precisão dos endereços.")
        print(f"Não há caminho entre {origem_nome} e {destino_nome}.")
        return None, float('inf'), None
    except Exception as e:
        messagebox.showerror("Erro de Cálculo", f"Ocorreu um erro ao calcular a rota: {e}")
        print(f"Erro ao calcular caminho com OSMnx: {e}")
        return None, float('inf'), None

def hospital_mais_proximo(origem_nome):
    """
    Encontra o hospital mais próximo do local de origem usando o algoritmo de Dijkstra do OSMnx/NetworkX.
    """
    _, orig_node_id = obter_coordenadas_e_no(origem_nome)

    if orig_node_id is None:
        messagebox.showerror("Erro de Localização", "Não foi possível encontrar o local de partida no mapa.")
        return None, float('inf'), None, None

    menor_dist = float('inf')
    melhor_caminho_nomes = None
    hospital_perto_nome = None
    melhor_route_nodes = None

    weight_attribute = 'travel_time' # Usando o tempo de viagem estimado do OSMnx (em segundos)

    for hospital_destino_nome in HOSPITAIS_MOGI:
        if origem_nome == hospital_destino_nome:
            continue # Não calcula rota para o mesmo hospital

        _, dest_node_id = obter_coordenadas_e_no(hospital_destino_nome)
        if dest_node_id is None:
            print(f"Aviso: Não foi possível obter nó para o hospital {hospital_destino_nome}. Pulando.")
            continue

        try:
            cost = nx.shortest_path_length(G, orig_node_id, dest_node_id, weight=weight_attribute)

            if cost < menor_dist:
                menor_dist = cost
                hospital_perto_nome = hospital_destino_nome
                # Calcula o caminho completo de nós apenas para o melhor hospital encontrado
                melhor_route_nodes = nx.shortest_path(G, orig_node_id, dest_node_id, weight=weight_attribute)

        except nx.NetworkXNoPath:
            print(f"Não há caminho entre {origem_nome} e {hospital_destino_nome}.")
            continue
        except Exception as e:
            print(f"Erro ao encontrar hospital mais próximo para {hospital_destino_nome}: {e}")

    if hospital_perto_nome:
        total_cost_minutes = menor_dist / 60.0 # Converter para minutos
        melhor_caminho_nomes = [origem_nome, hospital_perto_nome]
        return melhor_caminho_nomes, total_cost_minutes, hospital_perto_nome, melhor_route_nodes
    else:
        messagebox.showinfo("Nenhum Hospital Próximo", "Não foi possível encontrar um hospital válido e mais próximo para o destino.")
        return None, float('inf'), None, None


def criar_mapa(caminho_nomes, route_nodes_osmnx):
    """
    Cria um mapa Folium exibindo os locais de partida/destino e a rota calculada.
    Recebe a lista de nomes dos locais no caminho e a lista de nós do OSMnx para a rota.
    """
    if not caminho_nomes or not route_nodes_osmnx:
        messagebox.showwarning("Mapa Vazio", "Não há caminho para exibir no mapa.")
        return

    # Pega as coordenadas do primeiro ponto para centralizar o mapa
    coords_primeiro_ponto, _ = obter_coordenadas_e_no(caminho_nomes[0])
    # Centraliza em Mogi das Cruzes se o primeiro ponto não for encontrado
    map_location = coords_primeiro_ponto if coords_primeiro_ponto else [-23.5237, -46.1884] 

    mapa = folium.Map(location=map_location, zoom_start=13)
    marker_cluster = MarkerCluster().add_to(mapa)

    # Adiciona marcadores para os locais envolvidos (origem e destino)
    for local_nome in caminho_nomes:
        coords_geo, _ = obter_coordenadas_e_no(local_nome)
        if coords_geo:
            # Ícone diferente para origem e destino
            if local_nome == caminho_nomes[0]:
                icon = folium.Icon(color='green', icon='play') # Ícone para origem
            else:
                icon = folium.Icon(color='red', icon='stop') # Ícone para destino
            folium.Marker(coords_geo, popup=local_nome, icon=icon).add_to(marker_cluster)

    # Desenha a rota no mapa usando os nós do OSMnx
    route_coords = []
    for node_id in route_nodes_osmnx:
        node_data = G.nodes[node_id]
        # Folium PolyLine espera coordenadas no formato (latitude, longitude)
        route_coords.append((node_data['y'], node_data['x'])) 

    folium.PolyLine(route_coords, color='red', weight=5, opacity=0.7).add_to(mapa)

    mapa_path = os.path.join(os.getcwd(), "mapa_transplante_rota.html")
    mapa.save(mapa_path)
    try:
        webbrowser.open(f"file://{mapa_path}", new=2)
    except Exception as e:
        print(f"Erro ao abrir mapa no navegador: {e}. O arquivo foi salvo em {mapa_path}")
        messagebox.showerror("Erro ao Abrir Mapa", f"Não foi possível abrir o mapa no navegador. O arquivo foi salvo em:\n{mapa_path}")

# --- 4. FUNÇÕES DA INTERFACE E LÓGICA DO APLICATIVO ---

def validar_api_key():
    """Verifica se a API Key foi substituída."""
    if ORS_API_KEY == "SUA_API_KEY_AQUI" or not ORS_API_KEY:
        messagebox.showerror(
            "Erro de Configuração",
            "Atenção: A chave da API do OpenRouteService (ORS_API_KEY) não foi configurada. "
            "Por favor, substitua 'SUA_API_KEY_AQUI' no código pela sua chave real."
        )
        return False
    return True

def calcular_rota_gui_command():
    """
    Função chamada pelo botão 'Calcular Rota' da GUI.
    Executa o cálculo da rota em uma thread separada para não bloquear a GUI.
    """
    global btn_calcular_rota # Acessa o botão globalmente

    # Validações iniciais antes de iniciar a thread
    inicio_val = combo_inicio.get()
    fim_val = combo_fim.get()

    if not inicio_val or inicio_val == "Selecione um hospital (opcional)":
        resultado_label.config(text="Selecione um local de partida válido.")
        messagebox.showwarning("Entrada Inválida", "Por favor, selecione um local de partida válido.")
        return
    
    # Se o destino é opcional e não foi selecionado, ele será tratado como "hospital mais próximo"
    if fim_val == "Selecione um hospital (opcional)":
        fim_val = "" # Define como string vazia para a lógica de "hospital mais próximo"

    # Desabilita o botão para evitar cliques múltiplos
    btn_calcular_rota.config(state=tk.DISABLED)
    progress_bar_tk.start()
    resultado_label.config(text="Calculando rota, por favor aguarde...")

    # Executa a lógica de cálculo em uma thread separada
    threading.Thread(target=_calcular_rota_logic, args=(inicio_val, fim_val)).start()

def _calcular_rota_logic(inicio_val, fim_val):
    """
    Lógica de cálculo da rota, executada em uma thread separada.
    Recebe os valores de início e fim como argumentos.
    """
    global combo_inicio, combo_fim, resultado_label, tempo_real_var_tk, progress_bar_tk
    
    usar_tempo_real_bool = tempo_real_var_tk.get()

    caminho_nomes_final = None
    distancia_final_min = float('inf')
    destino_display_nome = fim_val
    route_nodes_osmnx = None

    if fim_val: # Rota entre dois hospitais específicos
        caminho_nomes_final, distancia_final_min, route_nodes_osmnx = encontrar_caminho_dijkstra_osmnx(inicio_val, fim_val)
        destino_display_nome = fim_val
    else: # Encontrar o hospital mais próximo
        caminho_nomes_final, distancia_final_min, destino_display_nome, route_nodes_osmnx = hospital_mais_proximo(inicio_val)
        
    # Atualiza a GUI após o cálculo
    main_tk_root.after(0, lambda: _update_gui_after_calculation(
        caminho_nomes_final, distancia_final_min, destino_display_nome, route_nodes_osmnx, usar_tempo_real_bool
    ))

def _update_gui_after_calculation(caminho_nomes_final, distancia_final_min, destino_display_nome, route_nodes_osmnx, usar_tempo_real_bool):
    """Atualiza a GUI com os resultados do cálculo da rota."""
    global resultado_label, progress_bar_tk, btn_calcular_rota

    if caminho_nomes_final and route_nodes_osmnx:
        texto_custo_grafo = f"Custo da rota (via grafo): {distancia_final_min:.1f} min"
        
        texto = f"Destino: {destino_display_nome}\nCaminho: {' -> '.join(caminho_nomes_final)}\n{texto_custo_grafo}"
        
        # O 'travel_time' do OSMnx já é uma estimativa de tempo.
        # Se 'Considerar Tráfego em Tempo Real (via ORS)' estiver marcado, tenta obter uma estimativa mais precisa do ORS.
        if usar_tempo_real_bool:
            # Convertendo a lista de nós do OSMnx para coordenadas [lon, lat] para o ORS
            # ATENÇÃO: Chamar ORS para a rota completa pode ser MUITO lento e consumir muitos créditos
            # Dependendo do tamanho da rota e número de nós. Considere limitar o número de waypoints.
            coords_para_ors = []
            # Para evitar muitos pontos no ORS, pegue apenas o início, fim e alguns pontos intermediários.
            # Exemplo: a cada 100 nós, pegue um ponto.
            step = max(1, len(route_nodes_osmnx) // 100) # Garante pelo menos 1
            selected_nodes = route_nodes_osmnx[::step]
            if route_nodes_osmnx and route_nodes_osmnx[-1] not in selected_nodes:
                selected_nodes.append(route_nodes_osmnx[-1]) # Garante que o último nó esteja incluído

            for node_id in selected_nodes:
                node_data = G.nodes[node_id]
                coords_para_ors.append([node_data['x'], node_data['y']]) # ORS: [lon, lat]
            
            if len(coords_para_ors) >= 2:
                try:
                    if not validar_api_key(): # Verifica a API Key antes da chamada ORS
                        texto += "\nErro: Chave da API ORS inválida para tempo real."
                    else:
                        rota_ors = client.directions(coordinates=coords_para_ors, profile='driving-car')
                        total_segundos_ors = rota_ors['routes'][0]['summary']['duration']
                        tempo_ors_rota_completa_minutos = round(total_segundos_ors / 60, 1)
                        # MENSAGEM ATUALIZADA: Agora indica "com tráfego"
                        texto += f"\nTempo ORS (com tráfego): {tempo_ors_rota_completa_minutos:.1f} min"
                        texto += "\n(A precisão do tráfego depende da sua chave ORS e da disponibilidade de dados.)"
                except Exception as e:
                    print(f"Erro ao obter tempo ORS para rota completa: {e}")
                    texto += "\nErro ao obter tempo ORS para rota completa (verifique sua chave e conexão)."
            else:
                texto += "\nNão há pontos suficientes para calcular tempo ORS completo."

        resultado_label.config(text=texto)
        criar_mapa(caminho_nomes_final, route_nodes_osmnx)
    else:
        resultado_label.config(text="Caminho não encontrado ou erro no cálculo.")
        # As funções de cálculo já devem ter exibido messageboxes em caso de falha.

    progress_bar_tk.stop()
    btn_calcular_rota.config(state=tk.NORMAL) # Reabilita o botão

def mostrar_janela_principal_gui_impl(master_root_param):
    """Cria e exibe a janela principal da aplicação."""
    global combo_inicio, combo_fim, resultado_label, tempo_real_var_tk, progress_bar_tk, btn_calcular_rota
    
    master_root_param.deiconify() # Torna a janela principal visível
    master_root_param.title("Roteador para Transplantes - Mogi das Cruzes")
    try:
        master_root_param.geometry("520x450") # Ajustado para caber mais
    except tk.TclError:
        pass # Ignora erro se a janela já estiver sendo gerenciada

    frame = ttk.Frame(master_root_param, padding="10 10 10 10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    master_root_param.columnconfigure(0, weight=1)
    master_root_param.rowconfigure(0, weight=1)
    
    if not HOSPITAIS_MOGI:
        ttk.Label(frame, text="Erro: Lista de hospitais não carregada.").grid(row=0, column=0, columnspan=2)
        return

    # Widgets da interface
    ttk.Label(frame, text="Local de partida:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
    combo_inicio = ttk.Combobox(frame, values=HOSPITAIS_MOGI, width=45, state="readonly")
    combo_inicio.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    if HOSPITAIS_MOGI:
        combo_inicio.set(HOSPITAIS_MOGI[0]) # Define o primeiro hospital como padrão

    ttk.Label(frame, text="Destino (opcional):").grid(row=1, column=0, sticky='e', padx=5, pady=5)
    combo_fim = ttk.Combobox(frame, values=HOSPITAIS_MOGI, width=45, state="readonly")
    combo_fim.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
    combo_fim.set("Selecione um hospital (opcional)") # Texto padrão para destino opcional
    
    tempo_real_var_tk = tk.BooleanVar(master=master_root_param)
    # Checkbutton agora indica "Considerar Tráfego em Tempo Real"
    ttk.Checkbutton(frame, text="Considerar Tráfego em Tempo Real (via ORS)", variable=tempo_real_var_tk).grid(row=2, column=0, columnspan=2, sticky='w', padx=5, pady=2)

    # Estilo do botão
    style = ttk.Style()
    style.configure("TButton", font=("Arial", 11, "bold"), padding=8)
    style.map("TButton", background=[('active', '#e0e0e0')])

    btn_calcular_rota = ttk.Button(frame, text="Calcular Rota", command=calcular_rota_gui_command)
    btn_calcular_rota.grid(row=3, column=0, columnspan=2, pady=10)
    
    resultado_label = ttk.Label(frame, text="Selecione a origem e (opcionalmente) o destino.", wraplength=480)
    resultado_label.grid(row=4, column=0, columnspan=2, pady=5, sticky='ew')

    progress_frame = ttk.Frame(frame)
    progress_frame.grid(row=5, column=0, columnspan=2, pady=5)
    progress_bar_tk = ttk.Progressbar(progress_frame, mode='indeterminate', length=300)
    progress_bar_tk.pack()

    # Adicionar um aviso sobre a chave da API ORS
    ttk.Label(frame, text="Lembre-se de substituir a ORS_API_KEY no código!", foreground="red").grid(row=6, column=0, columnspan=2, pady=5)

def mostrar_splash_gui_impl(main_app_root_param):
    """Exibe uma tela de splash enquanto o grafo é carregado."""
    global G # Necessário para modificar o grafo globalmente
    splash_window = tk.Toplevel(main_app_root_param)
    splash_window.overrideredirect(True) # Remove bordas e barra de título
    
    window_width = 400
    window_height = 300
    screen_width = splash_window.winfo_screenwidth()
    screen_height = splash_window.winfo_screenheight()
    center_x = int(screen_width/2 - window_width / 2)
    center_y = int(screen_height/2 - window_height / 2)
    splash_window.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    splash_window.configure(bg='white')
    
    # Caminho do logo agora é 'imagens/logo.png'
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imagens", "logo.png")
    
    logo_tk_img = None # Para evitar que a imagem seja coletada pelo garbage collector
    if os.path.exists(logo_path):
        try:
            img_pil = Image.open(logo_path)
            # Compatibilidade com versões antigas do Pillow
            try:
                img_pil = img_pil.resize((150, 150), Image.Resampling.LANCZOS)
            except AttributeError:
                img_pil = img_pil.resize((150, 150), Image.LANCZOS)
            logo_tk_img = ImageTk.PhotoImage(img_pil)
            label_logo = tk.Label(splash_window, image=logo_tk_img, bg='white')
            label_logo.image = logo_tk_img # Mantém uma referência
            label_logo.pack(pady=(40,10))
        except Exception as e:
            print(f"Erro ao carregar imagem do logo: {e}")
            tk.Label(splash_window, text="Carregando App...", bg='white', font=("Arial", 16)).pack(pady=(40,10))
    else:
        print(f"Logo não encontrado em: {logo_path}. Crie uma pasta 'imagens' com 'logo.png' ou ajuste o caminho.")
        tk.Label(splash_window, text="Carregando App...", bg='white', font=("Arial", 16)).pack(pady=(40,10))

    tk.Label(splash_window, text="GPS de Transplante Hospitalar", bg='white', font=("Arial", 12, "bold")).pack(pady=5)

    barra_splash = ttk.Progressbar(splash_window, mode='indeterminate', length=300)
    barra_splash.pack(fill='x', padx=30, pady=20)
    barra_splash.start(20)

    # Ação após o splash: carregar o grafo e depois mostrar a janela principal
    def after_splash_action():
        barra_splash.stop()
        splash_window.destroy()
        
        # Carrega o grafo de ruas de Mogi das Cruzes
        if carregar_grafo_mogi():
            # Se o grafo foi carregado com sucesso, mostra a GUI principal
            if not HOSPITAIS_MOGI: # Verifique se a lista de hospitais não está vazia
                messagebox.showerror("Erro Fatal", "A lista de hospitais está vazia. Não é possível iniciar a aplicação.")
                main_app_root_param.destroy()
                exit()
            mostrar_janela_principal_gui_impl(main_app_root_param)
        else:
            # Se o grafo não puder ser carregado, exibe erro e encerra a aplicação
            messagebox.showerror("Erro de Rede", "Não foi possível carregar a rede de ruas de Mogi das Cruzes. Verifique sua conexão com a internet e a chave da API ORS. A aplicação será encerrada.")
            main_app_root_param.destroy()
            exit()

    # Chama a função after_splash_action após um atraso (simula carregamento)
    splash_window.after(4000, after_splash_action)


# --- 5. EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    main_tk_root = tk.Tk()
    main_tk_root.withdraw() # Esconde a janela principal até o splash screen terminar

    carregar_cache() # Carrega o cache de coordenadas no início

    # A lógica de verificação da API Key e carregamento do grafo
    # agora está dentro de after_splash_action, que é chamada pelo splash.
    mostrar_splash_gui_impl(main_tk_root)
    main_tk_root.mainloop()