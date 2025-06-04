import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os

class SplashView:
    """Gerencia a exibição da tela de splash."""
    def __init__(self, master_root):
        self.master_root = master_root
        self.splash_window = None
        self.logo_tk_img = None

    def show_splash(self, callback_after_splash):
        """Exibe a tela de splash e agenda o callback."""
        self.splash_window = tk.Toplevel(self.master_root)
        self.splash_window.overrideredirect(True)
        
        window_width = 400
        window_height = 300
        screen_width = self.splash_window.winfo_screenwidth()
        screen_height = self.splash_window.winfo_screenheight()
        center_x = int(screen_width/2 - window_width / 2)
        center_y = int(screen_height/2 - window_height / 2)
        self.splash_window.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        self.splash_window.configure(bg='white')
        
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "logo.png")
        
        if os.path.exists(logo_path):
            try:
                img_pil = Image.open(logo_path)
                try: # Compatibilidade com versões antigas do Pillow
                    img_pil = img_pil.resize((150, 150), Image.Resampling.LANCZOS)
                except AttributeError:
                    img_pil = img_pil.resize((150, 150), Image.LANCZOS)
                self.logo_tk_img = ImageTk.PhotoImage(img_pil)
                label_logo = tk.Label(self.splash_window, image=self.logo_tk_img, bg='white')
                label_logo.image = self.logo_tk_img # Mantém uma referência
                label_logo.pack(pady=(40,10))
            except Exception as e:
                print(f"Erro ao carregar imagem do logo: {e}")
                tk.Label(self.splash_window, text="Carregando App...", bg='white', font=("Arial", 16)).pack(pady=(40,10))
        else:
            print(f"Logo não encontrado em: {logo_path}. Crie uma pasta 'assets' com 'logo.png' ou ajuste o caminho.")
            tk.Label(self.splash_window, text="Carregando App...", bg='white', font=("Arial", 16)).pack(pady=(40,10))

        tk.Label(self.splash_window, text="GPS de Transplante Hospitalar", bg='white', font=("Arial", 12, "bold")).pack(pady=5)

        barra_splash = ttk.Progressbar(self.splash_window, mode='indeterminate', length=300)
        barra_splash.pack(fill='x', padx=30, pady=20)
        barra_splash.start(20)

        # Chama o callback fornecido pelo Controller
        self.splash_window.after(4000, lambda: self._close_splash(barra_splash, callback_after_splash))

    def _close_splash(self, barra_splash, callback):
        barra_splash.stop()
        self.splash_window.destroy()
        callback() # Chama a função do Controller após fechar a splash