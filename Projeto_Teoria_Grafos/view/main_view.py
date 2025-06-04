import tkinter as tk
from tkinter import ttk, messagebox
import os
import webbrowser
import folium
from folium.plugins import MarkerCluster

class MainView:
    """Gerencia a exibição da janela principal da aplicação."""
    def __init__(self, master_root, calculate_route_command, hospitals_list):
        self.master_root = master_root
        self.calculate_route_command = calculate_route_command # Referência ao método do Controller
        self.hospitals_list = hospitals_list

        self.combo_inicio = None
        self.combo_fim = None
        self.resultado_label = None
        self.tempo_real_var_tk = None
        self.progress_bar_tk = None
        self.btn_calcular_rota = None

        self._setup_ui()

    def _setup_ui(self):
        """Configura os elementos da interface do usuário."""
        self.master_root.title("Roteador para Transplantes - Mogi das Cruzes")
        self.master_root.geometry("520x450")

        frame = ttk.Frame(self.master_root, padding="10 10 10 10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.master_root.columnconfigure(0, weight=1)
        self.master_root.rowconfigure(0, weight=1)
        
        if not self.hospitals_list:
            ttk.Label(frame, text="Erro: Lista de hospitais não carregada.").grid(row=0, column=0, columnspan=2)
            return

        ttk.Label(frame, text="Local de partida:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.combo_inicio = ttk.Combobox(frame, values=self.hospitals_list, width=45, state="readonly")
        self.combo_inicio.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        if self.hospitals_list:
            self.combo_inicio.set(self.hospitals_list[0])

        ttk.Label(frame, text="Destino (opcional):").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.combo_fim = ttk.Combobox(frame, values=self.hospitals_list, width=45, state="readonly")
        self.combo_fim.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.combo_fim.set("Selecione um hospital (opcional)")
        
        self.tempo_real_var_tk = tk.BooleanVar(master=self.master_root)
        ttk.Checkbutton(frame, text="Considerar Tráfego em Tempo Real (via ORS)", variable=self.tempo_real_var_tk).grid(row=2, column=0, columnspan=2, sticky='w', padx=5, pady=2)

        style = ttk.Style()
        style.configure("TButton", font=("Arial", 11, "bold"), padding=8)
        style.map("TButton", background=[('active', '#e0e0e0')])

        self.btn_calcular_rota = ttk.Button(frame, text="Calcular Rota", command=self.calculate_route_command)
        self.btn_calcular_rota.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.resultado_label = ttk.Label(frame, text="Selecione a origem e (opcionalmente) o destino.", wraplength=480)
        self.resultado_label.grid(row=4, column=0, columnspan=2, pady=5, sticky='ew')

        progress_frame = ttk.Frame(frame)
        progress_frame.grid(row=5, column=0, columnspan=2, pady=5)
        self.progress_bar_tk = ttk.Progressbar(progress_frame, mode='indeterminate', length=300)
        self.progress_bar_tk.pack()

        ttk.Label(frame, text="Lembre-se de substituir a ORS_API_KEY no código!", foreground="red").grid(row=6, column=0, columnspan=2, pady=5)

    def get_selected_origin(self):
        return self.combo_inicio.get()

    def get_selected_destination(self):
        return self.combo_fim.get()

    def get_real_time_traffic_preference(self):
        return self.tempo_real_var_tk.get()

    def update_status_label(self, text):
        self.resultado_label.config(text=text)

    def start_progress_bar(self):
        self.progress_bar_tk.start()
        self.btn_calcular_rota.config(state=tk.DISABLED)

    def stop_progress_bar(self):
        self.progress_bar_tk.stop()
        self.btn_calcular_rota.config(state=tk.NORMAL)

    def show_message(self, title, message, type='info'):
        if type == 'info':
            messagebox.showinfo(title, message)
        elif type == 'warning':
            messagebox.showwarning(title, message)
        elif type == 'error':
            messagebox.showerror(title, message)