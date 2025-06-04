import tkinter as tk
from controller.app_controller import AppController

if __name__ == "__main__":
    root = tk.Tk()
    app = AppController(root)
    app.start_app()