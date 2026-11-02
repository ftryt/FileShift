import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading

from core.models import ConversionRequest
from core.registry import available_targets, execute


class FormatFlowApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FormatFlow - Konwerter Plików")
        self.geometry("550x300")
        self.resizable(False, False)

        # Variables for storing user selections
        self.source_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.target_var = tk.StringVar()

        self._build_ui()

    def _build_ui(self):
        """Builds the main user interface layout."""
        padding = {'padx': 10, 'pady': 10}

        # --- Frame: File Selection ---
        frame_input = ttk.LabelFrame(self, text="1. Wybierz plik wejściowy")
        frame_input.pack(fill=tk.X, **padding)

        ttk.Entry(frame_input, textvariable=self.source_var, state='readonly').pack(side=tk.LEFT, fill=tk.X,
                                                                                    expand=True, padx=5, pady=5)
        ttk.Button(frame_input, text="Przeglądaj...", command=self.select_source_file).pack(side=tk.RIGHT, padx=5,
                                                                                            pady=5)

        # --- Frame: Output Directory ---
        frame_output = ttk.LabelFrame(self, text="2. Wybierz katalog docelowy")
        frame_output.pack(fill=tk.X, **padding)

        ttk.Entry(frame_output, textvariable=self.output_var, state='readonly').pack(side=tk.LEFT, fill=tk.X,
                                                                                     expand=True, padx=5, pady=5)
        ttk.Button(frame_output, text="Przeglądaj...", command=self.select_output_dir).pack(side=tk.RIGHT, padx=5,
                                                                                            pady=5)

        # --- Frame: Target Format ---
        frame_format = ttk.LabelFrame(self, text="3. Wybierz format docelowy")
        frame_format.pack(fill=tk.X, **padding)

        self.combo_target = ttk.Combobox(frame_format, textvariable=self.target_var, state='readonly')
        self.combo_target.pack(side=tk.LEFT, padx=5, pady=5)

        # Action button
        self.btn_convert = ttk.Button(self, text="Konwertuj", command=self.start_conversion, state=tk.DISABLED)
        self.btn_convert.pack(pady=10)

        # Status label
        self.status_label = ttk.Label(self, text="Gotowy.")
        self.status_label.pack(side=tk.BOTTOM, pady=5)

    def select_source_file(self):
        """Handles opening the file dialog and updating dynamic formats."""
        filepath = filedialog.askopenfilename(title="Wybierz plik do konwersji")
        if filepath:
            source_path = Path(filepath)
            self.source_var.set(str(source_path))
            print(f"Selected file: {source_path}")

            # Automatically set output directory to the source file's directory for UX
            if not self.output_var.get():
                self.output_var.set(str(source_path.parent))

            # Fetch dynamically what formats are supported for this specific file extension
            targets = available_targets(source_path)
            self.combo_target['values'] = targets

            if targets:
                self.combo_target.current(0)  # Select first available option
                self.btn_convert.config(state=tk.NORMAL)
                self.status_label.config(text=f"Znaleziono {len(targets)} obsługiwane formaty.")
            else:
                self.target_var.set("")
                self.combo_target['values'] = []
                self.btn_convert.config(state=tk.DISABLED)
                self.status_label.config(text="Brak obsługiwanych konwersji dla tego pliku.")
                messagebox.showwarning("Brak konwertera", f"Format {source_path.suffix} nie jest obsługiwany.")

    def select_output_dir(self):
        """Handles selecting the output directory."""
        dirpath = filedialog.askdirectory(title="Wybierz katalog zapisu")
        if dirpath:
            self.output_var.set(dirpath)
            print(f"Selected output dir: {dirpath}")

    def start_conversion(self):
        """Validates state, checks overwrite policy, and starts thread."""
        source_path = Path(self.source_var.get())
        output_dir = Path(self.output_var.get())
        target_ext = self.target_var.get()

        if not target_ext:
            messagebox.showerror("Błąd", "Wybierz format docelowy.")
            return

        # Check for overwrite before converting
        expected_target_file = output_dir / f"{source_path.stem}{target_ext}"
        if expected_target_file.exists():
            confirm = messagebox.askyesno(
                "Nadpisanie pliku",
                f"Plik docelowy '{expected_target_file.name}' już istnieje.\nCzy chcesz go nadpisać?"
            )
            if not confirm:
                print("Conversion aborted by user (file exists).")
                return

        request = ConversionRequest(
            source=source_path,
            target_format=target_ext,
            output_dir=output_dir
        )

        # Lock UI during processing
        self.btn_convert.config(state=tk.DISABLED)
        self.status_label.config(text="Przetwarzanie... proszę czekać.")
        print(f"Starting conversion thread: {source_path.name} -> {target_ext}")

        # Run conversion in background thread to keep GUI responsive
        thread = threading.Thread(target=self._run_conversion_thread, args=(request,), daemon=True)
        thread.start()

    def _run_conversion_thread(self, request: ConversionRequest):
        """Executes conversion and schedules UI update safely."""
        try:
            result_path = execute(request)
            # Use self.after to safely update GUI from background thread
            self.after(0, self._on_conversion_success, result_path)
        except Exception as e:
            self.after(0, self._on_conversion_error, str(e))

    def _on_conversion_success(self, result_path: Path):
        self.btn_convert.config(state=tk.NORMAL)
        self.status_label.config(text="Zakończono sukcesem.")
        print(f"Conversion successful: {result_path}")
        messagebox.showinfo("Sukces", f"Konwersja zakończona pomyślnie!\nZapisano do:\n{result_path}")

    def _on_conversion_error(self, error_message: str):
        self.btn_convert.config(state=tk.NORMAL)
        self.status_label.config(text="Błąd konwersji.")
        print(f"Conversion error: {error_message}")
        messagebox.showerror("Błąd konwersji", f"Wystąpił problem podczas przetwarzania:\n{error_message}")
