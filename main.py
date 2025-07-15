import os
import sys
import json
import socket
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pynput import mouse, keyboard
from PIL import Image, ImageDraw
import pystray
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, time as dt_time

def resource_path(relative_path):
    """ Obtém o caminho absoluto para o recurso, funciona para desenvolvimento e para o PyInstaller. """
    try:
        # O PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Se não estiver empacotado, usa o caminho do arquivo principal
        base_path = os.path.abspath(os.path.dirname(__file__))

    return os.path.join(base_path, relative_path)



# ==============================================================================
# --- CLASSE DE CONFIGURAÇÃO ---
# ==============================================================================
class ConfigManager:
    """Gerencia o carregamento e salvamento das configurações em um arquivo JSON."""
    def __init__(self, filename="config.json"):
        self.filename = filename
        # Garante que o arquivo de configuração exista com todos os campos necessários.
        self.config = self.load_or_create_config()

    def get_default_config(self):
        """Retorna a configuração padrão, incluindo os campos ocultos do usuário."""
        return {
            "tempo_limite_minutos": 20,
            "email_remetente": "seu-email-remetente",
            "senha_remetente": "sua-senha-de-app",
            "email_destinatario": ["destinatario_01@gmail.com", "destinatario_02@gmail.com"],
            "servidor_smtp": "smtp.gmail.com",
            "porta_smtp": 587,
            "almoco_inicio": "13:00",
            "almoco_fim": "14:00",
            "almoco_ativado": True
        }

    def load_or_create_config(self):
        """Carrega a configuração do arquivo JSON. Se não existir ou estiver incompleto, cria/atualiza com os padrões."""
        default_config = self.get_default_config()
        try:
            with open(self.filename, 'r') as f:
                config = json.load(f)
            # Garante que todas as chaves padrão existam no arquivo carregado
            missing_keys = False
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
                    missing_keys = True
            if missing_keys:
                self.save_config(config)
            return config
        except (FileNotFoundError, json.JSONDecodeError):
            self.save_config(default_config)
            return default_config

    def save_config(self, config_data):
        """Salva os dados de configuração no arquivo JSON."""
        with open(self.filename, 'w') as f:
            json.dump(config_data, f, indent=4)
        self.config = config_data

# ==============================================================================
# --- JANELA DE CONFIGURAÇÕES (TKINTER) - SIMPLIFICADA ---
# ==============================================================================
class SettingsWindow:
    """Cria a janela de configurações mostrando apenas as opções de almoço."""
    def __init__(self, config_manager, on_close_callback):
        self.config_manager = config_manager
        self.on_close_callback = on_close_callback
        self.window = None

    def open_window(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Tk()
        self.window.title("Configurações do Monitor")
        self.window.resizable(False, False) # Impede redimensionamento
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        config = self.config_manager.config
        
        # --- Frame de Horários (Apenas Almoço) ---
        time_frame = ttk.LabelFrame(self.window, text="Configuração da Pausa", padding=10)
        time_frame.pack(padx=10, pady=10, fill="x")

        self.almoco_ativado_var = tk.BooleanVar(value=config.get("almoco_ativado"))
        ttk.Checkbutton(time_frame, text="Pausar monitoramento no almoço", variable=self.almoco_ativado_var).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        ttk.Label(time_frame, text="Início da Pausa:").grid(row=1, column=0, sticky="w", pady=2, padx=5)
        self.almoco_inicio_var = tk.StringVar(value=config.get("almoco_inicio"))
        ttk.Entry(time_frame, textvariable=self.almoco_inicio_var, width=10).grid(row=1, column=1, sticky="w")

        ttk.Label(time_frame, text="Fim da Pausa:").grid(row=2, column=0, sticky="w", pady=2, padx=5)
        self.almoco_fim_var = tk.StringVar(value=config.get("almoco_fim"))
        ttk.Entry(time_frame, textvariable=self.almoco_fim_var, width=10).grid(row=2, column=1, sticky="w")

        # --- Botões ---
        button_frame = ttk.Frame(self.window, padding=(10, 0, 10, 10))
        button_frame.pack(fill="x")
        ttk.Button(button_frame, text="Salvar", command=self.save_and_close).pack(side="right")
        
        self.window.mainloop()

    def save_and_close(self):
        # Validação para garantir que o intervalo de almoço não exceda 2 horas.
        inicio_str = self.almoco_inicio_var.get()
        fim_str = self.almoco_fim_var.get()

        try:
            # Converte as strings de tempo em objetos datetime para cálculo
            formato_hora = '%H:%M'
            inicio_dt = datetime.strptime(inicio_str, formato_hora)
            fim_dt = datetime.strptime(fim_str, formato_hora)

            # Calcula a duração do intervalo
            duracao = fim_dt - inicio_dt

            # Se a duração for negativa (ex: fim 01:00, início 23:00), ajusta para o dia seguinte
            if duracao.total_seconds() < 0:
                duracao += timedelta(days=1)

            # Verifica se a duração excede 2 horas (7200 segundos)
            if duracao.total_seconds() > 7200:
                messagebox.showerror("Erro de Validação", "O intervalo de pausa não pode exceder 2 horas.")
                return # Interrompe o processo de salvamento

        except ValueError:
            # Lida com casos em que o formato da hora está incorreto
            messagebox.showerror("Erro de Formato", "O formato da hora deve ser HH:MM (ex: 12:30).")
            return # Interrompe o processo de salvamento

        # Se a validação passar, continua com o processo de salvamento
        current_config = self.config_manager.config.copy()
        current_config["almoco_inicio"] = inicio_str
        current_config["almoco_fim"] = fim_str
        current_config["almoco_ativado"] = self.almoco_ativado_var.get()
        
        self.config_manager.save_config(current_config)
        
        messagebox.showinfo("Salvo", "Configurações de pausa salvas com sucesso!")
        self.on_close()

    def on_close(self):
        if self.window:
            self.window.destroy()
            self.window = None
        self.on_close_callback()

# ==============================================================================
# --- CLASSE PRINCIPAL DO MONITOR (Sem alterações lógicas) ---
# ==============================================================================
class InactivityMonitor:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.timer = None
        self.alerta_enviado = False
        self.settings_window_open = False
        self.settings_window = SettingsWindow(config_manager, self.on_settings_closed)
        self.icon = self.setup_tray_icon()

    def is_lunch_time(self):
        """Verifica se a hora atual está dentro do intervalo de almoço configurado."""
        config = self.config_manager.config
        if not config.get("almoco_ativado"):
            return False
        
        try:
            now = datetime.now().time()
            start_time = dt_time.fromisoformat(config.get("almoco_inicio", "12:00"))
            end_time = dt_time.fromisoformat(config.get("almoco_fim", "13:00"))
            return start_time <= now <= end_time
        except (ValueError, TypeError):
            return False

    def on_activity(self, *args):
        """Chamado em qualquer atividade. Reseta o timer se não for hora do almoço."""
        if self.is_lunch_time():
            return
        self.reset_timer()

    def reset_timer(self):
        """Cancela o timer existente e inicia um novo."""
        if self.alerta_enviado:
            print("Atividade detectada. Resetando status do alerta.")
            self.alerta_enviado = False

        if self.timer:
            self.timer.cancel()
        
        tempo_limite_seg = self.config_manager.config.get("tempo_limite_minutos", 15) * 60
        self.timer = threading.Timer(tempo_limite_seg, self.trigger_alert)
        self.timer.start()

    def trigger_alert(self):
        """Verifica se deve enviar o alerta e o envia."""
        if self.is_lunch_time():
            print("Hora do almoço. Alerta pausado. Verificando novamente mais tarde.")
            self.reset_timer()
            return

        if self.alerta_enviado:
            return

        self.send_email_alert()

    def send_email_alert(self):
        """Prepara e envia o e-mail de alerta para múltiplos destinatários."""
        config = self.config_manager.config
        try:
            usuario = os.getlogin()
        except OSError:
            usuario = "N/A"
        maquina = socket.gethostname()

        print(f"ALERTA: Usuário '{usuario}' inativo. Preparando e-mail...")

        destinatarios = config.get("email_destinatario", [])
        if isinstance(destinatarios, str):
            destinatarios = [destinatarios]

        if not destinatarios:
            print("ERRO: Nenhum destinatário configurado no arquivo config.json.")
            return

        msg = MIMEMultipart()
        msg['From'] = config["email_remetente"]
        msg['To'] = ", ".join(destinatarios)
        msg['Subject'] = f"Alerta de Inatividade: {usuario} em {maquina}"
        
        corpo = f"""
        Atenção,
        Este é um alerta automático.

        - Usuário: {usuario}
        - Máquina: {maquina}
        - Tempo de Inatividade: Superior a {config['tempo_limite_minutos']} minutos.
        - Horário do Alerta: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        """
        msg.attach(MIMEText(corpo, 'plain'))

        try:
            server = smtplib.SMTP(config["servidor_smtp"], config["porta_smtp"])
            server.starttls()
            server.login(config["email_remetente"], config["senha_remetente"])
            server.sendmail(config["email_remetente"], destinatarios, msg.as_string())
            server.quit()
            print(f"E-mail de alerta enviado com sucesso para: {', '.join(destinatarios)}")
            self.alerta_enviado = True
        except Exception as e:
            print(f"ERRO: Falha ao enviar e-mail. Causa: {e}")

    def run(self):
        """Inicia os listeners e o ícone da bandeja."""
        self.reset_timer()
        
        self.mouse_listener = mouse.Listener(on_move=self.on_activity, on_click=self.on_activity, on_scroll=self.on_activity)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_activity)
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
        print("Monitor de atividade iniciado em segundo plano.")
        self.icon.run()

    def create_icon_image(self):
        """Cria uma imagem simples para o ícone da bandeja."""
        width = 64
        height = 64
        color1 = (50, 100, 200) 
        color2 = (255, 255, 255)
        image = Image.new('RGB', (width, height), color1)
        dc = ImageDraw.Draw(image)
        dc.line([(15,20), (49,20), (15,44), (49,44)], fill=color2, width=8)
        return image

    def open_settings_window(self):
        if not self.settings_window_open:
            self.settings_window_open = True
            threading.Thread(target=self.settings_window.open_window, daemon=True).start()

    def on_settings_closed(self):
        self.settings_window_open = False
        self.config_manager.load_or_create_config()
        print("Janela de configurações fechada. Configurações recarregadas.")

    def exit_app(self, icon, item):
        print("Encerrando aplicação...")
        if self.timer:
            self.timer.cancel()
        self.mouse_listener.stop()
        self.keyboard_listener.stop()
        icon.stop()
        sys.exit(0)

    def setup_tray_icon(self):
        """Configura e retorna o objeto do ícone da bandeja."""
        try:
            icon_path = resource_path("logo_32p.png")
            icon_image = Image.open(icon_path)
        except FileNotFoundError:
            print("ERRO: Arquivo de ícone 'logo_32p.png' não encontrado. Usando ícone padrão.")
            icon_image = self.create_icon_image()
        menu = (
            pystray.MenuItem('Configurar Pausa', self.open_settings_window),
            pystray.MenuItem('Encerrar', self.exit_app) 
        )
        icon = pystray.Icon("monitor_inatividade", icon_image, "Monitor de Atividade", menu)
        return icon

# ==============================================================================
# --- PONTO DE ENTRADA ---
# ==============================================================================
if __name__ == "__main__":
    config_mgr = ConfigManager()
    monitor = InactivityMonitor(config_mgr)
    monitor.run()
