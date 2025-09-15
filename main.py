# main.py

from datetime import datetime
import customtkinter
from tkinter import filedialog
from converter import Converter
import os

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Conversor de Arquivos")
        self.geometry("700x550")
        self.converter = Converter()
        self.input_file_path = ""

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.file_frame = customtkinter.CTkFrame(self)
        self.file_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        self.file_frame.grid_columnconfigure(1, weight=1)
        self.select_button = customtkinter.CTkButton(self.file_frame, text="Selecionar Arquivo de Origem", command=self.select_file)
        self.select_button.grid(row=0, column=0, padx=10, pady=10)
        self.input_file_label = customtkinter.CTkLabel(self.file_frame, text="Nenhum arquivo selecionado", anchor="w")
        self.input_file_label.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.options_frame = customtkinter.CTkFrame(self)
        self.options_frame.grid(row=1, column=0, padx=20, pady=0, sticky="ew")
        self.options_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.from_label = customtkinter.CTkLabel(self.options_frame, text="Converter De:")
        self.from_label.grid(row=0, column=0, padx=10, pady=10)
        self.from_optionmenu = customtkinter.CTkOptionMenu(self.options_frame, values=["OFX", "CSV", "PDF", "JPG", "XML"])
        self.from_optionmenu.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.from_optionmenu.set("OFX")
        self.to_label = customtkinter.CTkLabel(self.options_frame, text="Para:")
        self.to_label.grid(row=0, column=2, padx=10, pady=10)
        self.to_optionmenu = customtkinter.CTkOptionMenu(self.options_frame, values=["CSV", "PDF", "XML", "OFX", "JPG"])
        self.to_optionmenu.grid(row=0, column=3, padx=10, pady=10, sticky="ew")
        self.to_optionmenu.set("CSV")

        self.log_textbox = customtkinter.CTkTextbox(self, state="disabled")
        self.log_textbox.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        
        self.convert_button = customtkinter.CTkButton(self, text="Converter e Salvar", command=self.run_conversion, height=40)
        self.convert_button.grid(row=3, column=0, padx=20, pady=(10, 20), sticky="ew")

        self.log("Bem-vindo! Selecione um arquivo para começar.")
        
    def select_file(self):
        """MELHORIA: Filtra os tipos de arquivo na janela de seleção."""
        from_format = self.from_optionmenu.get().lower()
        
        filetypes = {
            'ofx': [("Extrato OFX", "*.ofx")],
            'csv': [("Arquivo CSV", "*.csv")],
            'pdf': [("Arquivo PDF", "*.pdf")],
            'jpg': [("Imagem JPG", "*.jpg;*.jpeg")],
            'xml': [("Arquivo XML", "*.xml")],
        }
        
        current_filetypes = filetypes.get(from_format, [])
        current_filetypes.append(("Todos os arquivos", "*.*"))

        self.input_file_path = filedialog.askopenfilename(filetypes=current_filetypes)
        
        if self.input_file_path:
            self.input_file_label.configure(text=os.path.basename(self.input_file_path))
            self.log(f"Arquivo selecionado: {self.input_file_path}")
        else:
            self.input_file_label.configure(text="Nenhum arquivo selecionado")

    def run_conversion(self):
        if not self.input_file_path:
            self.log("Erro: Por favor, selecione um arquivo de origem primeiro.")
            return

        from_format = self.from_optionmenu.get().lower()
        to_format = self.to_optionmenu.get().lower()

        self.log(f"Processando conversão de {from_format.upper()} para {to_format.upper()}...")
        self.update()

        try:
            conversion_function_name = f"{from_format}_to_{to_format}"
            if not hasattr(self.converter, conversion_function_name):
                raise NotImplementedError(f"A conversão de {from_format.upper()} para {to_format.upper()} não é suportada.")
            
            conversion_function = getattr(self.converter, conversion_function_name)
            converted_data = conversion_function(self.input_file_path)
            self.save_converted_file(converted_data, to_format)

        except (Exception, NotImplementedError) as e:
            self.log(f"Erro na conversão: {e}")

    def save_converted_file(self, data, to_format):
        output_path = filedialog.asksaveasfilename(defaultextension=f".{to_format}", filetypes=[(f"{to_format.upper()} files", f"*.{to_format}"), ("All files", "*.*")])
        if not output_path:
            self.log("Salvamento cancelado pelo usuário."); return

        try:
            if isinstance(data, list):
                base_dir, base_name = os.path.dirname(output_path), os.path.splitext(os.path.basename(output_path))[0]
                for i, img_bytes in enumerate(data):
                    page_path = os.path.join(base_dir, f"{base_name}_pagina_{i+1}.jpg")
                    with open(page_path, 'wb') as f: f.write(img_bytes)
                self.log(f"Sucesso! {len(data)} páginas salvas na pasta: {base_dir}")
            elif isinstance(data, str):
                with open(output_path, 'w', encoding='utf-8') as f: f.write(data)
                self.log(f"Sucesso! Arquivo salvo em: {output_path}")
            elif isinstance(data, bytes):
                with open(output_path, 'wb') as f: f.write(data)
                self.log(f"Sucesso! Arquivo salvo em: {output_path}")
        except Exception as e:
            self.log(f"Erro ao salvar o arquivo: {e}")

    def log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

if __name__ == "__main__":
    app = App()
    app.mainloop()