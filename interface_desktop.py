#!/usr/bin/env python3
import os
import queue
import shutil
import subprocess
import sys
import threading
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from processar_completo import (
    APP_NAME,
    ProcessingCancelled,
    generate_unique_path,
    get_runtime_paths,
    has_configured_api_key,
    load_settings,
    run_pipeline,
    sanitize_filename,
    save_api_key,
)


RUNTIME_PATHS = get_runtime_paths()
UPLOAD_DIR = RUNTIME_PATHS.source_dir
OUTPUT_DIR = RUNTIME_PATHS.output_dir
ENV_FILE = RUNTIME_PATHS.env_file

SUPPORTED_EXTENSIONS = (
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".wmv",
    ".flv",
    ".webm",
    ".m4v",
    ".3gp",
    ".ogv",
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
)


def is_supported_media_file(file_path):
    return Path(file_path).suffix.lower() in SUPPORTED_EXTENSIONS

def mask_api_key(api_key):
    cleaned = (api_key or "").strip()
    if not cleaned:
        return "Nao configurada"
    if len(cleaned) <= 8:
        return "*" * len(cleaned)
    return f"{cleaned[:4]}...{cleaned[-4:]}"


def detect_unsupported_macos_python():
    if sys.platform != "darwin":
        return None

    executable = Path(sys.executable).resolve()
    executable_str = str(executable)

    if "Xcode.app" in executable_str or executable_str.startswith("/usr/bin/python3"):
        return (
            "Runtime grafico nao suportado no macOS.\n\n"
            "Este aplicativo nao deve ser executado com o Python fornecido pelo Xcode/Apple, "
            "porque o Tk pode abortar ao criar a janela.\n\n"
            "Use o Python oficial do python.org ou um Python do Homebrew com Tk compativel.\n\n"
            "Exemplo com Python oficial:\n"
            "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 interface_desktop.py"
        )

    return None


class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcricao de Videos")
        self.root.geometry("1040x760")
        self.root.minsize(920, 680)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.log_queue = queue.Queue()
        self.worker_thread = None
        self.stop_event = threading.Event()
        self.is_running = False
        self.last_run_succeeded = False
        self.last_output_file = None

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        self.status_var = tk.StringVar(
            value="Configure a chave da API e selecione um ou mais videos ou audios."
        )
        self.api_status_var = tk.StringVar()
        self.api_key_var = tk.StringVar()

        self._build_ui()
        self.load_api_key()
        self.refresh_file_list()
        self.poll_log_queue()

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(self.root, padding=16)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)

        header = ttk.Frame(main_frame)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Transcricao de audio e video",
            font=("TkDefaultFont", 16, "bold"),
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            header,
            text=(
                "Os arquivos sao copiados para a pasta local do aplicativo e a transcricao final "
                "e gerada em formato .docx."
            ),
            wraplength=920,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        config_frame = ttk.Labelframe(main_frame, text="Configuracao da API", padding=12)
        config_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        config_frame.columnconfigure(1, weight=1)

        ttk.Label(config_frame, text="GEMINI_API_KEY").grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.api_key_entry = ttk.Entry(config_frame, textvariable=self.api_key_var, show="*")
        self.api_key_entry.grid(row=0, column=1, sticky="ew")

        self.save_api_button = ttk.Button(
            config_frame,
            text="Salvar no .env",
            command=self.save_api_key_from_form,
        )
        self.save_api_button.grid(row=0, column=2, padx=(8, 0))

        ttk.Label(
            config_frame,
            textvariable=self.api_status_var,
            foreground="#1f4d78",
            wraplength=900,
            justify="left",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))

        actions = ttk.Frame(main_frame)
        actions.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        actions.columnconfigure(5, weight=1)

        self.select_button = ttk.Button(actions, text="Selecionar arquivos", command=self.select_files)
        self.select_button.grid(row=0, column=0, padx=(0, 8))

        self.refresh_button = ttk.Button(actions, text="Atualizar lista", command=self.refresh_file_list)
        self.refresh_button.grid(row=0, column=1, padx=(0, 8))

        self.open_uploads_button = ttk.Button(
            actions,
            text="Abrir pasta de entrada",
            command=lambda: self.open_directory(UPLOAD_DIR),
        )
        self.open_uploads_button.grid(row=0, column=2, padx=(0, 8))

        self.open_outputs_button = ttk.Button(
            actions,
            text="Abrir transcricoes",
            command=lambda: self.open_directory(OUTPUT_DIR),
        )
        self.open_outputs_button.grid(row=0, column=3, padx=(0, 8))

        self.open_app_dir_button = ttk.Button(
            actions,
            text="Abrir pasta do app",
            command=lambda: self.open_directory(RUNTIME_PATHS.base_dir),
        )
        self.open_app_dir_button.grid(row=0, column=4, padx=(0, 8))

        self.start_button = ttk.Button(
            actions,
            text="Gerar transcricao",
            command=self.start_transcription,
        )
        self.start_button.grid(row=0, column=6, sticky="e")

        status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            foreground="#1f4d78",
            wraplength=980,
            justify="left",
        )
        status_label.grid(row=3, column=0, sticky="ew", pady=(0, 12))

        content = ttk.Panedwindow(main_frame, orient=tk.VERTICAL)
        content.grid(row=4, column=0, sticky="nsew")

        files_frame = ttk.Labelframe(content, text="Arquivos prontos para processar", padding=12)
        files_frame.columnconfigure(0, weight=1)
        files_frame.rowconfigure(0, weight=1)

        self.files_listbox = tk.Listbox(files_frame, height=10)
        self.files_listbox.grid(row=0, column=0, sticky="nsew")

        files_scroll = ttk.Scrollbar(files_frame, orient="vertical", command=self.files_listbox.yview)
        files_scroll.grid(row=0, column=1, sticky="ns")
        self.files_listbox.configure(yscrollcommand=files_scroll.set)

        content.add(files_frame, weight=1)

        logs_frame = ttk.Labelframe(content, text="Logs do processamento", padding=12)
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)

        self.logs_text = tk.Text(logs_frame, wrap="word", state="disabled", height=20)
        self.logs_text.grid(row=0, column=0, sticky="nsew")

        logs_scroll = ttk.Scrollbar(logs_frame, orient="vertical", command=self.logs_text.yview)
        logs_scroll.grid(row=0, column=1, sticky="ns")
        self.logs_text.configure(yscrollcommand=logs_scroll.set)

        content.add(logs_frame, weight=3)

    def load_api_key(self):
        settings = load_settings(ENV_FILE)
        self.api_key_var.set(settings.api_key)
        self.update_api_status()

    def update_api_status(self):
        api_key = self.api_key_var.get().strip()
        env_location = str(ENV_FILE)
        if has_configured_api_key(api_key):
            self.api_status_var.set(
                f"Chave configurada ({mask_api_key(api_key)}). Arquivo: {env_location}"
            )
        else:
            self.api_status_var.set(
                f"Chave nao configurada. Salve a GEMINI_API_KEY no arquivo: {env_location}"
            )

    def save_api_key_from_form(self):
        api_key = self.api_key_var.get().strip()
        if not has_configured_api_key(api_key):
            messagebox.showwarning(
                "Chave obrigatoria",
                "Informe uma GEMINI_API_KEY valida antes de salvar.",
            )
            return

        save_api_key(api_key, ENV_FILE)
        self.update_api_status()
        self.log(f"GEMINI_API_KEY salva em {ENV_FILE}")
        self.status_var.set("Chave da API salva com sucesso.")

    def log(self, message):
        self.logs_text.configure(state="normal")
        self.logs_text.insert("end", f"{message}\n")
        self.logs_text.see("end")
        self.logs_text.configure(state="disabled")

    def poll_log_queue(self):
        while True:
            try:
                message = self.log_queue.get_nowait()
            except queue.Empty:
                break

            if message == "__PROCESS_FINISHED__":
                self.finish_transcription()
                continue

            self.log(message)

        self.root.after(150, self.poll_log_queue)

    def refresh_file_list(self):
        self.files_listbox.delete(0, "end")

        files = sorted(
            [
                path.name
                for path in UPLOAD_DIR.iterdir()
                if path.is_file() and is_supported_media_file(path)
            ]
        )

        for file_name in files:
            self.files_listbox.insert("end", file_name)

        if files:
            self.status_var.set(
                f"{len(files)} arquivo(s) encontrado(s) em '{UPLOAD_DIR}'. Clique em 'Gerar transcricao' para iniciar."
            )
        else:
            self.status_var.set(
                f"Nenhum arquivo disponivel em '{UPLOAD_DIR}'. Selecione arquivos para copiar."
            )

    def select_files(self):
        if self.is_running:
            return

        filetypes = [
            ("Midia suportada", " ".join(f"*{extension}" for extension in SUPPORTED_EXTENSIONS)),
            ("Todos os arquivos", "*.*"),
        ]

        selected_files = filedialog.askopenfilenames(
            title="Selecione um ou mais videos ou audios",
            filetypes=filetypes,
        )

        if not selected_files:
            return

        copied_files = []
        skipped_files = []

        for source in selected_files:
            if not is_supported_media_file(source):
                skipped_files.append(Path(source).name)
                continue

            safe_name = sanitize_filename(Path(source).name)
            destination = generate_unique_path(UPLOAD_DIR, safe_name)
            shutil.copy2(source, destination)
            copied_files.append(destination.name)

        self.refresh_file_list()

        if copied_files:
            self.log("Arquivos copiados para a pasta do aplicativo: " + ", ".join(copied_files))

        if skipped_files:
            self.log("Arquivos ignorados por formato nao suportado: " + ", ".join(skipped_files))

    def open_directory(self, directory):
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(directory))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(directory)])
            else:
                subprocess.Popen(["xdg-open", str(directory)])
        except Exception as error:
            messagebox.showerror("Erro", f"Nao foi possivel abrir a pasta:\n{error}")

    def set_running_state(self, running):
        self.is_running = running

        state = "disabled" if running else "normal"
        self.select_button.configure(state=state)
        self.refresh_button.configure(state=state)
        self.start_button.configure(state=state)
        self.save_api_button.configure(state=state)
        self.api_key_entry.configure(state=state)

        if running:
            self.status_var.set("Processamento em andamento. Acompanhe os logs abaixo.")

    def start_transcription(self):
        api_key = self.api_key_var.get().strip()
        if not has_configured_api_key(api_key):
            messagebox.showwarning(
                "Chave obrigatoria",
                "Configure uma GEMINI_API_KEY valida antes de iniciar a transcricao.",
            )
            return

        save_api_key(api_key, ENV_FILE)
        self.update_api_status()

        files = [
            path
            for path in UPLOAD_DIR.iterdir()
            if path.is_file() and is_supported_media_file(path)
        ]

        if not files:
            messagebox.showwarning(
                "Nenhum arquivo",
                "Adicione ao menos um video ou audio antes de transcrever.",
            )
            return

        self.stop_event = threading.Event()
        self.last_run_succeeded = False
        self.last_output_file = None
        self.log("")
        self.log("========== NOVA EXECUCAO ==========")
        self.log(f"Arquivos na fila: {len(files)}")
        self.set_running_state(True)

        self.worker_thread = threading.Thread(target=self.run_pipeline_worker, daemon=True)
        self.worker_thread.start()

    def run_pipeline_worker(self):
        try:
            output_path = run_pipeline(logger=self.log_queue.put, stop_event=self.stop_event)
            self.last_output_file = output_path
            self.last_run_succeeded = True
            self.log_queue.put("")
            self.log_queue.put("Processamento finalizado com sucesso.")
        except ProcessingCancelled as error:
            self.log_queue.put(f"Processamento cancelado: {error}")
        except Exception as error:
            self.log_queue.put(f"Erro durante a transcricao: {error}")
        finally:
            self.log_queue.put("__PROCESS_FINISHED__")

    def finish_transcription(self):
        self.set_running_state(False)
        self.refresh_file_list()

        if self.last_run_succeeded and self.last_output_file:
            self.status_var.set(f"Transcricao concluida. Ultimo arquivo gerado: {self.last_output_file.name}")
        else:
            self.status_var.set("Processamento encerrado. Verifique os logs para detalhes.")

    def on_close(self):
        if self.is_running:
            should_close = messagebox.askyesno(
                "Encerrar aplicacao",
                "Existe uma transcricao em andamento. Deseja encerrar e cancelar o processamento?",
            )
            if not should_close:
                return
            self.stop_event.set()

        self.root.destroy()


def main():
    runtime_error = detect_unsupported_macos_python()
    if runtime_error:
        print(runtime_error, file=sys.stderr)
        raise SystemExit(1)

    root = tk.Tk()
    root.title(APP_NAME)
    TranscriptionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
